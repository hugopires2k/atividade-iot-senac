from datetime import datetime, timedelta, timezone

from app.db import Device, Reading, SessionLocal, utcnow


def payload(seq=1, **over):
    body = {"device_id": "esp32-lab-01", "seq": seq,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "temperature_c": 25.4, "humidity_pct": 61.0, "light_pct": 42.0}
    body.update(over)
    return body


def count_readings():
    with SessionLocal() as db:
        return db.query(Reading).count()


# ---------- health
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["db"] == "ok"


# ---------- auth: 401 / 403
def test_no_token_is_401(client):
    assert client.get("/api/v1/devices").status_code == 401


def test_garbage_token_is_401(client):
    r = client.get("/api/v1/devices", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


def test_wrong_password_is_401(client, ana):
    r = client.post("/api/v1/auth/login", json={"email": "ana@example.com", "password": "nope-nope"})
    assert r.status_code == 401


def test_other_users_device_is_403(client, device, bruno):
    for path in ("latest", "readings", "stats"):
        r = client.get(f"/api/v1/devices/{device['id']}/{path}", headers=bruno)
        assert r.status_code == 403, path


def test_owner_can_read_own_device(client, device, ana):
    assert client.get(f"/api/v1/devices/{device['id']}/latest", headers=ana).status_code == 200


def test_devices_list_only_shows_own(client, device, bruno):
    assert client.get("/api/v1/devices", headers=bruno).json() == []


# ---------- device key
def test_ingest_without_key_is_401(client, device):
    assert client.post("/api/v1/readings", json=payload()).status_code == 401


def test_ingest_with_wrong_key_is_401(client, device):
    r = client.post("/api/v1/readings", json=payload(), headers={"X-Device-Key": "wrong"})
    assert r.status_code == 401 and count_readings() == 0


def test_key_of_one_device_cannot_write_as_another(client, device, bruno):
    client.post("/api/v1/devices", json={"device_id": "esp32-other", "name": "Other"}, headers=bruno)
    r = client.post("/api/v1/readings", json=payload(device_id="esp32-other"), headers=device["key"])
    assert r.status_code == 403 and count_readings() == 0


# ---------- ingestion + validation: 400 and nothing stored
def test_valid_reading_is_stored(client, device, ana):
    r = client.post("/api/v1/readings", json=payload(), headers=device["key"])
    assert r.status_code == 201
    latest = client.get(f"/api/v1/devices/{device['id']}/latest", headers=ana).json()
    assert latest["reading"]["temperature_c"] == 25.4
    assert latest["status"]["online"] is True and latest["stale"] is False


def test_out_of_range_is_400_and_not_stored(client, device):
    r = client.post("/api/v1/readings", json=payload(temperature_c=999), headers=device["key"])
    assert r.status_code == 400 and count_readings() == 0


def test_malformed_body_is_400_and_not_stored(client, device):
    r = client.post("/api/v1/readings", json={"device_id": "esp32-lab-01", "seq": "abc"}, headers=device["key"])
    assert r.status_code == 400 and count_readings() == 0


def test_future_timestamp_is_400(client, device):
    future = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post("/api/v1/readings", json=payload(ts=future), headers=device["key"])
    assert r.status_code == 400 and count_readings() == 0


# ---------- R5: a failed sensor is stored as invalid, never as a value
def test_null_sensor_is_stored_as_invalid(client, device, ana):
    client.post("/api/v1/readings", json=payload(temperature_c=None, humidity_pct=None), headers=device["key"])
    item = client.get(f"/api/v1/devices/{device['id']}/latest", headers=ana).json()["reading"]
    assert item["temperature_c"] is None and item["valid"]["temperature"] is False
    assert item["valid"]["light"] is True and item["sensor_fault"] is True


# ---------- R3 / F5: idempotency
def test_duplicate_seq_creates_one_row(client, device):
    assert client.post("/api/v1/readings", json=payload(7), headers=device["key"]).status_code == 201
    second = client.post("/api/v1/readings", json=payload(7), headers=device["key"])
    assert second.status_code == 200 and second.json()["status"] == "duplicate"
    assert count_readings() == 1


# ---------- pagination + stats
def test_pagination_and_order(client, device, ana):
    for s in range(1, 6):
        client.post("/api/v1/readings", json=payload(s), headers=device["key"])
    page = client.get(f"/api/v1/devices/{device['id']}/readings?limit=2&offset=1", headers=ana).json()
    assert page["total"] == 5 and [i["seq"] for i in page["items"]] == [4, 3]


def test_limit_is_bounded(client, device, ana):
    assert client.get(f"/api/v1/devices/{device['id']}/readings?limit=100000", headers=ana).status_code == 400


def test_stats(client, device, ana):
    client.post("/api/v1/readings", json=payload(1, temperature_c=20), headers=device["key"])
    client.post("/api/v1/readings", json=payload(2, temperature_c=30, humidity_pct=None), headers=device["key"])
    s = client.get(f"/api/v1/devices/{device['id']}/stats", headers=ana).json()
    assert s["readings"] == 2 and s["temperature_c"]["avg"] == 25.0 and s["invalid"]["humidity"] == 1


# ---------- R6 / R7: offline is reported, old value is flagged as stale
def test_device_goes_offline_and_data_is_stale(client, device, ana):
    client.post("/api/v1/readings", json=payload(), headers=device["key"])
    with SessionLocal() as db:
        d = db.get(Device, device["id"])
        d.last_seen_at = utcnow() - timedelta(minutes=10)
        db.commit()
    latest = client.get(f"/api/v1/devices/{device['id']}/latest", headers=ana).json()
    assert latest["status"]["online"] is False and latest["stale"] is True
    assert latest["status"]["no_data_since"] is not None


def test_unknown_device_is_404(client, ana):
    assert client.get("/api/v1/devices/nope-123/latest", headers=ana).status_code == 404
