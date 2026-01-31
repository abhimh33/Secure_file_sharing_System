"""
Base Model with common fields
"""

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class BaseModel(Base):
    """Abstract base model with common fields"""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
