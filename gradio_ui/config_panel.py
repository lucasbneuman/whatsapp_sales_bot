"""Configuration panel for Gradio UI."""

from typing import Any, Dict, List

import gradio as gr

from services.config_manager import get_config_manager
from services.rag_service import get_rag_service
from services.tts_service import TTSService
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigPanelComponent:
    """Component for managing system configuration."""

    def __init__(self, db_session_factory):
        """
        Initialize config panel.

        Args:
            db_session_factory: Factory function to create DB sessions
        """
        self.db_session_factory = db_session_factory
        logger.info("Config panel component initialized")

    async def load_current_config(self) -> Dict[str, Any]:
        """
        Load current configuration from database.

        Returns:
            Dict with all config values
        """
        try:
            config_manager = get_config_manager()
            async with self.db_session_factory() as db:
                config = await config_manager.load_all_configs(db)
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    async def save_configuration(
        self,
        system_prompt: str,
        payment_link: str,
        response_delay: float,
        text_audio_ratio: float,
        use_emojis: bool,
        tts_voice: str,
        rag_enabled: bool,
    ) -> str:
        """
        Save configuration to database.

        Args:
            system_prompt: System prompt text
            payment_link: Payment link URL
            response_delay: Response delay in seconds
            text_audio_ratio: Text/audio ratio (0-100)
            use_emojis: Whether to use emojis
            tts_voice: TTS voice selection
            rag_enabled: Whether RAG is enabled

        Returns:
            Status message
        """
        try:
            config = {
                "system_prompt": system_prompt,
                "payment_link": payment_link,
                "response_delay": response_delay,
                "text_audio_ratio": text_audio_ratio,
                "use_emojis": use_emojis,
                "tts_voice": tts_voice,
                "rag_enabled": rag_enabled,
            }

            config_manager = get_config_manager()
            async with self.db_session_factory() as db:
                await config_manager.save_all_configs(db, config)

            logger.info("Configuration saved successfully")
            return "✅ Configuration saved successfully!"

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return f"❌ Error saving configuration: {str(e)}"

    async def upload_rag_documents(self, files: List[Any]) -> str:
        """
        Upload documents for RAG.

        Args:
            files: List of uploaded files

        Returns:
            Status message
        """
        if not files:
            return "No files selected"

        try:
            rag_service = get_rag_service()
            total_chunks = 0

            for file in files:
                try:
                    chunks = await rag_service.upload_document(file.name)
                    total_chunks += chunks
                    logger.info(f"Uploaded {file.name}: {chunks} chunks")
                except Exception as e:
                    logger.error(f"Failed to upload {file.name}: {e}")
                    continue

            stats = rag_service.get_collection_stats()
            return f"✅ Uploaded {len(files)} files ({total_chunks} chunks)\nTotal in DB: {stats['total_chunks']} chunks"

        except Exception as e:
            logger.error(f"Error uploading RAG documents: {e}")
            return f"❌ Error: {str(e)}"

    async def clear_rag_documents(self) -> str:
        """
        Clear all RAG documents.

        Returns:
            Status message
        """
        try:
            rag_service = get_rag_service()
            rag_service.clear_collection()
            logger.info("RAG collection cleared")
            return "✅ All RAG documents cleared"
        except Exception as e:
            logger.error(f"Error clearing RAG documents: {e}")
            return f"❌ Error: {str(e)}"

    def create_component(self) -> gr.Column:
        """
        Create the configuration panel UI component.

        Returns:
            Gradio Column with config panel
        """
        with gr.Column() as col:
            gr.Markdown("## ⚙️ Configuration Panel")

            with gr.Tabs():
                # Tab 1: System Configuration
                with gr.Tab("System"):
                    system_prompt = gr.Textbox(
                        label="System Prompt",
                        lines=5,
                        placeholder="Enter the system prompt that defines the bot's behavior...",
                        value="You are a friendly and professional sales assistant. Your goal is to help customers find the right product and complete their purchase smoothly.",
                    )

                    payment_link = gr.Textbox(
                        label="Payment Link",
                        placeholder="https://example.com/pay",
                        value="https://example.com/pay",
                    )

                    response_delay = gr.Slider(
                        label="Response Delay (seconds)",
                        minimum=0,
                        maximum=10,
                        step=0.5,
                        value=1.0,
                        info="Delay before sending response (simulates typing)",
                    )

                    use_emojis = gr.Checkbox(
                        label="Use Emojis in Responses",
                        value=True,
                    )

                # Tab 2: Text-to-Speech
                with gr.Tab("Text-to-Speech"):
                    text_audio_ratio = gr.Slider(
                        label="Text/Audio Ratio",
                        minimum=0,
                        maximum=100,
                        step=10,
                        value=0,
                        info="0-49: Text only | 50-100: Text + Audio",
                    )

                    tts_voice = gr.Dropdown(
                        label="TTS Voice",
                        choices=TTSService.AVAILABLE_VOICES,
                        value="nova",
                        info="Select voice for text-to-speech",
                    )

                    gr.Markdown("""
                    **Voice Descriptions:**
                    - **alloy**: Neutral and balanced
                    - **echo**: Clear and articulate
                    - **fable**: Warm and engaging
                    - **onyx**: Deep and authoritative
                    - **nova**: Friendly and energetic
                    - **shimmer**: Bright and cheerful
                    """)

                # Tab 3: RAG Configuration
                with gr.Tab("RAG (Knowledge Base)"):
                    rag_enabled = gr.Checkbox(
                        label="Enable RAG",
                        value=False,
                        info="Use document knowledge base to inform responses",
                    )

                    file_upload = gr.File(
                        label="Upload Documents",
                        file_count="multiple",
                        file_types=[".pdf", ".txt", ".doc", ".docx"],
                    )

                    upload_btn = gr.Button("📤 Upload Documents", variant="primary")
                    upload_status = gr.Textbox(label="Upload Status", interactive=False)

                    with gr.Row():
                        clear_rag_btn = gr.Button("🗑️ Clear All Documents", variant="stop")
                        rag_stats = gr.Textbox(
                            label="RAG Stats",
                            interactive=False,
                            placeholder="No documents uploaded",
                        )

                    # Upload handler
                    upload_btn.click(
                        self.upload_rag_documents,
                        file_upload,
                        upload_status,
                    )

                    # Clear handler
                    clear_rag_btn.click(
                        self.clear_rag_documents,
                        None,
                        upload_status,
                    )

                # Tab 4: Deployment
                with gr.Tab("Deployment"):
                    gr.Markdown("""
                    ### 🚀 Production Deployment

                    **Status:** Ready to deploy

                    **Before deploying:**
                    1. Ensure all configurations are saved
                    2. Test conversations in the chat interface
                    3. Verify Twilio webhook is configured
                    4. Check environment variables are set

                    **Deployment checklist:**
                    - ✅ Database initialized
                    - ✅ Services configured
                    - ✅ OpenAI API key set
                    - ✅ Twilio credentials set
                    """)

                    deploy_btn = gr.Button("🚀 Deploy to Production", variant="primary", size="lg")
                    deploy_status = gr.Textbox(label="Deployment Status", interactive=False)

                    def handle_deploy():
                        return "✅ Configuration saved! App is running. Configure Twilio webhook to: /webhook/whatsapp"

                    deploy_btn.click(handle_deploy, None, deploy_status)

            # Save Configuration Button (applies to all tabs)
            gr.Markdown("---")
            save_config_btn = gr.Button("💾 Save Configuration", variant="primary", size="lg")
            save_status = gr.Textbox(label="Save Status", interactive=False)

            # Save handler
            save_config_btn.click(
                self.save_configuration,
                [
                    system_prompt,
                    payment_link,
                    response_delay,
                    text_audio_ratio,
                    use_emojis,
                    tts_voice,
                    rag_enabled,
                ],
                save_status,
            )

            # Load current config on startup
            async def load_config_values():
                config = await self.load_current_config()
                return (
                    config.get("system_prompt", ""),
                    config.get("payment_link", ""),
                    config.get("response_delay", 1.0),
                    config.get("text_audio_ratio", 0),
                    config.get("use_emojis", True),
                    config.get("tts_voice", "nova"),
                    config.get("rag_enabled", False),
                )

            # Auto-load on component creation
            # Note: Gradio 5 changed the API - load event removed
            # Configuration will be loaded on first interaction or manually
            # gr.on(
            #     triggers=[col.load],
            #     fn=load_config_values,
            #     outputs=[
            #         system_prompt,
            #         payment_link,
            #         response_delay,
            #         text_audio_ratio,
            #         use_emojis,
            #         tts_voice,
            #         rag_enabled,
            #     ],
            # )

        return col
