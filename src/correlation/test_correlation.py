import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your models and the function we are testing
import models
from main import evaluate_alert_rules

# --- TEST DATABASE SETUP ---
# We use a temporary in-memory SQLite database so we don't mess up your real PostgreSQL data
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database(monkeypatch):
    """
    This fixture runs before EVERY test.
    It creates fresh tables and forces your main.py to use this test database.
    """
    models.Base.metadata.create_all(bind=engine)
    
    # Force main.py to use our TestingSessionLocal instead of the real one
    monkeypatch.setattr("main.SessionLocal", TestingSessionLocal)
    
    yield # Run the test
    
    # Tear down the tables after the test finishes
    models.Base.metadata.drop_all(bind=engine)

# --- HELPER FUNCTION ---
def seed_alerts(db, ip_address, count, minutes_ago=1):
    """Helper to quickly inject fake alerts into the test database."""
    alert_ids = []
    timestamp = datetime.utcnow() - timedelta(minutes=minutes_ago)
    
    for _ in range(count):
        new_alert = models.SecurityAlert(
            source_tool="test-script",
            source_ip=ip_address,
            event_type="failed_login",
            normalized_severity=2,
            timestamp=timestamp
        )
        db.add(new_alert)
        db.commit()
        alert_ids.append(new_alert.alert_id)
        
    return alert_ids

# --- WHITE BOX TEST CASES ---

def test_under_threshold_logic():
    """Path 1: Ensures 2 alerts do NOT trigger an incident."""
    db = TestingSessionLocal()
    ip = "10.0.0.99"
    
    # Inject 2 alerts
    alert_ids = seed_alerts(db, ip, 2)
    
    # Trigger the Business Logic on the last alert
    evaluate_alert_rules(alert_ids[-1])
    
    # Verify NO incident was created
    incident_count = db.query(models.Incident).count()
    assert incident_count == 0

def test_brute_force_logic():
    """Path 2: Ensures exactly 3 alerts trigger a HIGH severity incident."""
    db = TestingSessionLocal()
    ip = "10.0.0.100"
    
    # Inject 3 alerts
    alert_ids = seed_alerts(db, ip, 3)
    
    # Trigger the logic
    evaluate_alert_rules(alert_ids[-1])
    
    # Verify EXACTLY ONE incident was created, and it is HIGH severity
    incidents = db.query(models.Incident).all()
    assert len(incidents) == 1
    assert incidents[0].severity == models.SeverityLevel.high
    assert "Multiple Suspicious Events" in incidents[0].title

def test_ddos_logic():
    """Path 3: Ensures 50 alerts trigger a CRITICAL severity incident."""
    db = TestingSessionLocal()
    ip = "10.0.0.101"
    
    # Inject 50 alerts
    alert_ids = seed_alerts(db, ip, 50)
    
    # Trigger the logic
    evaluate_alert_rules(alert_ids[-1])
    
    # Verify it was upgraded to CRITICAL
    incidents = db.query(models.Incident).all()
    assert len(incidents) == 1
    assert incidents[0].severity == models.SeverityLevel.critical
    assert "Potential DDoS" in incidents[0].title

def test_dynamic_incident_append_logic():
    """Path 4: Ensures new alerts are attached to existing OPEN incidents."""
    db = TestingSessionLocal()
    ip = "10.0.0.102"
    
    # 1. Trigger an initial Brute Force incident (3 alerts)
    initial_alerts = seed_alerts(db, ip, 3)
    evaluate_alert_rules(initial_alerts[-1])
    
    first_incident = db.query(models.Incident).first()
    assert first_incident is not None
    
    # 2. Inject ONE new alert a minute later
    new_alert_ids = seed_alerts(db, ip, 1, minutes_ago=0)
    
    # Trigger the logic on the new alert
    evaluate_alert_rules(new_alert_ids[0])
    
    # 3. Verify NO new incident was created (count should still be 1)
    assert db.query(models.Incident).count() == 1
    
    # 4. Verify the new alert was successfully attached to the existing incident
    latest_alert = db.query(models.SecurityAlert).filter(models.SecurityAlert.alert_id == new_alert_ids[0]).first()
    assert latest_alert.incident_id == first_incident.incident_id