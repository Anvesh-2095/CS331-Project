import uuid
from sqlalchemy import Column, String, JSON, DateTime, UUID
from sqlalchemy.sql import func
from database import Base

class AuditLog(Base):
    """Immutable ledger for all system actions and evidence."""
    __tablename__ = "audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())