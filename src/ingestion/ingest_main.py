import uvicorn
import uuid
from datetime import datetime, time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Dict, Any

# --- CONFIGURATION ---
APP_VERSION = "1.0.0"
SERVICE_NAME = "ingest-service-01"

# Initialize the API
app = FastAPI(title="SOAR Ingestion Service", version=APP_VERSION)

# --- DATA MODELS (Pydantic) ---
# It rejects bad data automatically.

class RawAlert(BaseModel):
    """
    The expected format from our 'Simulation Script'.
    It mimics a generic security tool's output.
    """
    tool_id: str = Field(..., description="ID of the source tool (e.g., firewall-01)")
    event_type: str = Field(..., description="Type of event (e.g., malware, intrusion)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    description: str = Field(..., description="Human-readable message")
    source_ip: Optional[str] = Field(None, description="Attacker IP, if applicable")
    destination_ip: Optional[str] = Field(None, description="Target IP, if applicable")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Extra messy data")

class NormalizedAlert(BaseModel):
    """
    RawAlert -> NormalizedAlert.
    """
    alert_id: str
    timestamp: str
    ingested_at: str
    source: str
    normalized_severity: int  # 1 (Low) to 4 (Critical)
    type: str
    src: Optional[str]
    dst: Optional[str]
    details: str

# --- HELPER FUNCTIONS ---

def normalize_severity(level: str) -> int:
    """Converts text severity to a comparable integer."""
    mapping = {
        "low": 1,
        "info": 1,
        "medium": 2,
        "warning": 2,
        "high": 3,
        "critical": 4,
        "fatal": 4
    }
    return mapping.get(level.lower(), 1) # Default to 1 (Low)

def publish_to_queue(alert: NormalizedAlert):
    """
    Simulates pushing to RabbitMQ.
    this would use `pika` to send bytes.
    """
    print(f"\n[>>> MQ PUBLISH] Sending Alert to Brain: {alert.alert_id}")
    print(f"      |-- Source: {alert.source}")
    print(f"      |-- Type: {alert.type}")
    print(f"      |-- Severity: {alert.normalized_severity}")
    # Real code: channel.basic_publish(exchange='', routing_key='alerts', body=alert.json())

# --- API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "running", "service": SERVICE_NAME}

@app.post("/api/v1/ingest")
async def ingest_alert(alert: RawAlert):
    """
    Main ingestion endpoint.
    1. Validates Schema (done auto by Pydantic)
    2. Normalizes Data
    3. Pushes to Queue
    """
    
    # Generate unique ID for tracking
    unique_id = str(uuid.uuid4())
    # current_time = datetime.utcnow().isoformat()
    current_time = int(time.time() * 1000)  # milliseconds unix timestamp
    
    # Normalization Logic
    clean_alert = NormalizedAlert(
        alert_id=unique_id,
        timestamp=current_time, # TODO: check if alert has its own timestamp and use that instead
        ingested_at=current_time,
        source=alert.tool_id,
        normalized_severity=normalize_severity(alert.severity),
        type=alert.event_type.lower().replace(" ", "_"),
        src=alert.source_ip,
        dst=alert.destination_ip,
        details=alert.description
    )
    
    # Hand off to Message Bus
    publish_to_queue(clean_alert)
    
    return {
        "status": "accepted",
        "alert_id": unique_id,
        "message": "Alert queued for processing"
    }

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME} on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)