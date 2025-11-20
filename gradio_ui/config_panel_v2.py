"""Panel de configuración mejorado con pestañas para Chatbot y Producto/Servicio."""

import gradio as gr
from services.config_manager import get_config_manager
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigPanelComponentV2:
    """Componente de configuración con pestañas para Chatbot y Producto."""

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
                # Chatbot config
                "system_prompt", "payment_link", "response_delay_minutes",
                "text_audio_ratio", "use_emojis", "tts_voice", "rag_enabled",
                "multi_part_messages", "max_words_per_response",
                # Producto/Servicio config
                "product_name", "product_description", "product_features",
                "product_benefits", "product_price", "product_target_audience"
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
        """Crear componente UI con pestañas para Chatbot y Producto."""

        with gr.Column() as col:
            gr.Markdown("## ⚙️ Configuración")
            gr.Markdown("*Configura tu chatbot y describe tu producto/servicio*")

            with gr.Tabs():
                # Tab 1: Configuración del Chatbot
                with gr.Tab("🤖 Chatbot"):
                    gr.Markdown("### Configuración del Chatbot")

                    system_prompt = gr.Textbox(
                        label="System Prompt",
                        placeholder="Eres un asistente de ventas profesional...",
                        lines=4,
                        info="Personalidad y comportamiento base del chatbot"
                    )

                    payment_link = gr.Textbox(
                        label="Link de Pago",
                        placeholder="https://tu-sitio.com/pagar",
                        info="URL donde los clientes pueden realizar el pago"
                    )

                    gr.Markdown("#### Comportamiento")

                    with gr.Row():
                        response_delay = gr.Number(
                            label="Delay de Respuesta (minutos)",
                            value=0.5,
                            minimum=0,
                            maximum=10,
                            step=0.1,
                            info="Tiempo de espera antes de responder"
                        )

                        max_words = gr.Slider(
                            label="Máximo de Palabras por Respuesta",
                            minimum=20,
                            maximum=300,
                            step=10,
                            value=100,
                            info="Límite de palabras en cada mensaje"
                        )

                    with gr.Row():
                        use_emojis = gr.Checkbox(
                            label="Usar Emojis",
                            value=True,
                            info="Incluir emojis en las respuestas"
                        )

                        multi_part = gr.Checkbox(
                            label="Mensajes en Múltiples Partes",
                            value=False,
                            info="Dividir respuestas largas"
                        )

                        rag_enabled = gr.Checkbox(
                            label="Habilitar RAG",
                            value=False,
                            info="Usar base de conocimientos"
                        )

                    gr.Markdown("#### Audio/TTS")

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
                        value="nova",
                        info="Voz para mensajes de audio"
                    )

                # Tab 2: Producto/Servicio
                with gr.Tab("📦 Producto/Servicio"):
                    gr.Markdown("### Información de tu Producto/Servicio")
                    gr.Markdown("*Esta información se usará para adaptar las respuestas del chatbot*")

                    product_name = gr.Textbox(
                        label="Nombre del Producto/Servicio",
                        placeholder="Ej: Curso de Marketing Digital",
                        info="¿Qué vendes?"
                    )

                    product_description = gr.Textbox(
                        label="Descripción",
                        placeholder="Curso completo de marketing digital con más de 50 horas de contenido...",
                        lines=4,
                        info="Descripción general de lo que ofreces"
                    )

                    product_features = gr.Textbox(
                        label="Características Principales",
                        placeholder="- 50+ horas de video\n- Certificado al finalizar\n- Acceso de por vida\n- Soporte 24/7",
                        lines=5,
                        info="Lista las características clave (una por línea)"
                    )

                    product_benefits = gr.Textbox(
                        label="Beneficios para el Cliente",
                        placeholder="- Aprenderás a crear campañas efectivas\n- Aumentarás tus ventas online\n- Dominarás las redes sociales",
                        lines=5,
                        info="¿Qué gana el cliente? (una por línea)"
                    )

                    with gr.Row():
                        product_price = gr.Textbox(
                            label="Precio",
                            placeholder="Ej: $99 USD, Desde $50, Consultar",
                            info="Precio o rango de precio (opcional)"
                        )

                        product_target_audience = gr.Textbox(
                            label="Público Objetivo",
                            placeholder="Ej: Emprendedores, Pequeños negocios",
                            info="¿A quién está dirigido?"
                        )

            # Botón de guardar
            save_btn = gr.Button("💾 Guardar Configuración", variant="primary", size="lg")
            status_msg = gr.Textbox(label="Estado", interactive=False)

            # Conectar evento de guardar
            save_btn.click(
                self.save_all_configs,
                inputs=[
                    # Chatbot config
                    system_prompt, payment_link, response_delay,
                    text_audio_ratio, use_emojis, tts_voice, rag_enabled,
                    multi_part, max_words,
                    # Product config
                    product_name, product_description, product_features,
                    product_benefits, product_price, product_target_audience
                ],
                outputs=status_msg
            )

        return col
