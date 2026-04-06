# import time
# from collections import defaultdict
# from typing import List, Dict, Optional

# # --- CONFIGURATION ---
# CORRELATION_WINDOW_SECONDS = 300  # 5 Minutes
# THRESHOLD_COUNT = 3               # If > 3 alerts in window, create Incident

# CORRELATION_WINDOW_MILLIS = CORRELATION_WINDOW_SECONDS * 1000  # Convert to milliseconds

# class Incident:
#     """
#     Represents a grouped set of alerts that require action.
#     """
#     def __init__(self, key: str, alerts: List[Dict]):
#         self.id = f"inc_{int(time.time())}"
#         self.correlated_key = key  # e.g., The IP Address
#         self.alerts = alerts
#         self.timestamp = time.time()
#         self.severity = max([a.get('normalized_severity', 1) for a in alerts])
#         self.description = f"Correlation: {len(alerts)} alerts detected for {key}"

# class CorrelationEngine:
#     def __init__(self):
#         # A Dictionary of Lists:  {'192.168.1.5': [Alert1, Alert2], '10.0.0.1': [Alert1]}
#         self.alert_buffer = defaultdict(list)

#     def process_alert(self, alert: Dict) -> Optional[Incident]:
#         """
#         Main entry point.
#         1. Adds alert to buffer.
#         2. Cleans up old alerts.
#         3. Checks if threshold is met.
#         4. Returns an Incident if created, else None.
#         """
#         # 1. Extract the Correlation Key (e.g., Source IP)
#         # If the alert has no source IP, we might skip correlation or use another key.
#         key = alert.get('source_ip') or alert.get('src')
        
#         if not key:
#             print(f"Skipping correlation for alert {alert.get('alert_id')}: No Key found.")
#             return None

#         # 2. Add to Buffer
#         print(f"Adding alert {alert.get('alert_id')} to buffer for Key: {key}")
#         self.alert_buffer[key].append(alert)

#         # 3. Clean up (Remove alerts older than the window)
#         self._prune_buffer(key)

#         # 4. Check Logic (The "Rule")
#         if len(self.alert_buffer[key]) >= THRESHOLD_COUNT:
#             return self._create_incident(key)
        
#         return None

#     def _prune_buffer(self, key: str):
#         """Removes alerts that are too old to matter."""
#         current_time = int(time.time() * 1000)  # Current time in millisecond
#         # Keep only alerts within the window
#         # alert['timestamp'] is unix time in millisecond
        
#         valid_alerts = []
#         for alert in self.alert_buffer[key]:
            
#             alert_time = alert.get('timestamp') or alert.get('_local_timestamp')
            
#             if current_time - alert_time < CORRELATION_WINDOW_MILLIS:
#                 valid_alerts.append(alert)
        
#         self.alert_buffer[key] = valid_alerts

#     def _create_incident(self, key: str) -> Incident:
#         """
#         Bundles the alerts into an Incident and clears the buffer 
#         so we don't trigger the same incident twice.
#         """
#         alerts_to_bundle = self.alert_buffer[key]
        
#         # Create the object
#         new_incident = Incident(key, alerts_to_bundle)
        
#         # Clear the buffer for this key (Reset state)
#         # Alternatively, you could keep them and only alert on "New" ones, 
#         # but clearing is safer to avoid spam.
#         del self.alert_buffer[key]
        
#         print(f"!!! INCIDENT CREATED: {new_incident.description} !!!")
#         return new_incident
    
#     # --- SIMULATION RUNNER ---
# if __name__ == "__main__":
#     engine = CorrelationEngine()

#     # Create a Mock Alert Structure
#     def make_alert(ip, name):
#         return {
#             "alert_id": str(time.time()),
#             "source_ip": ip,
#             "type": name,
#             "normalized_severity": 3,
#             "_local_timestamp": time.time()
#         }

#     print("--- SCENARIO: Brute Force Attack ---")
    
#     # 1. First bad login
#     result = engine.process_alert(make_alert("10.0.0.5", "Failed Login"))
#     print(f"Result: {result}")  # Should be None

#     # 2. Second bad login
#     result = engine.process_alert(make_alert("10.0.0.5", "Failed Login"))
#     print(f"Result: {result}")  # Should be None

#     # 3. Third bad login (Should Trigger!)
#     result = engine.process_alert(make_alert("10.0.0.5", "Failed Login"))
    
#     if result:
#         print(f"SUCCESS: Created Incident {result.id} with {len(result.alerts)} alerts.")
#     else:
#         print("FAILED: No incident created.")


# # TODO: Test the code and add ddos checker
# # BUG: it will only create incidents of a fixed size
# # we need dynamic incident creation, add alerts to already created incidents if they match the key and are within the time window.
# # also requires a service to remove old alerts which are not part of any incident

import os
import uvicorn
import pika
import json
import threading
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models
from database import engine, get_db, SessionLocal

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)
load_dotenv()

