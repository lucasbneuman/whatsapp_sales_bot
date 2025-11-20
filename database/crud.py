"""CRUD operations for database models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.models import Config, FollowUp, Message, User


# ============================================================================
# USER OPERATIONS
# ============================================================================


async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    """
    Retrieve user by phone number.

    Args:
        db: Database session
        phone: User's phone number

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Retrieve user by ID.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, phone: str, name: Optional[str] = None, email: Optional[str] = None) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        phone: User's phone number
        name: User's name (optional)
        email: User's email (optional)

    Returns:
        Created User object
    """
    user = User(phone=phone, name=name, email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: int, **kwargs: Any) -> Optional[User]:
    """
    Update user fields.

    Args:
        db: Database session
        user_id: User's ID
        **kwargs: Fields to update

    Returns:
        Updated User object if found, None otherwise
    """
    user = await get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
    return user


async def get_all_active_users(db: AsyncSession, limit: int = 100) -> List[User]:
    """
    Get all users with recent activity.

    Args:
        db: Database session
        limit: Maximum number of users to retrieve

    Returns:
        List of User objects
    """
    result = await db.execute(
        select(User)
        .where(User.last_message_at.isnot(None))
        .order_by(desc(User.last_message_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_users_by_mode(db: AsyncSession, mode: str) -> List[User]:
    """
    Get all users in a specific conversation mode.

    Args:
        db: Database session
        mode: Conversation mode (AUTO/MANUAL/NEEDS_ATTENTION)

    Returns:
        List of User objects
    """
    result = await db.execute(
        select(User)
        .where(User.conversation_mode == mode)
        .order_by(desc(User.last_message_at))
    )
    return list(result.scalars().all())


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================


async def create_message(
    db: AsyncSession,
    user_id: int,
    message_text: str,
    sender: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Message:
    """
    Create a new message.

    Args:
        db: Database session
        user_id: User's ID
        message_text: Message content
        sender: 'user' or 'bot'
        metadata: Optional metadata (intent, sentiment, etc.)

    Returns:
        Created Message object
    """
    message = Message(user_id=user_id, message_text=message_text, sender=sender, message_metadata=metadata)
    db.add(message)

    # Update user's message count and last message time
    user = await get_user_by_id(db, user_id)
    if user:
        user.total_messages += 1
        user.last_message_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)
    return message


async def get_user_messages(db: AsyncSession, user_id: int, limit: int = 50) -> List[Message]:
    """
    Get conversation history for a user.

    Args:
        db: Database session
        user_id: User's ID
        limit: Maximum number of messages to retrieve

    Returns:
        List of Message objects ordered by timestamp
    """
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.timestamp)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_recent_messages(db: AsyncSession, user_id: int, count: int = 10) -> List[Message]:
    """
    Get most recent messages for a user.

    Args:
        db: Database session
        user_id: User's ID
        count: Number of recent messages to retrieve

    Returns:
        List of Message objects ordered by timestamp (most recent last)
    """
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(desc(Message.timestamp))
        .limit(count)
    )
    messages = list(result.scalars().all())
    return list(reversed(messages))  # Return in chronological order


# ============================================================================
# FOLLOW-UP OPERATIONS
# ============================================================================


async def create_follow_up(
    db: AsyncSession,
    user_id: int,
    scheduled_time: datetime,
    message: str,
    follow_up_count: int = 0,
    job_id: Optional[str] = None,
) -> FollowUp:
    """
    Create a follow-up task.

    Args:
        db: Database session
        user_id: User's ID
        scheduled_time: When to send the follow-up
        message: Message to send
        follow_up_count: Current follow-up count for this user
        job_id: APScheduler job ID

    Returns:
        Created FollowUp object
    """
    follow_up = FollowUp(
        user_id=user_id,
        scheduled_time=scheduled_time,
        message=message,
        follow_up_count=follow_up_count,
        job_id=job_id,
    )
    db.add(follow_up)
    await db.commit()
    await db.refresh(follow_up)
    return follow_up


async def get_pending_follow_ups(db: AsyncSession) -> List[FollowUp]:
    """
    Get all pending follow-ups.

    Args:
        db: Database session

    Returns:
        List of pending FollowUp objects
    """
    result = await db.execute(
        select(FollowUp)
        .where(FollowUp.status == "pending")
        .order_by(FollowUp.scheduled_time)
    )
    return list(result.scalars().all())


async def get_user_follow_ups(db: AsyncSession, user_id: int) -> List[FollowUp]:
    """
    Get all follow-ups for a specific user.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        List of FollowUp objects
    """
    result = await db.execute(
        select(FollowUp)
        .where(FollowUp.user_id == user_id)
        .order_by(desc(FollowUp.created_at))
    )
    return list(result.scalars().all())


async def update_follow_up_status(db: AsyncSession, follow_up_id: int, status: str) -> Optional[FollowUp]:
    """
    Update follow-up status.

    Args:
        db: Database session
        follow_up_id: FollowUp ID
        status: New status (pending/sent/cancelled)

    Returns:
        Updated FollowUp object if found, None otherwise
    """
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    follow_up = result.scalar_one_or_none()
    if follow_up:
        follow_up.status = status
        await db.commit()
        await db.refresh(follow_up)
    return follow_up


async def cancel_user_pending_follow_ups(db: AsyncSession, user_id: int) -> int:
    """
    Cancel all pending follow-ups for a user.

    Args:
        db: Database session
        user_id: User's ID

    Returns:
        Number of follow-ups cancelled
    """
    result = await db.execute(
        select(FollowUp)
        .where(FollowUp.user_id == user_id, FollowUp.status == "pending")
    )
    follow_ups = result.scalars().all()

    count = 0
    for follow_up in follow_ups:
        follow_up.status = "cancelled"
        count += 1

    await db.commit()
    return count


# ============================================================================
# CONFIG OPERATIONS
# ============================================================================


async def get_config(db: AsyncSession, key: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration value by key.

    Args:
        db: Database session
        key: Configuration key

    Returns:
        Configuration value (JSON) if found, None otherwise
    """
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()
    return config.value if config else None


async def set_config(db: AsyncSession, key: str, value: Dict[str, Any]) -> Config:
    """
    Set configuration value (create or update).

    Args:
        db: Database session
        key: Configuration key
        value: Configuration value (will be stored as JSON)

    Returns:
        Config object
    """
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()

    if config:
        config.value = value
        config.updated_at = datetime.utcnow()
    else:
        config = Config(key=key, value=value)
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config


async def get_all_configs(db: AsyncSession) -> Dict[str, Any]:
    """
    Get all configuration values.

    Args:
        db: Database session

    Returns:
        Dictionary mapping config keys to values
    """
    result = await db.execute(select(Config))
    configs = result.scalars().all()
    return {config.key: config.value for config in configs}


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================


async def init_default_configs(db: AsyncSession) -> None:
    """
    Initialize default configuration values if they don't exist.

    Args:
        db: Database session
    """
    defaults = {
        "system_prompt": "You are a friendly and professional sales assistant. Your goal is to help customers find the right product and complete their purchase smoothly.",
        "payment_link": "https://example.com/pay",
        "response_delay": 1.0,  # seconds
        "text_audio_ratio": 0,  # 0-100, 0 = text only
        "use_emojis": True,
        "tts_voice": "nova",
        "rag_enabled": False,
    }

    for key, value in defaults.items():
        existing = await get_config(db, key)
        if existing is None:
            await set_config(db, key, value)
