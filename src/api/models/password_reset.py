"""
PasswordResetToken model for password recovery
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, UUID, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.connection import Base


class PasswordResetToken(Base):
    """Tokens for secure password reset flow"""
    __tablename__ = "password_reset_tokens"

    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")

    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="token_not_expired"),
    )

    def __repr__(self):
        return f"<PasswordResetToken(user_id='{self.user_id}', used={self.used}, expires_at='{self.expires_at}')>"
