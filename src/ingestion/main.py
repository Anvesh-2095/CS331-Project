import os
import uvicorn
import uuid
import pika
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models
from database import engine, get_db

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

load_dotenv()

APP_VERSION = "1.0.0"
SERVICE_NAME = "ingest-service-01"

app = FastAPI(title="SOAR Ingestion Service", version=APP_VERSION)

# --- DATA MODELS (Pydantic) ---
class RawAlert(BaseModel):
    tool_id: str = Field(..., description="ID of the source tool (e.g., firewall-01)")
    event_type: str = Field(..., description="Type of event (e.g., malware, intrusion)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    description: str = Field(..., description="Human-readable message")
    source_ip: Optional[str] = Field(None, description="Attacker IP, if applicable")
    destination_ip: Optional[str] = Field(None, description="Target IP, if applicable")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Extra messy data")

# --- HELPER FUNCTIONS ---
def normalize_severity(level: str) -> int:
    """Converts text severity to a comparable integer for the Correlation Engine."""
    mapping = {"low": 1, "info": 1, "medium": 2, "warning": 2, "high": 3, "critical": 4, "fatal": 4}
    return mapping.get(level.lower(), 1)

def publish_to_queue(alert_id: str, severity: int):
    """
    Business Logic Layer: Publishes the ID of the new alert to RabbitMQ 
    so the Correlation Engine knows to wake up and analyze it.
    """
    credentials = pika.PlainCredentials(os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASS", "guest"))
    parameters = pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost"), port=5672, credentials=credentials)
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='raw_alerts_queue', durable=True)

        message = {
            "alert_id": alert_id,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        channel.basic_publish(
            exchange='',
            routing_key='raw_alerts_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
        )
        print(f"[+] Successfully published Alert {alert_id} to RabbitMQ.")
        connection.close()
    except Exception as e:
        print(f"[-] MQ Publish Failed: {e}")

# --- API ENDPOINTS ---
@app.get("/")
def health_check():
    return {"status": "running", "service": SERVICE_NAME}

@app.post("/api/v1/ingest")
async def ingest_alert(alert: RawAlert, db: Session = Depends(get_db)):
    """
    Main ingestion endpoint.
    1. Validates Schema (Pydantic)
    2. Transforms Data (Data Transformation BLL)
    3. Saves to Database (DAL)
    4. Pushes to Queue (BLL Communication)
    """
    
    # 1. Data Transformation
    norm_severity = normalize_severity(alert.severity)
    clean_event_type = alert.event_type.lower().replace(" ", "_")
    
    # 2. Data Access Layer (DAL) - Save to PostgreSQL
    new_db_alert = models.SecurityAlert(
        source_tool=alert.tool_id,
        source_ip=alert.source_ip,
        destination_ip=alert.destination_ip,
        normalized_severity=norm_severity,
        event_type=clean_event_type,
        raw_log_payload=alert.raw_payload or {"description": alert.description}
    )
    
    try:
        db.add(new_db_alert)
        db.commit()
        db.refresh(new_db_alert)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {e}")

    # 3. Business Logic Layer (BLL) - Notify the Correlation Engine
    publish_to_queue(str(new_db_alert.alert_id), norm_severity)
    
    return {
        "status": "accepted",
        "alert_id": str(new_db_alert.alert_id),
        "message": "Alert saved and queued for processing."
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting {SERVICE_NAME} on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)