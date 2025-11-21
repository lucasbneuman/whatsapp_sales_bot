"""Conversation state definition for LangGraph."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class ConversationState(TypedDict):
    """
    State object for the sales conversation graph.

    This state is passed between nodes and updated throughout the conversation.
    """

    # Message history
    messages: List[BaseMessage]

    # User identification
    user_phone: str
    user_name: Optional[str]
    user_email: Optional[str]

    # Conversation analysis (updated continuously)
    intent_score: float  # 0-1 scale, how likely user is to buy
    sentiment: str  # positive/neutral/negative
    stage: str  # welcome/qualifying/nurturing/closing/sold/follow_up

    # Conversation control
    conversation_mode: str  # AUTO/MANUAL/NEEDS_ATTENTION

    # Collected data
    collected_data: Dict[str, Any]  # Structured data collected from user

    # Transaction tracking
    payment_link_sent: bool
    follow_up_scheduled: Optional[datetime]
    follow_up_count: int

    # Conversation summary
    conversation_summary: Optional[str]  # AI-generated summary

    # Current response (set by nodes)
    current_response: Optional[str]

    # Configuration (loaded from DB/Gradio)
    config: Dict[str, Any]

    # Database session reference (for CRUD operations within nodes)
    db_session: Optional[Any]

    # Database user object (for HubSpot sync and updates)
    db_user: Optional[Any]
