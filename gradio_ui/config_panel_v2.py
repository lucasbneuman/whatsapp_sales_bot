"""Panel de configuración mejorado con pestañas para Chatbot, Producto/Servicio y Documentos RAG."""

import gradio as gr
from pathlib import Path
import tempfile
from services.config_manager import get_config_manager
from services.rag_service import get_rag_service
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigPanelComponentV2:
    """Componente de configuración con pestañas para Chatbot, Producto y Documentos RAG."""

    def __init__(self, db_session_factory):
        """
        Inicializar panel de configuración.

        Args:
            db_session_factory: Factory para crear sesiones de BD
        """
        self.db_session_factory = db_session_factory
        self.temp_dir = tempfile.mkdtemp()
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
                "system_prompt", "welcome_message", "payment_link", "response_delay_minutes",
                "text_audio_ratio", "use_emojis", "tts_voice",
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

    async def upload_documents(self, files):
        """Subir documentos al RAG."""
        if not files:
            return "⚠️ No se seleccionaron archivos", self.get_rag_stats()

        try:
            rag_service = get_rag_service()

            # Procesar cada archivo
            uploaded_count = 0
            total_chunks = 0

            for file in files:
                try:
                    # El archivo ya está en una ubicación temporal
                    file_path = file.name
                    chunks = await rag_service.upload_document(file_path)
                    total_chunks += chunks
                    uploaded_count += 1
                    logger.info(f"Uploaded {file_path}: {chunks} chunks")
                except Exception as e:
                    logger.error(f"Error uploading {file.name}: {e}")
                    continue

            if uploaded_count > 0:
                return f"✅ {uploaded_count} archivo(s) subido(s) correctamente ({total_chunks} fragmentos)", self.get_rag_stats()
            else:
                return "❌ No se pudo subir ningún archivo", self.get_rag_stats()

        except Exception as e:
            logger.error(f"Error in upload_documents: {e}")
            return f"❌ Error: {str(e)}", self.get_rag_stats()

    def get_rag_stats(self):
        """Obtener estadísticas del RAG."""
        try:
            rag_service = get_rag_service()
            stats = rag_service.get_collection_stats()
            return f"📊 Fragmentos en base de datos: {stats['total_chunks']}"
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return "📊 Fragmentos en base de datos: 0"

    async def preview_voice(self, voice_name: str):
        """Preview TTS voice."""
        try:
            from services.tts_service import get_tts_service
            tts_service = get_tts_service()

            # Sample text for preview
            preview_text = "Hola, soy tu asistente virtual. Esta es una muestra de mi voz."

            # Generate audio
            audio_bytes = await tts_service.generate_audio(preview_text, voice=voice_name)

            # Save temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            logger.info(f"Generated voice preview for {voice_name}")
            return tmp_path

        except Exception as e:
            logger.error(f"Error generating voice preview: {e}")
            return None

    async def clear_rag_collection(self):
        """Limpiar todos los documentos del RAG."""
        try:
            rag_service = get_rag_service()
            rag_service.clear_collection()
            logger.info("RAG collection cleared")
            return "✅ Base de conocimientos limpiada exitosamente", self.get_rag_stats()
        except Exception as e:
            logger.error(f"Error clearing RAG collection: {e}")
            return f"❌ Error: {str(e)}", self.get_rag_stats()

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

                    welcome_message = gr.Textbox(
                        label="Mensaje de Bienvenida",
                        placeholder="¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?",
                        lines=2,
                        info="Primer mensaje que verá el usuario al iniciar la conversación"
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
                            minimum=5,
                            maximum=500,
                            step=5,
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

                    gr.Markdown("#### Audio/TTS")

                    text_audio_ratio = gr.Slider(
                        label="Ratio Texto/Audio (%)",
                        info="0% = solo texto, 100% = solo audio",
                        minimum=0,
                        maximum=100,
                        step=10,
                        value=0
                    )

                    with gr.Row():
                        tts_voice = gr.Radio(
                            label="Voz TTS",
                            choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                            value="nova",
                            info="Selecciona la voz para mensajes de audio"
                        )
                        with gr.Column():
                            gr.Markdown("**Preview:**")
                            preview_voice_btn = gr.Button("🔊 Escuchar Voz", variant="secondary", size="sm")
                            voice_preview_audio = gr.Audio(label="", visible=True, autoplay=True)

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

                # Tab 3: Documentos RAG
                with gr.Tab("📚 Base de Conocimientos"):
                    gr.Markdown("### Documentos para el Chatbot")
                    gr.Markdown("*Sube archivos con información sobre tu producto/servicio. El chatbot usará esta información para responder preguntas específicas.*")

                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("**Formatos soportados:** TXT, PDF, DOC, DOCX")

                            file_upload = gr.File(
                                label="Subir Documentos",
                                file_count="multiple",
                                file_types=[".txt", ".pdf", ".doc", ".docx"],
                                type="filepath"
                            )

                            upload_btn = gr.Button("📤 Subir Archivos", variant="primary")

                        with gr.Column(scale=1):
                            gr.Markdown("### ℹ️ Información")
                            gr.Markdown("""
                            **¿Qué puedes subir?**
                            - Catálogos de productos
                            - Manuales de usuario
                            - FAQs
                            - Guías de precios
                            - Políticas y términos

                            **¿Cómo funciona?**
                            1. Sube tus documentos
                            2. Activa RAG en Chatbot
                            3. El bot usará automáticamente esta información
                            """)

                    rag_stats = gr.Textbox(
                        label="Estado",
                        value=self.get_rag_stats(),
                        interactive=False
                    )

                    upload_status = gr.Textbox(
                        label="Resultado de Carga",
                        interactive=False,
                        visible=False
                    )

                    gr.Markdown("---")
                    gr.Markdown("### ⚠️ Zona de Peligro")

                    with gr.Row():
                        clear_btn = gr.Button("🗑️ Limpiar Base de Conocimientos", variant="stop", size="sm")
                        clear_status = gr.Textbox(
                            label="",
                            interactive=False,
                            show_label=False,
                            visible=False
                        )

                    # Conectar eventos RAG
                    upload_btn.click(
                        self.upload_documents,
                        inputs=[file_upload],
                        outputs=[upload_status, rag_stats]
                    ).then(
                        lambda: gr.update(visible=True),
                        outputs=[upload_status]
                    )

                    clear_btn.click(
                        self.clear_rag_collection,
                        outputs=[clear_status, rag_stats]
                    ).then(
                        lambda: gr.update(visible=True),
                        outputs=[clear_status]
                    )

            # Botón de guardar
            save_btn = gr.Button("💾 Guardar Configuración", variant="primary", size="lg")
            status_msg = gr.Textbox(label="Estado", interactive=False)

            # Conectar evento de guardar
            save_btn.click(
                self.save_all_configs,
                inputs=[
                    # Chatbot config
                    system_prompt, welcome_message, payment_link, response_delay,
                    text_audio_ratio, use_emojis, tts_voice,
                    multi_part, max_words,
                    # Product config
                    product_name, product_description, product_features,
                    product_benefits, product_price, product_target_audience
                ],
                outputs=status_msg
            )

            # Conectar evento de preview de voz
            preview_voice_btn.click(
                self.preview_voice,
                inputs=[tts_voice],
                outputs=voice_preview_audio
            )

        return col
