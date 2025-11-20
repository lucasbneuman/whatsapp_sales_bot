"""Helper functions for the application."""

from datetime import datetime
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard format.

    Args:
        phone: Phone number (may include whatsapp: prefix)

    Returns:
        Formatted phone number (e.g., +1234567890)
    """
    # Remove whatsapp: prefix if present
    if phone.startswith("whatsapp:"):
        phone = phone.replace("whatsapp:", "")

    # Remove spaces, hyphens, parentheses
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Ensure starts with +
    if not phone.startswith("+"):
        phone = f"+{phone}"

    return phone


def messages_to_dict(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """
    Convert LangChain messages to dict format for JSON serialization.

    Args:
        messages: List of BaseMessage objects

    Returns:
        List of message dicts
    """
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({
                "role": "user",
                "content": msg.content,
                "timestamp": getattr(msg, "timestamp", datetime.utcnow().isoformat()),
            })
        elif isinstance(msg, AIMessage):
            result.append({
                "role": "assistant",
                "content": msg.content,
                "timestamp": getattr(msg, "timestamp", datetime.utcnow().isoformat()),
            })
    return result


def dict_to_messages(message_dicts: List[Dict[str, Any]]) -> List[BaseMessage]:
    """
    Convert dict format to LangChain messages.

    Args:
        message_dicts: List of message dicts

    Returns:
        List of BaseMessage objects
    """
    result = []
    for msg_dict in message_dicts:
        if msg_dict["role"] == "user":
            result.append(HumanMessage(content=msg_dict["content"]))
        elif msg_dict["role"] == "assistant":
            result.append(AIMessage(content=msg_dict["content"]))
    return result


def get_conversation_summary(messages: List[BaseMessage], max_messages: int = 5) -> str:
    """
    Get a brief summary of recent conversation.

    Args:
        messages: List of messages
        max_messages: Maximum number of recent messages to include

    Returns:
        Formatted conversation summary
    """
    recent = messages[-max_messages:] if len(messages) > max_messages else messages

    summary_lines = []
    for msg in recent:
        role = "User" if isinstance(msg, HumanMessage) else "Bot"
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        summary_lines.append(f"{role}: {content}")

    return "\n".join(summary_lines)


def calculate_intent_emoji(intent_score: float) -> str:
    """
    Get emoji representation of intent score.

    Args:
        intent_score: Intent score (0-1)

    Returns:
        Emoji string
    """
    if intent_score >= 0.8:
        return "🔥"  # Hot lead
    elif intent_score >= 0.6:
        return "✨"  # Interested
    elif intent_score >= 0.4:
        return "👀"  # Browsing
    else:
        return "❄️"  # Cold


def calculate_sentiment_emoji(sentiment: str) -> str:
    """
    Get emoji representation of sentiment.

    Args:
        sentiment: Sentiment string

    Returns:
        Emoji string
    """
    emoji_map = {
        "positive": "😊",
        "neutral": "😐",
        "negative": "😟",
    }
    return emoji_map.get(sentiment, "😐")


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime for display.

    Args:
        dt: Datetime object

    Returns:
        Formatted string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sanitize_for_json(obj: Any) -> Any:
    """
    Sanitize object for JSON serialization.

    Args:
        obj: Object to sanitize

    Returns:
        JSON-serializable object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, BaseMessage):
        return obj.content
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    else:
        return obj
