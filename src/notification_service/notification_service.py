import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- CONFIGURATION ---
APP_VERSION = "1.0.0"
SERVICE_NAME = "notification-service-01"

app = FastAPI(title="SOAR Notification Service", version=APP_VERSION)


# --- DATA MODELS ---

class IncidentNotification(BaseModel):
    """
    Represents the notification payload received from the Brain/Incident service.
    """
    incident_id: str
    severity: int
    description: str
    correlated_key: str
    created_at: int


# --- CORE NOTIFICATION SERVICE CLASS ---

class NotificationService:
    """
    Handles analyst notification logic.
    """

    def __init__(self):
        pass

    # 1️ INPUT METHOD (Blank for now as requested)
    def receive_incident(self, incident: IncidentNotification):
        """
        Entry point for receiving incident notifications.
        Implementation intentionally left blank.
        """
        pass

    # 2️ DATABASE EMAIL FETCH METHOD (Blank for now)
    def get_analyst_emails(self) -> List[str]:
        """
        Fetch list of analyst emails from database.
        Currently returns empty list.
        """
        # TODO: Implement DB query logic
        return []

    # 3️ INTERNAL NOTIFICATION LOGIC
    def send_notification(self, incident: IncidentNotification):
        """
        Sends notification to analysts.
        Currently simulated via console output.
        """

        email_list = self.get_analyst_emails()

        print("\n[NOTIFICATION SERVICE]")
        print(f"Incident ID: {incident.incident_id}")
        print(f"Severity: {incident.severity}")
        print(f"Description: {incident.description}")
        print(f"Recipients: {email_list}")
        print("Notification dispatched.\n")


# --- SERVICE INSTANCE ---
notification_handler = NotificationService()


# --- API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "running", "service": SERVICE_NAME}


@app.post("/api/v1/notify")
def notify_analyst(payload: IncidentNotification):
    """
    API endpoint to receive incident notification.
    """

    try:
        notification_handler.receive_incident(payload)
        notification_handler.send_notification(payload)

        return {
            "status": "success",
            "message": "Notification processed",
            "notification_id": str(uuid.uuid4())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- RUN SERVICE ---
if __name__ == "__main__":
    import uvicorn
    print(f"Starting {SERVICE_NAME} on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)