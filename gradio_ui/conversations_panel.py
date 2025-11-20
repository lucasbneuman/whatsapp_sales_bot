"""Active conversations panel for Gradio UI."""

from typing import List, Tuple

import gradio as gr

from database import crud
from services.twilio_service import get_twilio_service
from utils.helpers import format_timestamp
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConversationsPanelComponent:
    """Component for managing active conversations and manual handoff."""

    def __init__(self, db_session_factory):
        """
        Initialize conversations panel.

        Args:
            db_session_factory: Factory function to create DB sessions
        """
        self.db_session_factory = db_session_factory
        self.selected_user_id = None
        logger.info("Conversations panel component initialized")

    async def get_active_conversations(self) -> List[List[str]]:
        """
        Get list of active conversations.

        Returns:
            List of conversation rows [phone, mode, last_message, time]
        """
        try:
            async with self.db_session_factory() as db:
                users = await crud.get_all_active_users(db, limit=50)

                if not users:
                    return []

                # Format for table display
                rows = []
                for user in users:
                    # Format mode with emoji
                    mode = user.conversation_mode
                    if mode == "AUTO":
                        mode_display = "🟢 AUTO"
                    elif mode == "MANUAL":
                        mode_display = "🔴 MANUAL"
                    elif mode == "NEEDS_ATTENTION":
                        mode_display = "⚠️ ATTENTION"
                    else:
                        mode_display = mode

                    # Get last message
                    messages = await crud.get_recent_messages(db, user.id, count=1)
                    last_msg = messages[0].message_text[:50] + "..." if messages else "No messages"

                    # Format time
                    time_str = format_timestamp(user.last_message_at) if user.last_message_at else "N/A"

                    rows.append([
                        str(user.id),
                        user.phone,
                        user.name or "Unknown",
                        mode_display,
                        last_msg,
                        time_str,
                    ])

                return rows

        except Exception as e:
            logger.error(f"Error getting active conversations: {e}")
            return []

    async def take_control(self, selected_index: int, dataframe_data: List[List[str]]) -> Tuple[str, str]:
        """
        Take manual control of a conversation.

        Args:
            selected_index: Selected row index
            dataframe_data: Current dataframe data

        Returns:
            Tuple of (status_message, user_phone)
        """
        try:
            if selected_index is None or selected_index < 0:
                return "Please select a conversation first", ""

            if not dataframe_data or selected_index >= len(dataframe_data):
                return "Invalid selection", ""

            user_id = int(dataframe_data[selected_index][0])
            user_phone = dataframe_data[selected_index][1]

            # Update conversation mode to MANUAL
            async with self.db_session_factory() as db:
                user = await crud.update_user(db, user_id, conversation_mode="MANUAL")

                if user:
                    self.selected_user_id = user_id
                    logger.info(f"Took manual control of conversation: {user_phone}")
                    return f"✅ You now have control of {user_phone}", user_phone
                else:
                    return "❌ Failed to update conversation mode", ""

        except Exception as e:
            logger.error(f"Error taking control: {e}")
            return f"❌ Error: {str(e)}", ""

    async def return_to_bot(self, dataframe_data: List[List[str]], selected_index: int) -> str:
        """
        Return conversation to bot (AUTO mode).

        Args:
            dataframe_data: Current dataframe data
            selected_index: Selected row index

        Returns:
            Status message
        """
        try:
            if selected_index is None or selected_index < 0:
                return "Please select a conversation first"

            if not dataframe_data or selected_index >= len(dataframe_data):
                return "Invalid selection"

            user_id = int(dataframe_data[selected_index][0])
            user_phone = dataframe_data[selected_index][1]

            # Update conversation mode to AUTO
            async with self.db_session_factory() as db:
                user = await crud.update_user(db, user_id, conversation_mode="AUTO")

                if user:
                    self.selected_user_id = None
                    logger.info(f"Returned conversation to bot: {user_phone}")
                    return f"✅ {user_phone} is now in AUTO mode"
                else:
                    return "❌ Failed to update conversation mode"

        except Exception as e:
            logger.error(f"Error returning to bot: {e}")
            return f"❌ Error: {str(e)}"

    async def send_manual_message(self, message: str, phone: str) -> str:
        """
        Send a manual message via WhatsApp.

        Args:
            message: Message text
            phone: Recipient phone number

        Returns:
            Status message
        """
        if not message.strip():
            return "Please enter a message"

        if not phone:
            return "Please select a conversation first"

        try:
            twilio_service = get_twilio_service()
            result = twilio_service.send_message(phone, message)

            # Save message to database
            async with self.db_session_factory() as db:
                user = await crud.get_user_by_phone(db, phone)
                if user:
                    await crud.create_message(
                        db,
                        user_id=user.id,
                        message_text=message,
                        sender="bot",
                        metadata={"manual": True},
                    )

            logger.info(f"Manual message sent to {phone}")
            return f"✅ Message sent successfully (SID: {result['sid']})"

        except Exception as e:
            logger.error(f"Error sending manual message: {e}")
            return f"❌ Error: {str(e)}"

    def create_component(self) -> gr.Column:
        """
        Create the conversations panel UI component.

        Returns:
            Gradio Column with conversations panel
        """
        with gr.Column() as col:
            gr.Markdown("## 👥 Active Conversations")

            # Conversations table
            conversations_df = gr.Dataframe(
                headers=["ID", "Phone", "Name", "Mode", "Last Message", "Time"],
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Active Conversations",
                interactive=False,
                wrap=True,
                every=3,  # Auto-refresh every 3 seconds
            )

            # Populate initial data
            conversations_df.value = self.get_active_conversations

            # Control buttons
            with gr.Row():
                take_control_btn = gr.Button("🎮 Take Control", variant="primary")
                return_bot_btn = gr.Button("🤖 Return to Bot", variant="secondary")

            status_box = gr.Textbox(label="Status", interactive=False)

            # Manual messaging section
            gr.Markdown("### 💬 Manual Messaging")
            selected_phone = gr.Textbox(
                label="Selected Phone",
                interactive=False,
                placeholder="Select a conversation first",
            )

            with gr.Row():
                manual_msg_input = gr.Textbox(
                    placeholder="Type your manual message...",
                    show_label=False,
                    scale=4,
                )
                send_manual_btn = gr.Button("Send", scale=1, variant="primary")

            send_status = gr.Textbox(label="Send Status", interactive=False)

            # Event handlers
            selected_index = gr.State(value=-1)

            # Update selected index when row is clicked
            def on_select(evt: gr.SelectData):
                return evt.index[0]

            conversations_df.select(on_select, None, selected_index)

            # Take control handler
            async def handle_take_control(idx, data):
                status, phone = await self.take_control(idx, data)
                return status, phone

            take_control_btn.click(
                handle_take_control,
                [selected_index, conversations_df],
                [status_box, selected_phone],
            )

            # Return to bot handler
            return_bot_btn.click(
                self.return_to_bot,
                [conversations_df, selected_index],
                status_box,
            )

            # Send manual message handler
            send_manual_btn.click(
                self.send_manual_message,
                [manual_msg_input, selected_phone],
                send_status,
            )

        return col
