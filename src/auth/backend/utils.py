import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_for_dev_only")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Setup bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored database hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password for storing in the database."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates the short-lived JWT for API access."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default fallback if not provided
        expire = datetime.utcnow() + timedelta(minutes=5)
        
    to_encode.update({"exp": expire, "token_type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    """Generates the long-lived JWT for the Sliding Session."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "token_type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def publish_audit_log(event_type: str, user_email: str, status: str, details: dict = {}):
    """
    Dummy function to simulate pushing an audit event to RabbitMQ.
    The Artifact Recording Service will eventually listen for these.
    """
    audit_message = {
        "event_type": event_type,           # e.g., "AUTH_LOGIN_ATTEMPT"
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user": user_email,
        "status": status,                   # "SUCCESS" or "FAILURE"
        "details": details
    }
    
    # TODO: Replace this print statement with actual pika/RabbitMQ channel.basic_publish logic
    print(f"\n[>>> RABBITMQ AUDIT BUS <<<] Routing Key: audit.auth.{status.lower()}")
    print(json.dumps(audit_message, indent=2))
    print("-" * 50)