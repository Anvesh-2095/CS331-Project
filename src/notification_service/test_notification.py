# test_notification.py
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from main import app, get_db
import models

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
def setup_test_users():
    """Inject an Admin and an Analyst into the test DB."""
    db = TestingSessionLocal()
    db.query(models.User).delete()
    
    analyst = models.User(user_id=uuid.uuid4(), email="analyst@soar.local", role=models.UserRole.analyst)
    admin = models.User(user_id=uuid.uuid4(), email="admin@soar.local", role=models.UserRole.admin)
    
    db.add(analyst)
    db.add(admin)
    db.commit()
    db.close()

# --- WHITE BOX TEST CASES ---

@patch("smtplib.SMTP") 
def test_notification_routing_logic(mock_smtp):
    """
    Path 1: Ensures the BLL correctly filters emails.
    It should send an email to the Analyst, but NOT the Admin.
    """
    payload = {
        "incident_id": "inc-123",
        "severity": 4,
        "description": "DDoS Detected",
        "correlated_key": "192.168.1.1",
        "created_at": 1678886400
    }
    
    response = client.post("/api/v1/notify", json=payload)
    
    # Verify API success
    assert response.status_code == 200
    
    # Verify SMTP was called
    assert mock_smtp.called
    
    # Fetch the instance of the mocked SMTP server
    mock_server_instance = mock_smtp.return_value
    
    # Ensure sendmail was called exactly ONCE (because there is only 1 analyst)
    assert mock_server_instance.sendmail.call_count == 1
    
    # Check that the email went to the analyst, not the admin
    args, kwargs = mock_server_instance.sendmail.call_args
    assert args[1] == "analyst@soar.local"