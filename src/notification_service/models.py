# models.py
import enum
from sqlalchemy import Column, String, Enum, UUID
from database import Base

class UserRole(str, enum.Enum):
    admin = 'admin'
    analyst = 'analyst'

class User(Base):
    """Read-only model just to fetch emails from the Auth schema."""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)