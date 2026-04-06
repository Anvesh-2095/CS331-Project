import uuid
import enum
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class SeverityLevel(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class IncidentStatus(str, enum.Enum):
    open = 'open'
    investigating = 'investigating'
    resolved = 'resolved'
    closed = 'closed'

class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.open, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # One-to-Many: One Incident has many Alerts
    alerts = relationship("SecurityAlert", back_populates="incident")

class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_tool = Column(String(100), nullable=False)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    normalized_severity = Column(Integer, nullable=False) 
    event_type = Column(String(100), nullable=False)
    raw_log_payload = Column(JSON, nullable=True) 
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.incident_id"), nullable=True)
    incident = relationship("Incident", back_populates="alerts")