import time
from collections import defaultdict
from typing import List, Dict, Optional

# --- CONFIGURATION ---
CORRELATION_WINDOW_SECONDS = 300  # 5 Minutes
THRESHOLD_COUNT = 3               # If > 3 alerts in window, create Incident

class Incident:
    """
    Represents a grouped set of alerts that require action.
    """
    def __init__(self, key: str, alerts: List[Dict]):
        self.id = f"inc_{int(time.time())}"
        self.correlated_key = key  # e.g., The IP Address "192.168.1.5"
        self.alerts = alerts
        self.timestamp = time.time()
        self.severity = max([a.get('normalized_severity', 1) for a in alerts])
        self.description = f"Correlation: {len(alerts)} alerts detected for {key}"

class CorrelationEngine:
    def __init__(self):
        # A Dictionary of Lists:  {'192.168.1.5': [Alert1, Alert2], '10.0.0.1': [Alert1]}
        self.alert_buffer = defaultdict(list)

    def process_alert(self, alert: Dict) -> Optional[Incident]:
        """
        Main entry point.
        1. Adds alert to buffer.
        2. Cleans up old alerts.
        3. Checks if threshold is met.
        4. Returns an Incident if created, else None.
        """
        # 1. Extract the Correlation Key (e.g., Source IP)
        # If the alert has no source IP, we might skip correlation or use another key.
        key = alert.get('source_ip') or alert.get('src')
        
        if not key:
            print(f"Skipping correlation for alert {alert.get('alert_id')}: No Key found.")
            return None

        # 2. Add to Buffer
        print(f"Adding alert {alert.get('alert_id')} to buffer for Key: {key}")
        self.alert_buffer[key].append(alert)

        # 3. Clean up (Remove alerts older than the window)
        self._prune_buffer(key)

        # 4. Check Logic (The "Rule")
        if len(self.alert_buffer[key]) >= THRESHOLD_COUNT:
            return self._create_incident(key)
        
        return None

    def _prune_buffer(self, key: str):
        """Removes alerts that are too old to matter."""
        current_time = time.time()
        # Keep only alerts within the window
        # Assuming alert['timestamp'] is parseable or we use ingestion time
        # For simplicity, we just use current time of processing here
        valid_alerts = []
        for alert in self.alert_buffer[key]:
            # In a real app, parse the alert string timestamp to unix time.
            # Here we assume the alert object has an 'arrival_time' added by us, 
            # or we just rely on index if the stream is fast.
            # Let's assume we attached a local processing timestamp:
            alert_time = alert.get('_local_timestamp', current_time)
            
            if current_time - alert_time < CORRELATION_WINDOW_SECONDS:
                valid_alerts.append(alert)
        
        self.alert_buffer[key] = valid_alerts

    def _create_incident(self, key: str) -> Incident:
        """
        Bundles the alerts into an Incident and clears the buffer 
        so we don't trigger the same incident twice.
        """
        alerts_to_bundle = self.alert_buffer[key]
        
        # Create the object
        new_incident = Incident(key, alerts_to_bundle)
        
        # Clear the buffer for this key (Reset state)
        # Alternatively, you could keep them and only alert on "New" ones, 
        # but clearing is safer to avoid spam.
        del self.alert_buffer[key]
        
        print(f"!!! INCIDENT CREATED: {new_incident.description} !!!")
        return new_incident
    
    # --- SIMULATION RUNNER ---
if __name__ == "__main__":
    engine = CorrelationEngine()

    # Create a Mock Alert Structure
    def make_alert(ip, name):
        return {
            "alert_id": str(time.time()),
            "source_ip": ip,
            "type": name,
            "normalized_severity": 3,
            "_local_timestamp": time.time()
        }

    print("--- SCENARIO: Brute Force Attack ---")
    
    # 1. First bad login
    result = engine.process_alert(make_alert("10.0.0.5", "Failed Login"))
    print(f"Result: {result}")  # Should be None

    # 2. Second bad login
    result = engine.process_alert(make_alert("10.0.0.5", "Failed Login"))
    print(f"Result: {result}")  # Should be None

    # 3. Third bad login (Should Trigger!)
    result = engine.process_alert(make_alert("10.0.0.5", "Failed Login"))
    
    if result:
        print(f"SUCCESS: Created Incident {result.id} with {len(result.alerts)} alerts.")
    else:
        print("FAILED: No incident created.")


# TODO: Test the code and add ddos checker