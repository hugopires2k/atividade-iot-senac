import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import config
from .db import Device, SessionLocal, User, utcnow

bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- passwords (PBKDF2, stdlib only) ----
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return hmac.compare_digest(candidate, digest)


# ---- JWT for people (dashboard / app) ----
def create_token(user: User) -> str:
    payload = {"sub": str(user.id), "role": user.role,
               "exp": utcnow() + timedelta(minutes=config.JWT_EXPIRE_MINUTES)}
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise HTTPException(401, "Missing bearer token")
    try:
        data = jwt.decode(creds.credentials, config.JWT_SECRET, algorithms=["HS256"])
        user = db.get(User, int(data["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired token")
    if user is None:
        raise HTTPException(401, "Unknown user")
    return user


# ---- device keys (the board talks to the API with X-Device-Key) ----
def new_device_key() -> str:
    return secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def device_from_key(x_device_key: str = Header(default=None), db: Session = Depends(get_db)) -> Device:
    if not x_device_key:
        raise HTTPException(401, "Missing X-Device-Key header")
    h = hash_key(x_device_key)
    for dev in db.query(Device).all():  # tiny table; constant-time compare on each hash
        if hmac.compare_digest(dev.api_key_hash, h):
            return dev
    raise HTTPException(401, "Invalid device key")


def owned_device(device_id: str, user: User, db: Session) -> Device:
    """Object-level authorization: a user only touches their own devices (OWASP API1:2023)."""
    dev = db.get(Device, device_id)
    if dev is None:
        raise HTTPException(404, "Device not found")
    if dev.owner_id != user.id and user.role != "admin":
        raise HTTPException(403, "This device belongs to another user")
    return dev
