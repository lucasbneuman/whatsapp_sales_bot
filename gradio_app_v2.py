"""Aplicación Gradio mejorada con todas las funcionalidades."""

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
                # Columna izquierda: Datos del usuario simulado (COMPACTA)
                with gr.Column(scale=1):
                    gr.Markdown("## 👤 Datos Recolectados")

                    # Display compacto con formato de una línea
                    with gr.Group():
                        user_id_display = gr.Textbox(
                            label="",
                            value="🆔 ID: USRPRUEBAS_00",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        user_name_display = gr.Textbox(
                            label="",
                            value="📝 Nombre: Aún no mencionó su nombre",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        user_email_display = gr.Textbox(
                            label="",
                            value="📧 Email: No proporcionado",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        user_phone_display = gr.Textbox(
                            label="",
                            value="📱 Teléfono: +1234567890",
                            interactive=True,
                            show_label=False,
                            container=False,
                            placeholder="Ingrese número de teléfono"
                        )
                        last_contact_display = gr.Textbox(
                            label="",
                            value="🕐 Último contacto: -",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        intent_display = gr.Textbox(
                            label="",
                            value="🎯 Intención: -",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        sentiment_display = gr.Textbox(
                            label="",
                            value="😊 Sentimiento: -",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        stage_display = gr.Textbox(
                            label="",
                            value="📊 Etapa: -",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        needs_display = gr.Textbox(
                            label="",
                            value="💡 Necesidades: -",
                            interactive=False,
                            show_label=False,
                            container=False,
                            lines=2
                        )
                        requests_human_display = gr.Textbox(
                            label="",
                            value="👨‍💼 Solicita Humano: No",
                            interactive=False,
                            show_label=False,
                            container=False
                        )
                        notes_display = gr.Textbox(
                            label="",
                            value="📋 Notas: -",
                            interactive=False,
                            show_label=False,
                            container=False,
                            lines=3
                        )

                # Columna derecha: Chat de prueba
                with gr.Column(scale=2):
                    gr.Markdown("## 💬 Conversación de Prueba")

                    chatbot = gr.Chatbot(
                        label="Chat",
                        height=500,
                        type="messages",
                    )

                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Escribe tu mensaje...",
                            show_label=False,
                            scale=4,
                        )
                        send = gr.Button("Enviar", variant="primary", scale=1)

                    clear = gr.Button("Limpiar Chat", size="sm")

            # Función para actualizar datos del usuario
            async def process_chat_with_data(message: str, history: list, current_user_id, current_name, current_email, current_phone, current_last_contact, current_intent, current_sentiment, current_stage, current_needs, current_requests_human, current_notes) -> tuple:
                """Procesar chat y actualizar datos del usuario."""
                from datetime import datetime
                import uuid

                # Procesar mensaje normalmente
                new_history, empty_str = await process_chat(message, history)

                # Manejar mensajes multiparte con [PAUSA]
                if new_history and len(new_history) > 0:
                    last_bot_message = new_history[-1]
                    bot_content = last_bot_message.get("content", "")

                    # Buscar [PAUSA] con cualquier variación de espacios/saltos de línea
                    if last_bot_message.get("role") == "assistant" and "[PAUSA]" in bot_content:
                        # Dividir por el patrón de [PAUSA] con espacios/saltos
                        import re
                        # Reemplazar variaciones de [PAUSA] con un separador único
                        bot_response = re.sub(r'\s*\[PAUSA\]\s*', '|||SPLIT|||', bot_content)
                        parts = [p.strip() for p in bot_response.split('|||SPLIT|||') if p.strip()]

                        # Si hay múltiples partes, remover el último mensaje y agregar partes separadas
                        if len(parts) > 1:
                            new_history = new_history[:-1]
                            for part in parts:
                                new_history.append({"role": "assistant", "content": part})

                # Extraer valores actuales (removiendo el formato)
                user_id = current_user_id.split(": ", 1)[1] if ": " in current_user_id else ""
                name = current_name.split(": ", 1)[1] if ": " in current_name else ""
                email = current_email.split(": ", 1)[1] if ": " in current_email else ""
                phone = current_phone.split(": ", 1)[1] if ": " in current_phone else "+1234567890"
                intent = current_intent.split(": ", 1)[1] if ": " in current_intent else ""
                sentiment = current_sentiment.split(": ", 1)[1] if ": " in current_sentiment else ""
                stage = current_stage.split(": ", 1)[1] if ": " in current_stage else ""
                needs = current_needs.split(": ", 1)[1] if ": " in current_needs else ""
                requests_human = current_requests_human.split(": ", 1)[1] if ": " in current_requests_human else "No"
                notes = current_notes.split(": ", 1)[1] if ": " in current_notes else ""

                # Generar user_id si no existe o está en formato por defecto
                # Fix 1: Validación mejorada de User ID
                if not user_id or user_id in ["user_12345678", "USR_00", "USRPRUEBAS_00", "USRPRUEBAS_", "USR_"] or user_id.startswith("user_"):
                    # Detectar entorno (PRD vs testing)
                    environment = os.getenv("ENVIRONMENT", "testing").lower()

                    # Generar número secuencial (aquí usamos timestamp para unicidad)
                    from time import time
                    unique_num = str(int(time() * 1000))[-8:]  # Últimos 8 dígitos del timestamp

                    if environment == "production" or environment == "prd":
                        user_id = f"USR_{unique_num}"
                    else:
                        user_id = f"USRPRUEBAS_{unique_num}"

                    # Fix 3: Logging mejorado
                    print(f"✅ User ID generado: {user_id} (Entorno: {environment})")

                # Actualizar último contacto
                last_contact = datetime.now().strftime("%d/%m/%Y %H:%M")

                # Detectar intent básico
                message_lower = message.lower()
                if any(word in message_lower for word in ["comprar", "precio", "costo", "pagar", "quiero"]):
                    intent = "Compra 🛒"
                elif any(word in message_lower for word in ["info", "informacion", "que es", "como", "dime", "explica"]):
                    intent = "Información ℹ️"
                elif any(word in message_lower for word in ["ayuda", "problema", "error", "no funciona"]):
                    intent = "Soporte 🆘"
                elif any(word in message_lower for word in ["hola", "buenos", "hey", "saludos"]):
                    intent = "Saludo 👋"
                else:
                    intent = "Conversación 💬"

                # Detectar sentimiento básico
                if any(word in message_lower for word in ["genial", "perfecto", "excelente", "gracias", "increible"]):
                    sentiment = "Positivo 😊"
                elif any(word in message_lower for word in ["mal", "terrible", "horrible", "problema", "no me gusta"]):
                    sentiment = "Negativo 😞"
                else:
                    sentiment = "Neutral 😐"

                # Detectar solicitud de humano
                if any(word in message_lower for word in ["humano", "persona", "supervisor", "agente", "operador", "hablar con alguien", "hablar con un"]):
                    requests_human = "Sí"
                    # Fix 3: Logging mejorado
                    print(f"🚨 Flag 'Solicita Humano' activado para User ID: {user_id}")

                # Detectar nombre (mejorado)
                import re
                if "me llamo" in message_lower or "soy" in message_lower or "mi nombre es" in message_lower:
                    words = message.split()
                    for i, word in enumerate(words):
                        if word.lower() in ["llamo", "soy", "nombre"] and i + 1 < len(words):
                            potential_name = words[i + 1].strip(",.!?")
                            if potential_name and len(potential_name) > 1:
                                # Capitalize first letter
                                name = potential_name.capitalize()
                                break

                # Si no se detectó nombre pero el mensaje es corto y empieza con mayúscula (posible nombre)
                if not name or name == "Aún no mencionó su nombre":
                    if len(message.split()) <= 3 and message.strip() and message.strip()[0].isupper():
                        # Podría ser un nombre
                        potential_name = message.split()[0].strip(",.!?")
                        if len(potential_name) > 2 and potential_name.isalpha():
                            name = potential_name.capitalize()

                # Detectar email (mejorado con regex)
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_match = re.search(email_pattern, message)
                if email_match:
                    email = email_match.group(0)

                # Detectar teléfono (nuevo)
                # Buscar patrones como "mi teléfono es", "mi telefono es", "mi número es", o simplemente números largos
                phone_keywords = ["teléfono", "telefono", "número", "numero", "celular", "whatsapp", "contacto"]
                if any(keyword in message_lower for keyword in phone_keywords):
                    # Extraer números después del keyword
                    phone_pattern = r'[\d\s\-\+\(\)]{8,}'
                    phone_match = re.search(phone_pattern, message)
                    if phone_match:
                        extracted_phone = phone_match.group(0).strip()
                        # Limpiar espacios y caracteres extra
                        phone = re.sub(r'[^\d\+]', '', extracted_phone)
                        if len(phone) >= 8:  # Validar que tenga al menos 8 dígitos
                            phone = "+" + phone if not phone.startswith("+") else phone
                # También detectar si el mensaje es solo un número largo (probablemente teléfono)
                elif re.match(r'^[\d\s\-\+\(\)]{8,}$', message.strip()):
                    phone = re.sub(r'[^\d\+]', '', message.strip())
                    if len(phone) >= 8:
                        phone = "+" + phone if not phone.startswith("+") else phone

                # Etapa
                if len(new_history) <= 2:
                    stage = "Bienvenida 👋"
                elif intent == "Compra 🛒":
                    stage = "Cierre 💰"
                elif intent == "Información ℹ️":
                    stage = "Calificación 🔍"
                else:
                    stage = "Conversación 💬"

                # Detectar necesidades
                if any(word in message_lower for word in ["necesito", "quiero", "busco", "me interesa"]):
                    needs = message

                # Generar notas en puntos clave usando GPT-4 mini
                if stage == "Cierre 💰" or requests_human == "Sí" or len(new_history) >= 10:
                    try:
                        # Usar LLM para generar notas inteligentes
                        from services.llm_service import get_llm_service
                        llm_service = get_llm_service()

                        # Preparar datos del usuario
                        user_data = {
                            "name": name if name and name != "Aún no mencionó su nombre" else "",
                            "email": email if email and email != "No proporcionado" else "",
                            "phone": phone if phone != "+1234567890" else "",
                            "needs": needs if needs != "-" else "",
                            "intent": intent,
                            "sentiment": sentiment,
                            "stage": stage,
                            "requests_human": requests_human == "Sí"
                        }

                        # Fix 2: Manejo de errores mejorado en conversión de historial
                        from langchain_core.messages import HumanMessage, AIMessage
                        conversation_history = []
                        try:
                            for msg in history:
                                # Validar que msg es dict y tiene las keys necesarias
                                if not isinstance(msg, dict):
                                    print(f"⚠️ Mensaje no es dict, saltando: {type(msg)}")
                                    continue

                                role = msg.get("role")
                                content = msg.get("content", "")

                                if role == "user" and content:
                                    conversation_history.append(HumanMessage(content=content))
                                elif role == "assistant" and content:
                                    conversation_history.append(AIMessage(content=content))
                        except Exception as conv_error:
                            print(f"⚠️ Error convirtiendo historial para notas: {conv_error}")
                            # Continuar con el historial parcial que se haya construido

                        # Generar notas con LLM
                        notes = await llm_service.generate_conversation_notes(user_data, conversation_history)

                        # Fix 3: Logging mejorado
                        print(f"📝 Notas generadas con LLM para User ID: {user_id} (Trigger: etapa={stage}, solicita_humano={requests_human}, msgs={len(new_history)})")

                    except Exception as e:
                        # Fallback a formato simple si hay error
                        print(f"❌ Error generating notes with LLM: {e}")
                        notes = f"Cliente: {name} | Email: {email} | Tel: {phone} | Etapa: {stage} | Intención: {intent}"

                # Formatear valores para display compacto
                user_id_display = f"🆔 ID: {user_id}"
                name_display = f"📝 Nombre: {name if name and name not in ['Aún no mencionó su nombre', '-'] else 'Aún no mencionó su nombre'}"
                email_display = f"📧 Email: {email if email and email not in ['No proporcionado', '-'] else 'No proporcionado'}"
                phone_display = f"📱 Teléfono: {phone}"
                last_contact_display = f"🕐 Último contacto: {last_contact}"
                intent_display = f"🎯 Intención: {intent if intent and intent != '-' else '-'}"
                sentiment_display = f"😊 Sentimiento: {sentiment if sentiment and sentiment != '-' else '-'}"
                stage_display = f"📊 Etapa: {stage if stage and stage != '-' else '-'}"
                needs_display = f"💡 Necesidades: {needs if needs and needs != '-' else '-'}"
                requests_human_display = f"👨‍💼 Solicita Humano: {requests_human}"
                notes_display = f"📋 Notas: {notes if notes else '-'}"

                return new_history, "", user_id_display, name_display, email_display, phone_display, last_contact_display, intent_display, sentiment_display, stage_display, needs_display, requests_human_display, notes_display

            # Connect events
            msg.submit(
                process_chat_with_data,
                [msg, chatbot, user_id_display, user_name_display, user_email_display, user_phone_display, last_contact_display, intent_display, sentiment_display, stage_display, needs_display, requests_human_display, notes_display],
                [chatbot, msg, user_id_display, user_name_display, user_email_display, user_phone_display, last_contact_display, intent_display, sentiment_display, stage_display, needs_display, requests_human_display, notes_display]
            )
            send.click(
                process_chat_with_data,
                [msg, chatbot, user_id_display, user_name_display, user_email_display, user_phone_display, last_contact_display, intent_display, sentiment_display, stage_display, needs_display, requests_human_display, notes_display],
                [chatbot, msg, user_id_display, user_name_display, user_email_display, user_phone_display, last_contact_display, intent_display, sentiment_display, stage_display, needs_display, requests_human_display, notes_display]
            )
            clear.click(
                lambda: ([], "🆔 ID: USRPRUEBAS_00", "📝 Nombre: Aún no mencionó su nombre", "📧 Email: No proporcionado", "📱 Teléfono: +1234567890", "🕐 Último contacto: -", "🎯 Intención: -", "😊 Sentimiento: -", "📊 Etapa: -", "💡 Necesidades: -", "👨‍💼 Solicita Humano: No", "📋 Notas: -"),
                None,
                [chatbot, user_id_display, user_name_display, user_email_display, user_phone_display, last_contact_display, intent_display, sentiment_display, stage_display, needs_display, requests_human_display, notes_display]
            )

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
