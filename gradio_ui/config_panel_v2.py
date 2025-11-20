"""Panel de configuración mejorado con sub-pestañas para prompts."""

import gradio as gr
from services.config_manager import get_config_manager
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigPanelComponentV2:
    """Componente de configuración con sub-pestañas."""

    def __init__(self, db_session_factory):
        """
        Inicializar panel de configuración.

        Args:
            db_session_factory: Factory para crear sesiones de BD
        """
        self.db_session_factory = db_session_factory
        logger.info("Config panel V2 initialized")

    async def load_all_configs(self):
        """Cargar todas las configuraciones."""
        try:
            config_manager = get_config_manager()
            async with self.db_session_factory() as db:
                configs = await config_manager.load_all_configs(db)
                return configs
        except Exception as e:
            logger.error(f"Error loading configs: {e}")
            return {}

    async def save_all_configs(self, *args):
        """Guardar todas las configuraciones."""
        try:
            config_manager = get_config_manager()

            # Mapear args a config keys
            config_keys = [
                "system_prompt", "payment_link", "response_delay_minutes",
                "text_audio_ratio", "use_emojis", "tts_voice", "rag_enabled",
                "multi_part_messages", "max_words_per_response",
                "welcome_prompt", "intent_prompt", "sentiment_prompt",
                "data_extraction_prompt", "closing_prompt"
            ]

            configs = dict(zip(config_keys, args))

            async with self.db_session_factory() as db:
                await config_manager.save_all_configs(db, configs)

            logger.info("All configs saved successfully")
            return "✅ Configuración guardada exitosamente"

        except Exception as e:
            logger.error(f"Error saving configs: {e}")
            return f"❌ Error: {str(e)}"

    def create_component(self):
        """Crear componente UI con sub-pestañas."""

        with gr.Column() as col:
            gr.Markdown("## ⚙️ Configuración del Bot")
            gr.Markdown("*Los valores se cargarán de la base de datos al abrir cada campo*")

            with gr.Tabs():
                # Tab 1: Configuración General
                with gr.Tab("General"):
                    gr.Markdown("### Configuración General")

                    system_prompt = gr.Textbox(
                        label="System Prompt",
                        placeholder="Eres un asistente de ventas...",
                        lines=4,
                    )

                    payment_link = gr.Textbox(
                        label="Link de Pago",
                        placeholder="https://example.com/pay",
                    )

                    with gr.Row():
                        response_delay = gr.Number(
                            label="Delay de Respuesta (minutos)",
                            value=0.5,
                            minimum=0,
                            maximum=10,
                            step=0.1
                        )

                        max_words = gr.Slider(
                            label="Máximo de Palabras por Respuesta",
                            minimum=20,
                            maximum=300,
                            step=10,
                            value=100
                        )

                    with gr.Row():
                        use_emojis = gr.Checkbox(
                            label="Usar Emojis",
                            value=True
                        )

                        multi_part = gr.Checkbox(
                            label="Mensajes en Múltiples Partes",
                            value=False
                        )

                        rag_enabled = gr.Checkbox(
                            label="Habilitar RAG",
                            value=False
                        )

                # Tab 2: Audio/TTS
                with gr.Tab("Audio/TTS"):
                    gr.Markdown("### Configuración de Audio")

                    text_audio_ratio = gr.Slider(
                        label="Ratio Texto/Audio (%)",
                        info="0% = solo texto, 100% = solo audio",
                        minimum=0,
                        maximum=100,
                        step=10,
                        value=0
                    )

                    tts_voice = gr.Dropdown(
                        label="Voz TTS",
                        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                        value="nova"
                    )

                # Tab 3: Prompts Editables
                with gr.Tab("Prompts"):
                    gr.Markdown("### Editar Prompts del Sistema")

                    welcome_prompt = gr.Textbox(
                        label="Prompt de Bienvenida",
                        lines=3,
                    )

                    intent_prompt = gr.Textbox(
                        label="Prompt de Clasificación de Intent",
                        lines=3,
                    )

                    sentiment_prompt = gr.Textbox(
                        label="Prompt de Análisis de Sentimiento",
                        lines=2,
                    )

                    data_extraction_prompt = gr.Textbox(
                        label="Prompt de Extracción de Datos",
                        lines=3,
                    )

                    closing_prompt = gr.Textbox(
                        label="Prompt de Cierre",
                        lines=3,
                    )

            # Botón de guardar
            save_btn = gr.Button("💾 Guardar Configuración", variant="primary", size="lg")
            status_msg = gr.Textbox(label="Estado", interactive=False)

            # Conectar evento de guardar
            save_btn.click(
                self.save_all_configs,
                inputs=[
                    system_prompt, payment_link, response_delay,
                    text_audio_ratio, use_emojis, tts_voice, rag_enabled,
                    multi_part, max_words,
                    welcome_prompt, intent_prompt, sentiment_prompt,
                    data_extraction_prompt, closing_prompt
                ],
                outputs=status_msg
            )

        return col
