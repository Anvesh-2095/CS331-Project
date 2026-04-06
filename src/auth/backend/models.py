import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, text
# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base

class UserRole(str, enum.Enum):
    admin = 'admin'
    analyst = 'analyst'

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_string = Column(String(512), unique=True, nullable=False, index=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")

class AuthAuditLog(Base):
    __tablename__ = "auth_audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_attempted = Column(String(255), nullable=False)
    attempt_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    status = Column(String(50), nullable=False)
    user_agent = Column(String)