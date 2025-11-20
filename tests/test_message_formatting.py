"""Tests for message formatting and conversion."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage


class TestMessageFormatting:
    """Test suite for message formatting."""

    def test_human_message_has_content(self):
        """Test that HumanMessage has content attribute."""
        msg = HumanMessage(content="Hello")
        assert hasattr(msg, 'content')
        assert msg.content == "Hello"

    def test_ai_message_has_content(self):
        """Test that AIMessage has content attribute."""
        msg = AIMessage(content="Hi there")
        assert hasattr(msg, 'content')
        assert msg.content == "Hi there"

    def test_system_message_has_content(self):
        """Test that SystemMessage has content attribute."""
        msg = SystemMessage(content="You are a helpful assistant")
        assert hasattr(msg, 'content')
        assert msg.content == "You are a helpful assistant"

    def test_messages_are_basemessage_instances(self):
        """Test that all message types are BaseMessage instances."""
        human_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi")
        system_msg = SystemMessage(content="System")

        assert isinstance(human_msg, BaseMessage)
        assert isinstance(ai_msg, BaseMessage)
        assert isinstance(system_msg, BaseMessage)

    def test_message_content_is_string(self):
        """Test that message content is properly converted to string."""
        # Test with various input types
        msg1 = HumanMessage(content=str(123))
        msg2 = HumanMessage(content=str(None))
        msg3 = HumanMessage(content=str("test"))

        assert isinstance(msg1.content, str)
        assert isinstance(msg2.content, str)
        assert isinstance(msg3.content, str)

    def test_conversation_history_format(self):
        """Test that conversation history is properly formatted."""
        conversation_history = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="How are you?"),
            AIMessage(content="I'm doing well, thanks!")
        ]

        # All should be BaseMessage instances
        assert all(isinstance(msg, BaseMessage) for msg in conversation_history)

        # All should have content
        assert all(hasattr(msg, 'content') for msg in conversation_history)

        # Content should be strings
        assert all(isinstance(msg.content, str) for msg in conversation_history)

    def test_dict_to_message_conversion(self):
        """Test conversion of dict messages to BaseMessage objects."""
        dict_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "system", "content": "You are helpful"}
        ]

        converted = []
        for msg in dict_messages:
            if msg["role"] == "user":
                converted.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                converted.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                converted.append(SystemMessage(content=msg["content"]))

        assert len(converted) == 3
        assert isinstance(converted[0], HumanMessage)
        assert isinstance(converted[1], AIMessage)
        assert isinstance(converted[2], SystemMessage)

    def test_empty_content_handling(self):
        """Test that empty content is handled properly."""
        msg = HumanMessage(content="")
        assert msg.content == ""
        assert isinstance(msg.content, str)

    def test_none_content_conversion(self):
        """Test that None content is converted to string."""
        # LangChain messages should not accept None, but we test the string conversion
        msg = HumanMessage(content=str(None))
        assert msg.content == "None"
        assert isinstance(msg.content, str)

    def test_message_list_concatenation(self):
        """Test that message lists can be concatenated."""
        history = [HumanMessage(content="Hello")]
        new_msg = [HumanMessage(content="World")]

        combined = history + new_msg

        assert len(combined) == 2
        assert all(isinstance(msg, BaseMessage) for msg in combined)
