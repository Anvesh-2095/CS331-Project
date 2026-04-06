import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
import time

from main import app, get_db
import models
import utils

# --- TEST DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool 
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_user():
    """Injects a fake user into the test database before tests run."""
    db = TestingSessionLocal()
    # Clear old data just in case
    db.query(models.User).delete()
    
    test_user = models.User(
        email="test@soar.local",
        password_hash=utils.get_password_hash("securepassword123"),
        full_name="Test User",
        role=models.UserRole.analyst
    )
    db.add(test_user)
    db.commit()
    db.close()

# --- WHITE BOX TEST CASES ---

@patch("utils.publish_audit_log") # Mock RabbitMQ audit logs
def test_successful_login(mock_audit):
    """Path 1: Ensures valid credentials return tokens."""
    payload = {
        "email": "test@soar.local",
        "password": "securepassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "analyst"
    
    # Verify the audit log was triggered
    mock_audit.assert_called_once()

@patch("utils.publish_audit_log")
def test_failed_login_bad_password(mock_audit):
    """Path 2: Ensures invalid credentials are rejected."""
    payload = {
        "email": "test@soar.local",
        "password": "WRONG_PASSWORD"
    }
    
    response = client.post("/api/v1/auth/login", json=payload)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

@patch("utils.publish_audit_log")
def test_sliding_session_refresh(mock_audit):
    """Path 3: Ensures a valid refresh token yields a new access token."""
    # 1. Log in first to get a real refresh token
    login_payload = {
        "email": "test@soar.local",
        "password": "securepassword123"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    refresh_token = login_response.json()["refresh_token"]

    time.sleep(1);
    
    # 2. Attempt to refresh the session
    refresh_payload = {
        "refresh_token": refresh_token
    }
    refresh_response = client.post("/api/v1/auth/refresh", json=refresh_payload)
    
    # 3. Verify new tokens were issued
    assert refresh_response.status_code == 200
    new_data = refresh_response.json()
    assert "access_token" in new_data
    assert new_data["access_token"] != login_response.json()["access_token"]