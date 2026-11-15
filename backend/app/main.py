"""IoT Environment Monitor - API (previa v0.9).

Board -> POST /api/v1/readings (X-Device-Key)  |  People -> JWT (dashboard, PWA).
"""
import logging
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import config
from .db import Device, Reading, User, init_db, utcnow
from .schemas import DeviceIn, LoginIn, ReadingIn, RegisterIn
from .security import (create_token, current_user, device_from_key, get_db, hash_key,
                       hash_password, new_device_key, owned_device, verify_password)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("iot.api")

app = FastAPI(
    title="IoT Environment Monitor API",
    version="0.9.0",
    description="Ingests sensor readings from an ESP32 board and serves them to the dashboard and the mobile app.",
)
init_db()


def iso(dt):
    return dt.isoformat(timespec="seconds") + "Z" if dt else None


# The spec asks for 400 (not FastAPI's default 422) on malformed or out-of-range input.
@app.exception_handler(RequestValidationError)
async def validation_to_400(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(p) for p in e["loc"][1:]), "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": "Invalid request", "errors": errors})


def status_of(dev: Device) -> dict:
    now = utcnow()
    online = dev.last_seen_at is not None and (now - dev.last_seen_at).total_seconds() <= config.OFFLINE_AFTER_SECONDS
    return {"online": online, "last_contact": iso(dev.last_seen_at),
            "no_data_since": None if online else iso(dev.last_seen_at)}


def reading_out(r: Reading) -> dict:
    return {
        "seq": r.seq, "ts": iso(r.ts), "received_at": iso(r.received_at), "origin": r.origin,
        "temperature_c": r.temperature_c, "humidity_pct": r.humidity_pct, "light_pct": r.light_pct,
        "valid": {"temperature": r.temp_valid, "humidity": r.hum_valid, "light": r.light_valid},
        "sensor_fault": not (r.temp_valid and r.hum_valid and r.light_valid),
    }


# ------------------------------------------------------------------ health
@app.get("/health", tags=["ops"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok", "time": iso(utcnow())}
    except Exception:
        log.exception("health check failed")
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "down"})


# ------------------------------------------------------------------ auth
@app.post("/api/v1/auth/register", status_code=201, tags=["auth"])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if not config.ALLOW_REGISTRATION:
        raise HTTPException(403, "Registration is disabled")
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email}


@app.post("/api/v1/auth/login", tags=["auth"])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"access_token": create_token(user), "token_type": "bearer"}


# ------------------------------------------------------------------ devices
@app.post("/api/v1/devices", status_code=201, tags=["devices"])
def create_device(body: DeviceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.get(Device, body.device_id):
        raise HTTPException(409, "device_id already exists")
    key = new_device_key()
    db.add(Device(id=body.device_id, owner_id=user.id, name=body.name,
                  interval_s=body.interval_s, api_key_hash=hash_key(key)))
    db.commit()
    # The key is shown once. Only its hash is stored.
    return {"device_id": body.device_id, "name": body.name, "api_key": key}


@app.get("/api/v1/devices", tags=["devices"])
def list_devices(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Device)
    if user.role != "admin":
        q = q.filter(Device.owner_id == user.id)
    return [{"device_id": d.id, "name": d.name, "interval_s": d.interval_s, **status_of(d)} for d in q.all()]


# ------------------------------------------------------------------ ingestion (board)
@app.post("/api/v1/readings", tags=["readings"])
def ingest(body: ReadingIn, dev: Device = Depends(device_from_key), db: Session = Depends(get_db)):
    if body.device_id != dev.id:
        raise HTTPException(403, "This key does not belong to that device_id")
    row = Reading(
        device_id=dev.id, seq=body.seq, ts=body.ts,
        temperature_c=body.temperature_c, humidity_pct=body.humidity_pct, light_pct=body.light_pct,
        temp_valid=body.temperature_c is not None,
        hum_valid=body.humidity_pct is not None,
        light_valid=body.light_pct is not None,
        origin=body.origin,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:  # same (device_id, seq) again -> idempotent, no second row
        db.rollback()
        dev = db.get(Device, dev.id)
        dev.last_seen_at = utcnow()
        db.commit()
        return JSONResponse(status_code=200, content={"status": "duplicate", "seq": body.seq})
    dev.last_seen_at = utcnow()  # every reading doubles as a heartbeat (R7)
    db.commit()
    if row.temp_valid is False or row.hum_valid is False or row.light_valid is False:
        log.warning("sensor fault device=%s seq=%s valid=%s/%s/%s", dev.id, body.seq,
                    row.temp_valid, row.hum_valid, row.light_valid)
    return JSONResponse(status_code=201, content={"status": "stored", "seq": body.seq})


# ------------------------------------------------------------------ queries (people)
@app.get("/api/v1/devices/{device_id}/readings", tags=["readings"])
def list_readings(device_id: str, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_device(device_id, user, db)
    q = db.query(Reading).filter(Reading.device_id == device_id)
    total = q.count()
    rows = q.order_by(Reading.seq.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [reading_out(r) for r in rows]}


@app.get("/api/v1/devices/{device_id}/latest", tags=["readings"])
def latest(device_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dev = owned_device(device_id, user, db)
    r = db.query(Reading).filter(Reading.device_id == device_id).order_by(Reading.seq.desc()).first()
    st = status_of(dev)
    # R6: never present an old value as if it were current.
    return {"device_id": dev.id, "name": dev.name, "status": st, "stale": not st["online"],
            "reading": reading_out(r) if r else None}


@app.get("/api/v1/devices/{device_id}/stats", tags=["readings"])
def stats(device_id: str, hours: int = Query(24, ge=1, le=168),
          user: User = Depends(current_user), db: Session = Depends(get_db)):
    """BI indicators for the dashboard: descriptive stats, invalid counts and availability."""
    dev = owned_device(device_id, user, db)
    since = utcnow() - timedelta(hours=hours)
    base = db.query(Reading).filter(Reading.device_id == device_id, Reading.ts >= since)
    n = base.count()
    agg = db.query(
        func.min(Reading.temperature_c), func.avg(Reading.temperature_c), func.max(Reading.temperature_c),
        func.min(Reading.humidity_pct), func.avg(Reading.humidity_pct), func.max(Reading.humidity_pct),
        func.avg(Reading.light_pct),
    ).filter(Reading.device_id == device_id, Reading.ts >= since).one()
    r2 = lambda v: None if v is None else round(float(v), 2)  # noqa: E731
    expected = hours * 3600 / dev.interval_s
    return {
        "window_hours": hours, "readings": n,
        "invalid": {
            "temperature": base.filter(Reading.temp_valid.is_(False)).count(),
            "humidity": base.filter(Reading.hum_valid.is_(False)).count(),
            "light": base.filter(Reading.light_valid.is_(False)).count(),
        },
        "temperature_c": {"min": r2(agg[0]), "avg": r2(agg[1]), "max": r2(agg[2])},
        "humidity_pct": {"min": r2(agg[3]), "avg": r2(agg[4]), "max": r2(agg[5])},
        "light_pct": {"avg": r2(agg[6])},
        "availability_pct": round(min(100.0, 100.0 * n / expected), 1) if expected else None,
        "status": status_of(dev),
    }


# ------------------------------------------------------------------ static front-ends
ROOT = Path(__file__).resolve().parents[2]
for route, folder in (("/dashboard", "frontend"), ("/app", "mobile")):
    if (ROOT / folder).is_dir():
        app.mount(route, StaticFiles(directory=ROOT / folder, html=True), name=folder)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/dashboard/")
