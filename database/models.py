"""SQLAlchemy models for sales bot database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User/Customer model representing WhatsApp contacts."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Conversation tracking
    intent_score = Column(Float, default=0.0)  # 0-1 scale
    sentiment = Column(String(20), default="neutral")  # positive/neutral/negative
    stage = Column(String(50), default="welcome")  # welcome/qualifying/nurturing/closing/sold/follow_up
    conversation_mode = Column(String(20), default="AUTO")  # AUTO/MANUAL/NEEDS_ATTENTION
    conversation_summary = Column(Text, nullable=True)  # AI-generated summary of conversation

    # Activity tracking
    total_messages = Column(Integer, default=0)
    last_message_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone}, name={self.name})>"


class Message(Base):
    """Message model for storing conversation history."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_text = Column(Text, nullable=False)
    sender = Column(String(10), nullable=False)  # 'user' or 'bot'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    message_metadata = Column(JSON, nullable=True)  # Store intent, sentiment at that moment

    # Relationships
    user = relationship("User", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, user_id={self.user_id}, sender={self.sender})>"


class FollowUp(Base):
    """Follow-up scheduling model."""

    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending/sent/cancelled
    follow_up_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    job_id = Column(String(100), nullable=True)  # APScheduler job ID

    # Relationships
    user = relationship("User", back_populates="follow_ups")

    def __repr__(self) -> str:
        return f"<FollowUp(id={self.id}, user_id={self.user_id}, status={self.status})>"


class Config(Base):
    """Configuration storage model."""

    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Config(key={self.key})>"
