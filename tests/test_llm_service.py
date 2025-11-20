"""Unit tests for LLM service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from services.llm_service import LLMService


@pytest.fixture
def llm_service():
    """Create an LLM service instance for testing."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        service = LLMService(openai_api_key="test-key")
        return service


@pytest.mark.asyncio
async def test_generate_response_with_basemessage_objects(llm_service):
    """Test that generate_response handles BaseMessage objects correctly."""
    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.content = "Test response"

    # Create a mock LLM
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    # Replace the gpt4o instance
    llm_service.gpt4o = mock_llm

    messages = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi there!"),
        HumanMessage(content="How are you?")
    ]

    response = await llm_service.generate_response(
        messages=messages,
        system_prompt="You are a helpful assistant"
    )

    assert response == "Test response"
    assert mock_llm.ainvoke.called


@pytest.mark.asyncio
async def test_generate_response_with_dict_messages(llm_service):
    """Test that generate_response handles dictionary messages correctly."""
    mock_response = MagicMock()
    mock_response.content = "Test response"

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    llm_service.gpt4o = mock_llm

    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    response = await llm_service.generate_response(
        messages=messages,
        system_prompt="You are a helpful assistant"
    )

    assert response == "Test response"


@pytest.mark.asyncio
async def test_generate_response_with_mixed_messages(llm_service):
    """Test that generate_response handles mixed message types."""
    mock_response = MagicMock()
    mock_response.content = "Test response"

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    llm_service.gpt4o = mock_llm

    messages = [
        HumanMessage(content="Hello"),
        {"role": "assistant", "content": "Hi there!"},
        HumanMessage(content="How are you?")
    ]

    response = await llm_service.generate_response(
        messages=messages,
        system_prompt="You are a helpful assistant"
    )

    assert response == "Test response"


@pytest.mark.asyncio
async def test_generate_response_with_rag_context(llm_service):
    """Test that RAG context is included in the prompt."""
    mock_response = MagicMock()
    mock_response.content = "Test response with context"

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    llm_service.gpt4o = mock_llm

    messages = [HumanMessage(content="What is your product?")]
    rag_context = "Our product is a sales bot."

    response = await llm_service.generate_response(
        messages=messages,
        system_prompt="You are a sales assistant",
        rag_context=rag_context
    )

    assert response == "Test response with context"
    # Verify the system message includes RAG context
    call_args = mock_llm.ainvoke.call_args[0][0]
    assert any("RELEVANT CONTEXT" in msg.content for msg in call_args if isinstance(msg, SystemMessage))


@pytest.mark.asyncio
async def test_generate_response_handles_error_gracefully(llm_service):
    """Test that errors are handled gracefully."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))
    llm_service.gpt4o = mock_llm

    messages = [HumanMessage(content="Hello")]

    response = await llm_service.generate_response(
        messages=messages,
        system_prompt="You are a helpful assistant"
    )

    assert "I apologize" in response
    assert "trouble" in response


@pytest.mark.asyncio
async def test_classify_intent(llm_service):
    """Test intent classification."""
    mock_response = MagicMock()
    mock_response.content = '{"category": "interested", "score": 0.7}'

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    llm_service.gpt4o_mini = mock_llm

    result = await llm_service.classify_intent("I want to buy your product")

    assert result["category"] == "interested"
    assert result["score"] == 0.7


@pytest.mark.asyncio
async def test_analyze_sentiment(llm_service):
    """Test sentiment analysis."""
    mock_response = MagicMock()
    mock_response.content = "positive"

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    llm_service.gpt4o_mini = mock_llm

    sentiment = await llm_service.analyze_sentiment("I love this product!")

    assert sentiment == "positive"


@pytest.mark.asyncio
async def test_extract_data(llm_service):
    """Test data extraction."""
    mock_response = MagicMock()
    mock_response.content = '{"name": "John Doe", "email": "john@example.com", "needs": "CRM software"}'

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    llm_service.gpt4o_mini = mock_llm

    data = await llm_service.extract_data("My name is John Doe and my email is john@example.com")

    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["needs"] == "CRM software"


def test_get_llm_for_task_lightweight(llm_service):
    """Test that lightweight tasks use GPT-4o-mini."""
    llm = llm_service.get_llm_for_task("classification")
    assert llm == llm_service.gpt4o_mini

    llm = llm_service.get_llm_for_task("sentiment")
    assert llm == llm_service.gpt4o_mini

    llm = llm_service.get_llm_for_task("extraction")
    assert llm == llm_service.gpt4o_mini


def test_get_llm_for_task_heavyweight(llm_service):
    """Test that heavyweight tasks use GPT-4o."""
    llm = llm_service.get_llm_for_task("response")
    assert llm == llm_service.gpt4o

    llm = llm_service.get_llm_for_task("conversation")
    assert llm == llm_service.gpt4o

    llm = llm_service.get_llm_for_task("closing")
    assert llm == llm_service.gpt4o
