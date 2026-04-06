import uuid
from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base

class SecurityAlert(Base):
    """Stores raw telemetry and logs from external security tools."""
    __tablename__ = "security_alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_tool = Column(String(100), nullable=False)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    
    # Normalized severity score (1-4)
    normalized_severity = Column(Integer, nullable=False) 
    event_type = Column(String(100), nullable=False)
    raw_log_payload = Column(JSON, nullable=True) 
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())