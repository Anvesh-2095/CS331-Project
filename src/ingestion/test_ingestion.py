import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Import from your ingestion main.py
from main import app, normalize_severity, get_db
import models

# --- TEST DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

def override_get_db():
    """Overrides the FastAPI dependency to use our isolated test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# --- WHITE BOX TEST CASES ---

def test_data_transformation_logic():
    """Tests the internal BLL logic for normalizing severity strings to integers."""
    assert normalize_severity("low") == 1
    assert normalize_severity("INFO") == 1  # Tests case insensitivity
    assert normalize_severity("high") == 3
    assert normalize_severity("fatal") == 4
    assert normalize_severity("completely_made_up_string") == 1  # Tests fallback default


def test_validation_logic_failure():
    """Tests the Pydantic schema validation by sending intentionally bad data."""
    # Missing required fields like 'tool_id', 'event_type', and 'severity'
    bad_payload = {
        "description": "I am a broken alert",
        "source_ip": "10.0.0.1"
    }
    
    response = client.post("/api/v1/ingest", json=bad_payload)
    
    # 422 Unprocessable Entity means our validation successfully caught the bad data!
    assert response.status_code == 422


@patch("main.publish_to_queue") 
def test_successful_ingestion_pipeline(mock_rabbitmq):
    """
    Tests the full DAL insertion and BLL transformation.
    We @patch (mock) RabbitMQ so the test doesn't fail if Docker is turned off.
    """
    valid_payload = {
        "tool_id": "PaloAlto-FW-01",
        "event_type": "Brute Force Attempt",
        "severity": "high",
        "description": "Multiple failed SSH logins",
        "source_ip": "192.168.1.150"
    }

    response = client.post("/api/v1/ingest", json=valid_payload)
    
    # 1. Verify API responded correctly
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "alert_id" in data

    # 2. Verify RabbitMQ BLL function was triggered exactly once
    mock_rabbitmq.assert_called_once()

    # 3. Verify Data Access Layer (DAL) successfully saved it to the DB
    db = TestingSessionLocal()
    saved_alert = db.query(models.SecurityAlert).filter(models.SecurityAlert.alert_id == data["alert_id"]).first()
    
    assert saved_alert is not None
    assert saved_alert.source_tool == "PaloAlto-FW-01"
    
    # 4. Verify Data Transformation actually altered the data before saving
    assert saved_alert.normalized_severity == 3
    assert saved_alert.event_type == "brute_force_attempt"  # Should be lowercased with underscores