app = FastAPI(title="SOAR Correlation Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BUSINESS LOGIC LAYER (The Brain) ---
# def evaluate_alert_rules(alert_id: str):
#     """
#     Core BLL Function. Evaluates if an incoming alert should trigger an Incident.
#     Rule: 3 or more alerts from the same source IP in the last 5 minutes = INCIDENT.
#     """
#     db = SessionLocal()
#     try:
#         # 1. Fetch the new alert
#         new_alert = db.query(models.SecurityAlert).filter(models.SecurityAlert.alert_id == alert_id).first()
#         if not new_alert or not new_alert.source_ip:
#             return

#         print(f"[*] Brain analyzing Alert {alert_id} from IP: {new_alert.source_ip}")

#         # 2. Time Window Calculation (Last 5 minutes)
#         five_mins_ago = datetime.utcnow() - timedelta(minutes=5)

#         # 3. Correlation Logic
#         recent_alerts = db.query(models.SecurityAlert).filter(
#             models.SecurityAlert.source_ip == new_alert.source_ip,
#             models.SecurityAlert.timestamp >= five_mins_ago,
#             models.SecurityAlert.incident_id == None # Only count unassigned alerts
#         ).all()

#         if len(recent_alerts) >= 3:
#             print(f"[!] THRESHOLD MET: {len(recent_alerts)} alerts from {new_alert.source_ip}. Generating Incident!")
            
#             # 4. Create the Incident
#             new_incident = models.Incident(
#                 title=f"Multiple Suspicious Events from {new_alert.source_ip}",
#                 severity=models.SeverityLevel.high,
#                 status=models.IncidentStatus.open
#             )
#             db.add(new_incident)
#             db.flush() # Get the new incident ID before committing

#             # 5. Link all recent alerts to this new Incident
#             for alert in recent_alerts:
#                 alert.incident_id = new_incident.incident_id
            
#             db.commit()
#             print(f"[+] Incident {new_incident.incident_id} created successfully.")
            
#             # FUTURE EXPANSION: Push to Playbook RabbitMQ Queue here!

#     except Exception as e:
#         print(f"[-] Correlation Engine Error: {e}")
#         db.rollback()
#     finally:
#         db.close()

def evaluate_alert_rules(alert_id: str):
    """
    Core BLL Function. Evaluates if an incoming alert should trigger or update an Incident.
    """
    db = SessionLocal()
    try:
        # 1. Fetch the new alert
        new_alert = db.query(models.SecurityAlert).filter(models.SecurityAlert.alert_id == alert_id).first()
        if not new_alert or not new_alert.source_ip:
            return

        print(f"[*] Brain analyzing Alert {alert_id} from IP: {new_alert.source_ip}")

        # --- BUG FIX: DYNAMIC INCIDENTS ---
        # 2. Check if there is ALREADY an open incident for this IP
        # We do this by finding if any existing alert from this IP is tied to an OPEN incident
        existing_alert_with_incident = db.query(models.SecurityAlert).join(models.Incident).filter(
            models.SecurityAlert.source_ip == new_alert.source_ip,
            models.Incident.status == models.IncidentStatus.open
        ).first()

        if existing_alert_with_incident:
            # Attach the new alert to the existing incident!
            active_incident_id = existing_alert_with_incident.incident_id
            new_alert.incident_id = active_incident_id
            db.commit()
            print(f"[+] Dynamic Update: Appended Alert {alert_id} to existing Incident {active_incident_id}")
            return

        # --- RULE 1: BRUTE FORCE & DDOS CHECKER ---
        # 3. If no open incident exists, count unassigned alerts in the last 5 minutes
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_alerts = db.query(models.SecurityAlert).filter(
            models.SecurityAlert.source_ip == new_alert.source_ip,
            models.SecurityAlert.timestamp >= five_mins_ago,
            models.SecurityAlert.incident_id == None 
        ).all()

        alert_count = len(recent_alerts)

        if alert_count >= 3:
            # Default to High (Brute Force)
            computed_severity = models.SeverityLevel.high
            incident_title = f"Multiple Suspicious Events from {new_alert.source_ip}"

            # DDoS Checker Upgrade!
            if alert_count >= 50:
                computed_severity = models.SeverityLevel.critical
                incident_title = f"Potential DDoS / Volumetric Attack from {new_alert.source_ip}"

            print(f"[!] THRESHOLD MET: {alert_count} alerts from {new_alert.source_ip}. Generating {computed_severity.upper()} Incident!")
            
            # 4. Create the Incident
            new_incident = models.Incident(
                title=incident_title,
                severity=computed_severity,
                status=models.IncidentStatus.open
            )
            db.add(new_incident)
            db.flush() 

            # 5. Link all recent alerts to this new Incident
            for alert in recent_alerts:
                alert.incident_id = new_incident.incident_id
            
            db.commit()
            print(f"[+] Incident {new_incident.incident_id} created successfully.")

    except Exception as e:
        print(f"[-] Correlation Engine Error: {e}")
        db.rollback()
    finally:
        db.close()

# --- RABBITMQ CONSUMER (Background Thread) ---
def start_rabbitmq_consumer():
    """Listens for new alerts from the Ingestion Service."""
    credentials = pika.PlainCredentials(os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASS", "guest"))
    parameters = pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost"), port=5672, credentials=credentials)
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='raw_alerts_queue', durable=True)

        def callback(ch, method, properties, body):
            data = json.loads(body)
            evaluate_alert_rules(data['alert_id'])
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='raw_alerts_queue', on_message_callback=callback)
        print("[*] Correlation Engine connected to RabbitMQ. Waiting for alerts...")
        channel.start_consuming()
    except Exception as e:
        print(f"[-] MQ Consumer failed: {e}")

# --- API ENDPOINTS (For Analyst Dashboard) ---
@app.get("/api/v1/incidents")
def get_open_incidents(db: Session = Depends(get_db)):
    """Allows the Frontend to view all active Incidents."""
    incidents = db.query(models.Incident).filter(models.Incident.status != models.IncidentStatus.closed).order_by(models.Incident.created_at.desc()).all()
    return {"incidents": incidents}

@app.on_event("startup")
def startup_event():
    # Start the RabbitMQ consumer in a background thread so it doesn't block the API
    thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    thread.start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    print(f"Starting Correlation API on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)