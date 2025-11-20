"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "LOG_LEVEL": "ERROR",  # Reduce log noise in tests
    }
    with pytest.MonkeyPatch.context() as mp:
        for key, value in env_vars.items():
            mp.setenv(key, value)
        yield


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_config():
    """Sample configuration for tests."""
    return {
        "system_prompt": "You are a helpful sales assistant.",
        "use_emojis": True,
        "rag_enabled": False,
        "response_delay": 0,
        "text_audio_ratio": 0,
        "payment_link": "https://example.com/pay",
        "tts_voice": "nova",
    }


@pytest.fixture
def sample_conversation_state(sample_config):
    """Sample conversation state for tests."""
    from langchain_core.messages import HumanMessage
    from graph.state import ConversationState

    state: ConversationState = {
        "messages": [HumanMessage(content="Hello")],
        "user_phone": "+1234567890",
        "user_name": "Test User",
        "user_email": "test@example.com",
        "intent_score": 0.5,
        "sentiment": "neutral",
        "stage": "welcome",
        "conversation_mode": "AUTO",
        "collected_data": {},
        "payment_link_sent": False,
        "follow_up_scheduled": None,
        "follow_up_count": 0,
        "current_response": None,
        "config": sample_config,
        "db_session": None,
    }
    return state
