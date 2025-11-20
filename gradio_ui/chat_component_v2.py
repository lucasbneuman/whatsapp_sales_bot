"""Simplified Chat component that works with Gradio + FastAPI."""

from typing import List, Dict
import gradio as gr
import asyncio
from langchain_core.messages import AIMessage, HumanMessage

from graph.workflow import process_message
from services.config_manager import get_config_manager
from utils.logging_config import get_logger

logger = get_logger(__name__)


def create_chat_component(db_session_factory):
    """
    Create a working chat component.

    Args:
        db_session_factory: Database session factory

    Returns:
        Gradio Column with chat interface
    """
    logger.info("Creating simplified chat component")

    def process_chat_message(message: str, history: List[Dict]) -> tuple:
        """Process chat message synchronously."""
        logger.info(f"=" * 60)
        logger.info(f"CHAT MESSAGE RECEIVED: '{message}'")
        logger.info(f"=" * 60)

        if not message.strip():
            logger.warning("Empty message, ignoring")
            return history, ""

        try:
            # Run async code in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Get config
                config_manager = get_config_manager()

                async def async_process():
                    """Async processing function."""
                    # Load config
                    async with db_session_factory() as db:
                        config = await config_manager.load_all_configs(db)

                    logger.info(f"Config loaded: {list(config.keys())}")

                    # Convert history to LangChain messages
                    messages = []
                    for msg in history:
                        if msg.get("role") == "user":
                            messages.append(HumanMessage(content=msg["content"]))
                        elif msg.get("role") == "assistant":
                            messages.append(AIMessage(content=msg["content"]))

                    logger.info(f"Processing {len(messages)} history messages")

                    # Process through graph
                    result = await process_message(
                        user_phone="+1234567890",
                        message=message,
                        conversation_history=messages,
                        config=config,
                    )

                    bot_response = result.get("current_response", "Sorry, no response generated.")
                    logger.info(f"Bot response: {bot_response[:100]}...")

                    return bot_response

                # Run the async function
                bot_response = loop.run_until_complete(async_process())

                # Update history
                new_history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": bot_response}
                ]

                logger.info("Message processed successfully!")
                logger.info("=" * 60)

                return new_history, ""

            finally:
                loop.close()

        except Exception as e:
            logger.error(f"ERROR: {e}", exc_info=True)
            error_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"Error: {str(e)}"}
            ]
            return error_history, ""

    # Create UI
    with gr.Column(scale=1) as col:
        gr.Markdown("## 💬 Chat Testing")
        gr.Markdown("Test your bot conversations (simulates WhatsApp)")

        chatbot = gr.Chatbot(
            label="Conversation",
            height=400,
        )

        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Type your message...",
                show_label=False,
                scale=4,
            )
            send_btn = gr.Button("Send", scale=1, variant="primary")

        clear_btn = gr.Button("Clear Chat", size="sm")

        # Connect events
        msg_input.submit(process_chat_message, [msg_input, chatbot], [chatbot, msg_input])
        send_btn.click(process_chat_message, [msg_input, chatbot], [chatbot, msg_input])
        clear_btn.click(lambda: [], None, chatbot)

    logger.info("Chat component created")
    return col
