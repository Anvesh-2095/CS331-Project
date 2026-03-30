import os
import json
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

import pika
import json

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Setup bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=5))
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def publish_audit_log(event_type: str, user_email: str, status: str, details: dict = None):
    """Dummy function to simulate pushing an audit event to RabbitMQ."""
    audit_message = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user": user_email,
        "status": status,
        "details": details or {}
    }
    print(f"\n[>>> RABBITMQ AUDIT BUS <<<] Routing Key: audit.auth.{status.lower()}")
    print(json.dumps(audit_message, indent=2))
    print("-" * 50)


def publish_action_to_rabbitmq(action: str, target: str, user: str):
    """
    Connects to RabbitMQ and publishes an action for the remote agent to execute.
    """
    # 1. Connect to the local Docker RabbitMQ instance
    credentials = pika.PlainCredentials('soar_admin', 'supersecret')
    parameters = pika.ConnectionParameters(
        host='localhost', 
        port=5672, 
        credentials=credentials
    )
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 2. Ensure the queue exists before sending
        channel.queue_declare(queue='soar_actuator_queue', durable=True)

        # 3. Format the command as a JSON message
        message = {
            "action": action,
            "target": target,
            "issued_by": user,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # 4. Publish the message to the queue
        channel.basic_publish(
            exchange='',
            routing_key='soar_actuator_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
        print(f"[+] Successfully published to RabbitMQ: {message}")
        connection.close()
        return True
    
    except Exception as e:
        print(f"[-] RabbitMQ Connection Failed: {e}")
        return False