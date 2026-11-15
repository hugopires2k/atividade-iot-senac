from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
                        String, UniqueConstraint, create_engine)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from . import config

connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def utcnow() -> datetime:
    """Naive UTC datetime. Everything is stored in UTC; the 'Z' is added when serializing."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user | admin
    created_at = Column(DateTime, nullable=False, default=utcnow)
    devices = relationship("Device", back_populates="owner")


class Device(Base):
    __tablename__ = "devices"
    id = Column(String(64), primary_key=True)  # the device_id sent by the board
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(120), nullable=False)
    api_key_hash = Column(String(64), nullable=False)  # sha256 of the device key
    interval_s = Column(Integer, nullable=False, default=20)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    last_seen_at = Column(DateTime, nullable=True)
    owner = relationship("User", back_populates="devices")


class Reading(Base):
    __tablename__ = "readings"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(64), ForeignKey("devices.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    ts = Column(DateTime, nullable=False)  # when the board measured (NTP, UTC)
    received_at = Column(DateTime, nullable=False, default=utcnow)
    temperature_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    light_pct = Column(Float, nullable=True)
    temp_valid = Column(Boolean, nullable=False, default=False)
    hum_valid = Column(Boolean, nullable=False, default=False)
    light_valid = Column(Boolean, nullable=False, default=False)
    origin = Column(String(12), nullable=False, default="device")  # device | simulated

    __table_args__ = (
        UniqueConstraint("device_id", "seq", name="uq_device_seq"),  # idempotency (R3)
        Index("ix_readings_device_ts", "device_id", "ts"),
    )


def init_db():
    Base.metadata.create_all(engine)
