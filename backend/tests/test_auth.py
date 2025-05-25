import os, sys, pathlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]  # /Adityaverse
sys.path.insert(0, str(ROOT_DIR))

from backend.main import app
from backend.db.session import Base, get_db
from backend.core.config import settings
from unittest.mock import AsyncMock, patch



# ─── Setup test database ─────────────────────────────
SQLALCHEMY_DATABASE_URL = str(settings.database_url)

engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base.metadata.create_all(bind=engine)

# ─── Override get_db dependency ──────────────────────
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ─── Actual Test ─────────────────────────────────────
# def test_register_and_login():
#     # Register
#     response = client.post("/api/v1/auth/register", json={
#         "email": "test5@example.com",
#         "password": "test1234"
#     })
#     print("register response:", response.status_code, response.json())

#     assert response.status_code == 200
#     assert "access_token" in response.json()

#     # Login
#     response = client.post("/api/v1/auth/login", data={
#         "username": "test5@example.com",
#         "password": "test1234"
#     })
#     print("login response:", response.status_code, response.json())

#     assert response.status_code == 200
#     assert "access_token" in response.json()


def test_mock_google_oauth(monkeypatch):
    fake_user = {
        "email": "googleuser3@example.com",
        "name": "Google User",
        "picture": "https://example.com/avatar.png"
    }

    # Mock the OAuth client methods
    monkeypatch.setattr(
        "backend.core.oauth.oauth.google.authorize_access_token",
        AsyncMock(return_value={"access_token": "fake-token"})
    )
    monkeypatch.setattr(
        "backend.core.oauth.oauth.google.parse_id_token",
        AsyncMock(return_value=fake_user)
    )

    # TestClient will follow the redirect into /oauth-success
    with TestClient(app, base_url="http://testserver", raise_server_exceptions=False) as client:
        response = client.get(
            "/api/v1/auth/google/callback?code=fake-code&state=state123"
        )

    # The dummy oauth_success handler should return 200 with our token
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "OAuth successful"
    assert body["token"].startswith("eyJ")  # JWT tokens begin with eyJ