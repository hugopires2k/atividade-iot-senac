import os
import tempfile

# Must be set before the app is imported.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register_and_login(client, email="ana@example.com", password="s3cret-pass"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def ana(client):
    return register_and_login(client, "ana@example.com")


@pytest.fixture
def bruno(client):
    return register_and_login(client, "bruno@example.com")


@pytest.fixture
def device(client, ana):
    r = client.post("/api/v1/devices", json={"device_id": "esp32-lab-01", "name": "Lab"}, headers=ana)
    assert r.status_code == 201
    return {"id": "esp32-lab-01", "key": {"X-Device-Key": r.json()["api_key"]}}
