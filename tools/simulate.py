"""Development helper: pretends to be the board so you can test the API/dashboard without hardware.

Everything it sends is tagged origin="simulated", so it is identifiable in the database
(the spec only accepts simulated data when it is declared). NEVER use it in the live demo.

  python tools/simulate.py --base http://localhost:8000 --email a@b.com --password 12345678 \
      --device-id esp32-sim-01 --count 200 --step-seconds 20
"""
import argparse
import math
import random
from datetime import datetime, timedelta, timezone

import httpx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8000")
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--device-id", default="esp32-sim-01")
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--step-seconds", type=int, default=20)
    a = p.parse_args()

    c = httpx.Client(base_url=a.base, timeout=10)
    c.post("/api/v1/auth/register", json={"email": a.email, "password": a.password})  # ok if it already exists
    tok = c.post("/api/v1/auth/login", json={"email": a.email, "password": a.password}).json()["access_token"]
    r = c.post("/api/v1/devices", json={"device_id": a.device_id, "name": "Simulated board"},
               headers={"Authorization": f"Bearer {tok}"})
    if r.status_code != 201:
        raise SystemExit(f"Could not create device ({r.status_code}): {r.text}. Use a new --device-id.")
    key = r.json()["api_key"]

    end = datetime.now(timezone.utc)
    start = end - timedelta(seconds=a.step_seconds * (a.count - 1))
    random.seed(7)
    for i in range(a.count):
        ts = start + timedelta(seconds=i * a.step_seconds)
        hour = ts.hour + ts.minute / 60
        temp = 26 + 3 * math.sin((hour - 9) / 24 * 2 * math.pi) + random.gauss(0, 0.15)
        body = {"device_id": a.device_id, "seq": i + 1, "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "temperature_c": round(temp, 2), "humidity_pct": round(60 - (temp - 26) * 2 + random.gauss(0, 0.5), 1),
                "light_pct": round(max(0, 50 + 40 * math.sin((hour - 6) / 24 * 2 * math.pi)), 1), "origin": "simulated"}
        c.post("/api/v1/readings", json=body, headers={"X-Device-Key": key}).raise_for_status()
    print(f"sent {a.count} simulated readings for {a.device_id}")


if __name__ == "__main__":
    main()
