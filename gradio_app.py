"""Standalone Gradio app that works independently."""

import os
from dotenv import load_dotenv
import gradio as gr
import asyncio

from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from graph.workflow import process_message
from services.llm_service import LLMService
from services.tts_service import TTSService
from services.rag_service import RAGService
from services.config_manager import ConfigManager
from utils.logging_config import setup_logging, get_logger

# Load environment
load_dotenv()

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sales_bot.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Initialize services
logger.info("Initializing services...")

async def init_services():
    """Initialize all services."""
    global llm_service, tts_service, rag_service, config_manager

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Services
    llm_service = LLMService()
    tts_service = TTSService()
    rag_service = RAGService()
    config_manager = ConfigManager()

    # Load default config
    async with AsyncSessionLocal() as db:
        await config_manager.initialize_defaults(db)

    logger.info("All services initialized")

# Run initialization
asyncio.run(init_services())


async def process_chat(message: str, history: list) -> tuple:
    """Process chat message (async version)."""
    print(f"\n{'='*60}")
    print(f"MESSAGE: '{message}'")
    print(f"{'='*60}")

    if not message.strip():
        return history, ""

    try:
        # Load config
        async with AsyncSessionLocal() as db:
            config = await config_manager.load_all_configs(db)

        # Convert history
        messages = []
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        print(f"Processing with {len(messages)} history messages")
        print(f"Config keys: {list(config.keys())}")

        # Process through graph
        result = await process_message(
            user_phone="+1234567890",
            message=message,
            conversation_history=messages,
            config=config,
        )

        bot_response = result.get("current_response", "No response generated")
        print(f"BOT: {bot_response[:100]}...")
        print(f"{'='*60}\n")

        # Update history
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": bot_response}
        ]

        return new_history, ""

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

        error_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"Error: {str(e)}"}
        ]
        return error_history, ""


# Import panels
from gradio_ui.config_panel_v2 import ConfigPanelComponentV2
from gradio_ui.live_chats_panel import LiveChatsPanel

# Create Gradio interface
with gr.Blocks(title="WhatsApp Sales Bot", theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div style="text-align: center; padding: 2em;">
        <h1 style="color: #25D366; margin: 0;">WhatsApp Sales Bot - Panel de Control</h1>
        <p style="color: #666; margin-top: 0.5em;">Gestiona conversaciones, configura y prueba tu bot de ventas</p>
    </div>
    """)

    with gr.Tabs():
        # 1. Chats Tab - Conversaciones en tiempo real
        with gr.Tab("💬 Chats"):
            live_chats = LiveChatsPanel(AsyncSessionLocal)
            live_chats.create_component()

        # 2. Configuration Tab
        with gr.Tab("⚙️ Configuracion"):
            config_panel = ConfigPanelComponentV2(AsyncSessionLocal)
            config_panel.create_component()

        # 3. Pruebas Tab - Testing local
        with gr.Tab("🧪 Pruebas"):
            with gr.Row():
                # Columna izquierda: Datos del usuario simulado
                with gr.Column(scale=1):
                    gr.Markdown("## 👤 Datos del Usuario de Prueba")
                    gr.Markdown("*Los datos se recolectan automáticamente durante la conversación*")

                    user_data_display = gr.Markdown(
                        value="""
### 📊 Datos Recolectados

*Aún no hay datos. Inicia una conversación para ver cómo se recolecta información.*
                        """,
                        label="Datos del Usuario",
                    )

                # Columna derecha: Chat de prueba
                with gr.Column(scale=2):
                    gr.Markdown("## 💬 Conversacion de Prueba")

                    chatbot = gr.Chatbot(
                        label="Chat",
                        height=500,
                    )

                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Escribe tu mensaje...",
                            show_label=False,
                            scale=4,
                        )
                        send = gr.Button("Enviar", variant="primary", scale=1)

                    clear = gr.Button("Limpiar Chat", size="sm")

            # Estado interno para datos del usuario
            test_user_data = {
                "telefono": "+1234567890",
                "nombre": "",
                "email": "",
                "intent": "",
                "sentiment": "",
                "productos": [],
                "mensajes_count": 0
            }

            # Funcion para actualizar datos del usuario
            async def process_chat_with_data(message: str, history: list, current_md: str) -> tuple:
                """Procesar chat y actualizar datos del usuario."""
                # Procesar mensaje normalmente
                new_history, empty_str = await process_chat(message, history)

                # Actualizar datos simulados
                test_user_data["mensajes_count"] += 1

                # Detectar intent basico (simplificado)
                message_lower = message.lower()
                if any(word in message_lower for word in ["comprar", "precio", "costo", "pagar", "cuanto"]):
                    test_user_data["intent"] = "compra 🛒"
                elif any(word in message_lower for word in ["info", "informacion", "que es", "como funciona"]):
                    test_user_data["intent"] = "información ℹ️"
                elif any(word in message_lower for word in ["ayuda", "problema", "error", "soporte"]):
                    test_user_data["intent"] = "soporte 🆘"
                else:
                    test_user_data["intent"] = "conversación 💬"

                # Detectar sentiment basico
                if any(word in message_lower for word in ["excelente", "genial", "perfecto", "gracias"]):
                    test_user_data["sentiment"] = "positivo 😊"
                elif any(word in message_lower for word in ["mal", "error", "problema", "no funciona"]):
                    test_user_data["sentiment"] = "negativo 😞"
                else:
                    test_user_data["sentiment"] = "neutral 😐"

                # Extraer nombre si se menciona
                if "me llamo" in message_lower or "mi nombre es" in message_lower:
                    words = message.split()
                    for i, word in enumerate(words):
                        if word.lower() in ["llamo", "nombre"] and i + 1 < len(words):
                            test_user_data["nombre"] = words[i + 1].strip(".,!?")

                # Extraer email si se menciona
                import re
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
                if email_match:
                    test_user_data["email"] = email_match.group()

                # Formatear datos como Markdown
                data_md = f"""
### 📊 Datos Recolectados

📱 **Teléfono:** {test_user_data["telefono"]}
👤 **Nombre:** {test_user_data["nombre"] or "*No proporcionado*"}
📧 **Email:** {test_user_data["email"] or "*No proporcionado*"}

🎯 **Intención:** {test_user_data["intent"] or "*Detectando...*"}
😊 **Sentimiento:** {test_user_data["sentiment"] or "*Analizando...*"}

💬 **Mensajes enviados:** {test_user_data["mensajes_count"]}
"""

                return new_history, "", data_md

            def reset_test_chat():
                """Resetear chat de prueba y datos del usuario."""
                test_user_data["nombre"] = ""
                test_user_data["email"] = ""
                test_user_data["intent"] = ""
                test_user_data["sentiment"] = ""
                test_user_data["productos"] = []
                test_user_data["mensajes_count"] = 0

                empty_md = """
### 📊 Datos Recolectados

*Aún no hay datos. Inicia una conversación para ver cómo se recolecta información.*
                """
                return [], empty_md

            # Connect events
            msg.submit(process_chat_with_data, [msg, chatbot, user_data_display], [chatbot, msg, user_data_display])
            send.click(process_chat_with_data, [msg, chatbot, user_data_display], [chatbot, msg, user_data_display])
            clear.click(reset_test_chat, None, [chatbot, user_data_display])

    gr.Markdown("""
    ---
    <div style="text-align: center; color: #999;">
        <p>WhatsApp Sales Bot | Powered by LangGraph + OpenAI + Gradio</p>
    </div>
    """)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting WhatsApp Sales Bot - Gradio UI")
    print("="*60)
    print(f"URL: http://localhost:7860")
    print("="*60 + "\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
