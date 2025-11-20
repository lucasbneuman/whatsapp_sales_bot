"""Real-time data viewer component for Gradio UI."""

import gradio as gr

from utils.helpers import calculate_intent_emoji, calculate_sentiment_emoji
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DataViewerComponent:
    """Component for displaying real-time conversation data."""

    def __init__(self, chat_component):
        """
        Initialize data viewer component.

        Args:
            chat_component: Reference to chat component to get state
        """
        self.chat_component = chat_component
        logger.info("Data viewer component initialized")

    def get_current_state(self) -> dict:
        """
        Get current conversation state for display.

        Returns:
            Dict with formatted state data
        """
        try:
            state = self.chat_component.get_last_state()

            if not state:
                return {
                    "status": "No active conversation",
                    "user_name": "N/A",
                    "intent_score": 0.0,
                    "sentiment": "neutral",
                    "stage": "N/A",
                    "collected_data": {},
                    "payment_link_sent": False,
                    "conversation_mode": "N/A",
                }

            # Format for display
            intent_score = state.get("intent_score", 0.0)
            sentiment = state.get("sentiment", "neutral")

            return {
                "status": "Active",
                "user_name": state.get("user_name") or "Not collected",
                "intent_score": f"{intent_score:.2f} {calculate_intent_emoji(intent_score)}",
                "sentiment": f"{sentiment} {calculate_sentiment_emoji(sentiment)}",
                "stage": state.get("stage", "unknown").upper(),
                "collected_data": state.get("collected_data", {}),
                "payment_link_sent": "✅ Yes" if state.get("payment_link_sent") else "❌ No",
                "conversation_mode": state.get("conversation_mode", "AUTO"),
            }

        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return {"error": str(e)}

    def create_component(self) -> gr.Column:
        """
        Create the data viewer UI component.

        Returns:
            Gradio Column with data viewer
        """
        with gr.Column(scale=1) as col:
            gr.Markdown("## 📊 Real-Time Data Viewer")
            gr.Markdown("Live conversation state and metrics")

            # JSON display with auto-refresh
            json_display = gr.JSON(
                value=self.get_current_state,
                label="Current State",
                every=2,  # Refresh every 2 seconds
            )

            # Visual metrics
            with gr.Row():
                intent_gauge = gr.Textbox(
                    label="Intent Score",
                    value="0.00",
                    interactive=False,
                )
                sentiment_box = gr.Textbox(
                    label="Sentiment",
                    value="neutral",
                    interactive=False,
                )

            stage_box = gr.Textbox(
                label="Current Stage",
                value="N/A",
                interactive=False,
            )

            # Update function for metrics
            def update_metrics():
                state = self.get_current_state()
                return (
                    state.get("intent_score", "0.00"),
                    state.get("sentiment", "neutral"),
                    state.get("stage", "N/A"),
                )

            # Auto-refresh metrics
            gr.Timer(
                value=2,  # 2 seconds
                active=True,
            ).tick(
                update_metrics,
                None,
                [intent_gauge, sentiment_box, stage_box],
            )

        return col
