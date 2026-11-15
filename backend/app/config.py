import logging
import os
import secrets

log = logging.getLogger("iot")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iot.db")
# Render/Heroku style URLs start with postgres://, SQLAlchemy wants postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Tokens stop working after a restart: fine for dev, and loud on purpose.
    JWT_SECRET = secrets.token_urlsafe(48)
    log.warning("JWT_SECRET not set: using a random one for this process only")

JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
ALLOW_REGISTRATION = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"
OFFLINE_AFTER_SECONDS = int(os.getenv("OFFLINE_AFTER_SECONDS", "75"))

# Physical limits used to reject nonsense (HTTP 400). DHT22 spec: -40..80 C, 0..100 %RH.
TEMP_RANGE = (-40.0, 80.0)
HUM_RANGE = (0.0, 100.0)
LIGHT_RANGE = (0.0, 100.0)
