"""Unit tests for graph nodes."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from graph.nodes import (
    welcome_node,
    intent_classifier_node,
    sentiment_analyzer_node,
    data_collector_node,
    router_node,
    conversation_node,
)


@pytest.mark.asyncio
async def test_welcome_node_first_message(sample_conversation_state):
    """Test welcome node generates message for first-time users."""
    mock_llm_service = MagicMock()
    mock_llm_service.generate_response = AsyncMock(return_value="Welcome! How can I help you?")

    with patch("graph.nodes.get_llm_service", return_value=mock_llm_service):
        result = await welcome_node(sample_conversation_state)

        assert "current_response" in result
        assert result["current_response"] == "Welcome! How can I help you?"
        assert result["stage"] == "welcome"


@pytest.mark.asyncio
async def test_welcome_node_returning_user(sample_conversation_state):
    """Test welcome node skips message for returning users."""
    # Add more messages to simulate returning user
    sample_conversation_state["messages"] = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi there!"),
        HumanMessage(content="I'm back"),
    ]

    result = await welcome_node(sample_conversation_state)

    # Should return empty dict (no updates)
    assert result == {}


@pytest.mark.asyncio
async def test_intent_classifier_node(sample_conversation_state):
    """Test intent classification node."""
    mock_llm_service = MagicMock()
    mock_llm_service.classify_intent = AsyncMock(
        return_value={"category": "interested", "score": 0.7}
    )

    with patch("graph.nodes.get_llm_service", return_value=mock_llm_service):
        result = await intent_classifier_node(sample_conversation_state)

        assert "intent_score" in result
        assert result["intent_score"] == 0.7


@pytest.mark.asyncio
async def test_sentiment_analyzer_node_positive(sample_conversation_state):
    """Test sentiment analysis with positive sentiment."""
    mock_llm_service = MagicMock()
    mock_llm_service.analyze_sentiment = AsyncMock(return_value="positive")

    with patch("graph.nodes.get_llm_service", return_value=mock_llm_service):
        result = await sentiment_analyzer_node(sample_conversation_state)

        assert result["sentiment"] == "positive"
        assert "conversation_mode" not in result  # Should not trigger handoff


@pytest.mark.asyncio
async def test_sentiment_analyzer_node_negative(sample_conversation_state):
    """Test sentiment analysis with negative sentiment."""
    mock_llm_service = MagicMock()
    mock_llm_service.analyze_sentiment = AsyncMock(return_value="negative")

    with patch("graph.nodes.get_llm_service", return_value=mock_llm_service):
        result = await sentiment_analyzer_node(sample_conversation_state)

        assert result["sentiment"] == "negative"


@pytest.mark.asyncio
async def test_data_collector_node(sample_conversation_state):
    """Test data collector extracts user information."""
    # Remove existing user_name and user_email to test extraction
    sample_conversation_state["user_name"] = None
    sample_conversation_state["user_email"] = None

    mock_llm_service = MagicMock()
    mock_llm_service.extract_data = AsyncMock(
        return_value={"name": "John Doe", "email": "john@example.com"}
    )

    mock_hubspot_service = MagicMock()
    mock_hubspot_service.enabled = False

    with patch("graph.nodes.get_llm_service", return_value=mock_llm_service), \
         patch("graph.nodes.get_hubspot_service", return_value=mock_hubspot_service):

        result = await data_collector_node(sample_conversation_state)

        assert "collected_data" in result
        assert result["collected_data"]["name"] == "John Doe"
        assert result["user_name"] == "John Doe"
        assert result["user_email"] == "john@example.com"


@pytest.mark.asyncio
async def test_conversation_node(sample_conversation_state):
    """Test conversation node generates response."""
    mock_llm_service = MagicMock()
    mock_llm_service.generate_response = AsyncMock(
        return_value="I can help you with that!"
    )

    mock_rag_service = MagicMock()
    mock_rag_service.retrieve_context = AsyncMock(return_value=None)

    with patch("graph.nodes.get_llm_service", return_value=mock_llm_service), \
         patch("graph.nodes.get_rag_service", return_value=mock_rag_service):

        result = await conversation_node(sample_conversation_state)

        assert result["current_response"] == "I can help you with that!"
        assert "stage" in result


def test_router_node_high_intent(sample_conversation_state):
    """Test router routes to closing with high intent."""
    sample_conversation_state["intent_score"] = 0.9

    result = router_node(sample_conversation_state)

    assert result == "closing"


def test_router_node_low_intent(sample_conversation_state):
    """Test router routes to follow-up with low intent."""
    sample_conversation_state["intent_score"] = 0.1

    result = router_node(sample_conversation_state)

    assert result == "follow_up"


def test_router_node_needs_attention(sample_conversation_state):
    """Test router routes to handoff when needs attention."""
    sample_conversation_state["conversation_mode"] = "NEEDS_ATTENTION"

    result = router_node(sample_conversation_state)

    assert result == "handoff"


def test_router_node_default(sample_conversation_state):
    """Test router defaults to conversation node."""
    sample_conversation_state["intent_score"] = 0.5

    result = router_node(sample_conversation_state)

    assert result == "conversation"
