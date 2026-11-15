-- PostgreSQL schema (the API creates the same tables through SQLAlchemy; this file is the reference
-- script for the DB deliverable). Time is always UTC.
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
    created_at    TIMESTAMP    NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

CREATE TABLE devices (
    id            VARCHAR(64) PRIMARY KEY,                 -- device_id sent by the board
    owner_id      INTEGER     NOT NULL REFERENCES users(id),
    name          VARCHAR(120) NOT NULL,
    api_key_hash  VARCHAR(64) NOT NULL,                    -- sha256, the key itself is never stored
    interval_s    INTEGER     NOT NULL DEFAULT 20 CHECK (interval_s BETWEEN 15 AND 3600),
    created_at    TIMESTAMP   NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    last_seen_at  TIMESTAMP
);

CREATE TABLE readings (
    id            SERIAL PRIMARY KEY,
    device_id     VARCHAR(64) NOT NULL REFERENCES devices(id),
    seq           INTEGER     NOT NULL,
    ts            TIMESTAMP   NOT NULL,                    -- measured on the board (NTP)
    received_at   TIMESTAMP   NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    temperature_c DOUBLE PRECISION CHECK (temperature_c BETWEEN -40 AND 80),
    humidity_pct  DOUBLE PRECISION CHECK (humidity_pct BETWEEN 0 AND 100),
    light_pct     DOUBLE PRECISION CHECK (light_pct BETWEEN 0 AND 100),
    temp_valid    BOOLEAN     NOT NULL,
    hum_valid     BOOLEAN     NOT NULL,
    light_valid   BOOLEAN     NOT NULL,
    origin        VARCHAR(12) NOT NULL DEFAULT 'device' CHECK (origin IN ('device','simulated')),
    CONSTRAINT uq_device_seq UNIQUE (device_id, seq)       -- idempotency (R3 / F5)
);
CREATE INDEX ix_readings_device_ts ON readings (device_id, ts);
