import time
import pika
import json
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal

# Ensure tables are created in PostgreSQL before we start
models.Base.metadata.create_all(bind=engine)

def start_auditor():
    """Listens to RabbitMQ and saves evidence to the database."""
    credentials = pika.PlainCredentials("soar_admin", "supersecret")
    parameters = pika.ConnectionParameters("localhost", 5672, "/", credentials)
    
    connection = None
    
    # --- THE RETRY LOOP ---
    for i in range(5):
        try:
            print(f"[*] Attempting to connect to RabbitMQ (Attempt {i+1}/5)...")
            connection = pika.BlockingConnection(parameters)
            break # If it connects, break out of the loop!
        except Exception as e:
            print(f"[-] Connection failed. Retrying in 3 seconds... ({repr(e)})")
            time.sleep(3)
            
    if not connection:
        print("[-] FATAL: Could not connect to RabbitMQ after 5 attempts.")
        return
    # ----------------------

    try:
        channel = connection.channel()
        channel.queue_declare(queue='audit_logs_queue', durable=True)

        def callback(ch, method, properties, body):
            data = json.loads(body)
            db = SessionLocal()
            try:
                # Save the artifact to the Data Access Layer (DAL)
                new_log = models.AuditLog(
                    service_name=data.get("service", "unknown"),
                    action=data.get("action", "unknown_action"),
                    details=data.get("details", {})
                )
                db.add(new_log)
                db.commit()
                print(f"[+] Artifact Saved: {new_log.action}")
            except Exception as e:
                print(f"[-] Database Error: {repr(e)}")
                db.rollback()
            finally:
                db.close()
                # Tell RabbitMQ we successfully processed the message
                ch.basic_ack(delivery_tag=method.delivery_tag)

        # Only give this worker 1 message at a time
        channel.basic_qos(prefetch_count=1)
        print("[*] Artifact Recorder successfully connected and listening for audit events...")
        
        channel.basic_consume(queue='audit_logs_queue', on_message_callback=callback)
        channel.start_consuming()

    except Exception as e:
        print(f"[-] Artifact Recorder failed: {repr(e)}")

if __name__ == "__main__":
    start_auditor()