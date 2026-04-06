# import uuid
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from datetime import datetime
# from typing import List, Dict, Any
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# # --- CONFIGURATION ---
# APP_VERSION = "1.0.0"
# SERVICE_NAME = "notification-service-01"

# # Email configuration (change these)
# SENDER_EMAIL = "sender@gmail.com"
# SENDER_PASSWORD = "app_password"

# app = FastAPI(title="SOAR Notification Service", version=APP_VERSION)


# # --- DATA MODELS ---

# class IncidentNotification(BaseModel):
#     """
#     Represents the notification payload received from the Brain/Incident service.
#     """
#     incident_id: str
#     severity: int
#     description: str
#     correlated_key: str
#     created_at: int


# # --- CORE NOTIFICATION SERVICE CLASS ---

# class NotificationService:
#     """
#     Handles analyst notification logic.
#     """

#     def __init__(self):
#         pass

#     # 1️ INPUT METHOD (Blank as requested)
#     def receive_incident(self, incident: IncidentNotification):
#         """
#         Entry point for receiving incident notifications.
#         """
#         pass

#     # 2️ DATABASE EMAIL FETCH METHOD
#     def get_analyst_emails(self) -> List[str]:
#         """
#         Fetch list of analyst emails from database.
#         Currently returns test emails.
#         """
#         return [
#             "analyst@gmail.com"
#         ]


#     # 3 EMAIL NOTIFICATION LOGIC
#     def send_notification(self, incident: IncidentNotification):
#         """
#         Sends notification email to analysts.
#         """

#         email_list = self.get_analyst_emails()

#         if not email_list:
#             print("No analyst emails found. Skipping email notification.")
#             return

#         subject = f"SOAR Alert - Incident {incident.incident_id}"

#         body = f"""
# SOAR Incident Notification

# Incident ID: {incident.incident_id}
# Severity: {incident.severity}
# Description: {incident.description}
# Source Key: {incident.correlated_key}
# Created At: {incident.created_at}

# Please investigate immediately.
# """

#         try:
#             # Connect to SMTP server
#             server = smtplib.SMTP("smtp.gmail.com", 587)
#             server.starttls()

#             # Login to email
#             server.login(SENDER_EMAIL, SENDER_PASSWORD)

#             for recipient in email_list:

#                 message = MIMEMultipart()
#                 message["From"] = SENDER_EMAIL
#                 message["To"] = recipient
#                 message["Subject"] = subject

#                 message.attach(MIMEText(body, "plain"))

#                 server.sendmail(
#                     SENDER_EMAIL,
#                     recipient,
#                     message.as_string()
#                 )

#                 print(f"Email sent to {recipient}")

#             server.quit()

#             print("Notification email dispatched successfully.")

#         except Exception as e:
#             print(f"Failed to send email notification: {e}")


# # --- SERVICE INSTANCE ---
# notification_handler = NotificationService()


# # --- API ENDPOINTS ---

# @app.get("/")
# def health_check():
#     return {"status": "running", "service": SERVICE_NAME}


# @app.post("/api/v1/notify")
# def notify_analyst(payload: IncidentNotification):
#     """
#     API endpoint to receive incident notification.
#     """

#     try:
#         notification_handler.receive_incident(payload)
#         notification_handler.send_notification(payload)

#         return {
#             "status": "success",
#             "message": "Notification processed",
#             "notification_id": str(uuid.uuid4())
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # --- RUN SERVICE ---
# if __name__ == "__main__":
#     import uvicorn
#     print(f"Starting {SERVICE_NAME} on port 8001...")
#     uvicorn.run(app, host="0.0.0.0", port=8001)



# main.py
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import get_db

APP_VERSION = "1.0.0"
SERVICE_NAME = "notification-service-01"

SENDER_EMAIL = "sender@gmail.com"
SENDER_PASSWORD = "app_password"

app = FastAPI(title="SOAR Notification Service", version=APP_VERSION)

class IncidentNotification(BaseModel):
    incident_id: str
    severity: int
    description: str
    correlated_key: str
    created_at: int

class NotificationService:
    # --- BUSINESS LOGIC LAYER ---
    def get_analyst_emails(self, db: Session) -> List[str]:
        """Fetches active analyst emails from the Database."""
        analysts = db.query(models.User).filter(models.User.role == models.UserRole.analyst).all()
        return [analyst.email for analyst in analysts]

    def send_notification(self, incident: IncidentNotification, db: Session):
        email_list = self.get_analyst_emails(db)

        if not email_list:
            print("[-] No analyst emails found. Skipping notification.")
            return

        subject = f"SOAR Alert - Incident {incident.incident_id}"
        body = f"""SOAR Incident Notification
Incident ID: {incident.incident_id}
Severity: {incident.severity}
Description: {incident.description}
Source Key: {incident.correlated_key}

Please investigate immediately.
"""
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for recipient in email_list:
                message = MIMEMultipart()
                message["From"] = SENDER_EMAIL
                message["To"] = recipient
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain"))

                server.sendmail(SENDER_EMAIL, recipient, message.as_string())
                print(f"[+] Email sent to {recipient}")

            server.quit()
        except Exception as e:
            print(f"[-] Failed to send email notification: {e}")

notification_handler = NotificationService()

@app.get("/")
def health_check():
    return {"status": "running", "service": SERVICE_NAME}

@app.post("/api/v1/notify")
def notify_analyst(payload: IncidentNotification, db: Session = Depends(get_db)):
    try:
        notification_handler.send_notification(payload, db)
        return {
            "status": "success",
            "message": "Notification processed",
            "notification_id": str(uuid.uuid4())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # MOVED TO PORT 8003 TO AVOID COLLISION WITH AUTH SERVICE
    print(f"Starting {SERVICE_NAME} on port 8003...")
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)