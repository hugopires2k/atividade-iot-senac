from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from . import config


class RegisterIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str
    password: str


class DeviceIn(BaseModel):
    device_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,64}$")
    name: str = Field(min_length=1, max_length=120)
    interval_s: int = Field(default=20, ge=15, le=3600)  # ThingSpeak free tier needs >= 15 s


class ReadingIn(BaseModel):
    """One measurement. A null value means 'sensor failed' (R5), never a fake number."""
    device_id: str = Field(pattern=r"^[A-Za-z0-9_-]{3,64}$")
    seq: int = Field(ge=0, le=2**31 - 1)
    ts: datetime
    temperature_c: Optional[float] = Field(default=None, allow_inf_nan=False)
    humidity_pct: Optional[float] = Field(default=None, allow_inf_nan=False)
    light_pct: Optional[float] = Field(default=None, allow_inf_nan=False)
    origin: Literal["device", "simulated"] = "device"

    @staticmethod
    def _check(v, lo_hi, name):
        if v is not None and not (lo_hi[0] <= v <= lo_hi[1]):
            raise ValueError(f"{name} out of physical range {lo_hi}")
        return v

    @field_validator("temperature_c")
    @classmethod
    def _t(cls, v):
        return cls._check(v, config.TEMP_RANGE, "temperature_c")

    @field_validator("humidity_pct")
    @classmethod
    def _h(cls, v):
        return cls._check(v, config.HUM_RANGE, "humidity_pct")

    @field_validator("light_pct")
    @classmethod
    def _l(cls, v):
        return cls._check(v, config.LIGHT_RANGE, "light_pct")

    @field_validator("ts")
    @classmethod
    def _ts(cls, v: datetime):
        if v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if v > now + timedelta(minutes=5):
            raise ValueError("ts is in the future")
        if v < datetime(2024, 1, 1):
            raise ValueError("ts is implausibly old (clock not synced?)")
        return v
