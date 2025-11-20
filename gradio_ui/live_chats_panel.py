"""Panel de conversaciones en vivo estilo WhatsApp Web."""

from typing import List, Dict, Optional, Tuple
import gradio as gr
import asyncio
from datetime import datetime

from database import crud
from services.twilio_service import get_twilio_service
from utils.helpers import format_timestamp
from utils.logging_config import get_logger

logger = get_logger(__name__)


class LiveChatsPanel:
    """Panel de chats en vivo estilo WhatsApp Web."""

    def __init__(self, db_session_factory):
        """
        Inicializar panel de chats.

        Args:
            db_session_factory: Factory para crear sesiones de BD
        """
        self.db_session_factory = db_session_factory
        self.selected_user_id = None
        logger.info("Panel de chats en vivo inicializado")

    def format_conversation_item(self, user, last_message: str, unread: bool = False) -> str:
        """
        Formatear item de conversacion para la lista.

        Args:
            user: Objeto User
            last_message: Ultimo mensaje
            unread: Si tiene mensajes sin leer

        Returns:
            HTML formateado
        """
        # Indicator de modo
        if user.conversation_mode == "AUTO":
            mode_indicator = "🟢"
        elif user.conversation_mode == "MANUAL":
            mode_indicator = "🔴"
        else:
            mode_indicator = "⚠️"

        # Nombre o telefono
        display_name = user.name or user.phone

        # Timestamp
        time_str = format_timestamp(user.last_message_at) if user.last_message_at else ""

        # Truncar mensaje
        msg_preview = last_message[:50] + "..." if len(last_message) > 50 else last_message

        style = "font-weight: bold;" if unread else ""

        return f"""
        <div style="padding: 12px; border-bottom: 1px solid #e0e0e0; cursor: pointer; {style}">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 16px;">{mode_indicator} {display_name}</span>
                <span style="font-size: 12px; color: #666;">{time_str}</span>
            </div>
            <div style="font-size: 14px; color: #666; margin-top: 4px;">
                {msg_preview}
            </div>
        </div>
        """

    async def get_conversations_list(self) -> str:
        """
        Obtener lista de conversaciones activas.

        Returns:
            HTML con la lista de conversaciones
        """
        try:
            async with self.db_session_factory() as db:
                users = await crud.get_all_active_users(db, limit=50)

                if not users:
                    return "<div style='padding: 20px; text-align: center; color: #999;'>No hay conversaciones activas</div>"

                html_parts = []
                for user in users:
                    # Obtener ultimo mensaje
                    messages = await crud.get_recent_messages(db, user.id, count=1)
                    last_msg = messages[0].message_text if messages else "Sin mensajes"

                    html_parts.append(self.format_conversation_item(user, last_msg))

                return "".join(html_parts)

        except Exception as e:
            logger.error(f"Error obteniendo lista de conversaciones: {e}")
            return f"<div style='padding: 20px; color: red;'>Error: {str(e)}</div>"

    async def get_conversation_messages(self, user_id: int) -> List[Dict]:
        """
        Obtener mensajes de una conversacion.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de mensajes en formato Gradio
        """
        try:
            async with self.db_session_factory() as db:
                messages = await crud.get_user_messages(db, user_id, limit=100)

                # Convertir a formato Gradio chatbot
                formatted_messages = []
                for msg in messages:
                    if msg.sender == "user":
                        formatted_messages.append({
                            "role": "user",
                            "content": msg.message_text
                        })
                    else:
                        formatted_messages.append({
                            "role": "assistant",
                            "content": msg.message_text
                        })

                return formatted_messages

        except Exception as e:
            logger.error(f"Error obteniendo mensajes: {e}")
            return []

    async def get_user_info(self, user_id: int) -> str:
        """
        Obtener informacion del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            HTML con info del usuario
        """
        try:
            async with self.db_session_factory() as db:
                user = await crud.get_user_by_id(db, user_id)

                if not user:
                    return "Usuario no encontrado"

                # Modo
                if user.conversation_mode == "AUTO":
                    mode_display = "🟢 Automatico"
                elif user.conversation_mode == "MANUAL":
                    mode_display = "🔴 Manual"
                else:
                    mode_display = "⚠️ Necesita Atencion"

                return f"""
                <div style="padding: 16px; background: #f5f5f5; border-radius: 8px;">
                    <h3 style="margin: 0 0 12px 0;">{user.name or 'Sin nombre'}</h3>
                    <p><strong>Telefono:</strong> {user.phone}</p>
                    <p><strong>Email:</strong> {user.email or 'No registrado'}</p>
                    <p><strong>Modo:</strong> {mode_display}</p>
                    <p><strong>Total Mensajes:</strong> {user.total_messages}</p>
                    <p><strong>Ultima actividad:</strong> {format_timestamp(user.last_message_at) if user.last_message_at else 'N/A'}</p>
                </div>
                """

        except Exception as e:
            logger.error(f"Error obteniendo info de usuario: {e}")
            return f"Error: {str(e)}"

    async def send_manual_message(self, user_id: int, message: str) -> Tuple[str, List[Dict]]:
        """
        Enviar mensaje manual.

        Args:
            user_id: ID del usuario
            message: Texto del mensaje

        Returns:
            Tupla (status_message, updated_chat_history)
        """
        if not message.strip():
            return "Por favor ingresa un mensaje", []

        try:
            async with self.db_session_factory() as db:
                user = await crud.get_user_by_id(db, user_id)

                if not user:
                    return "Usuario no encontrado", []

                # Enviar via Twilio si esta configurado
                try:
                    twilio_service = get_twilio_service()
                    if twilio_service:
                        twilio_service.send_message(user.phone, message)
                except Exception as e:
                    logger.warning(f"Twilio no disponible: {e}")

                # Guardar en BD
                await crud.create_message(
                    db,
                    user_id=user.id,
                    message_text=message,
                    sender="bot",
                    metadata={"manual": True, "timestamp": datetime.utcnow().isoformat()},
                )

                # Obtener historial actualizado
                updated_history = await self.get_conversation_messages(user_id)

                logger.info(f"Mensaje manual enviado a usuario {user_id}")
                return "✅ Mensaje enviado", updated_history

        except Exception as e:
            logger.error(f"Error enviando mensaje manual: {e}")
            return f"❌ Error: {str(e)}", []

    async def toggle_conversation_mode(self, user_id: int) -> str:
        """
        Alternar modo de conversacion (AUTO <-> MANUAL).

        Args:
            user_id: ID del usuario

        Returns:
            Mensaje de estado
        """
        try:
            async with self.db_session_factory() as db:
                user = await crud.get_user_by_id(db, user_id)

                if not user:
                    return "Usuario no encontrado"

                # Alternar modo
                new_mode = "MANUAL" if user.conversation_mode == "AUTO" else "AUTO"
                await crud.update_user(db, user_id, conversation_mode=new_mode)

                if new_mode == "MANUAL":
                    return "🔴 Modo MANUAL activado - El bot no respondera"
                else:
                    return "🟢 Modo AUTO activado - El bot respondera automaticamente"

        except Exception as e:
            logger.error(f"Error alternando modo: {e}")
            return f"❌ Error: {str(e)}"

    def create_component(self) -> gr.Column:
        """
        Crear componente UI estilo WhatsApp Web.

        Returns:
            Columna Gradio con el panel
        """
        with gr.Column() as col:
            gr.Markdown("## 💬 Conversaciones en Tiempo Real")

            with gr.Row():
                # Columna izquierda: Lista de conversaciones
                with gr.Column(scale=1):
                    gr.Markdown("### Chats Activos")

                    conversations_html = gr.HTML(
                        value=lambda: asyncio.run(self.get_conversations_list()),
                        every=5,  # Auto-refresh cada 5 segundos
                        label="Conversaciones",
                    )

                    refresh_btn = gr.Button("🔄 Actualizar", size="sm")

                # Columna derecha: Chat y detalles
                with gr.Column(scale=2):
                    # Info del usuario seleccionado
                    user_info_html = gr.HTML(
                        value="<div style='padding: 20px; text-align: center; color: #999;'>Selecciona una conversacion</div>"
                    )

                    # Boton de control
                    toggle_mode_btn = gr.Button("🔄 Cambiar Modo (AUTO/MANUAL)", variant="secondary")
                    mode_status = gr.Textbox(label="Estado", interactive=False)

                    gr.Markdown("---")

                    # Chat
                    gr.Markdown("### Historial de Mensajes")
                    chat_display = gr.Chatbot(
                        label="Conversacion",
                        height=400,
                        type="messages",
                    )

                    # Input para mensaje manual
                    with gr.Row():
                        manual_msg_input = gr.Textbox(
                            placeholder="Escribe un mensaje manual...",
                            show_label=False,
                            scale=4,
                        )
                        send_btn = gr.Button("Enviar", scale=1, variant="primary")

                    send_status = gr.Textbox(label="Estado de Envio", interactive=False)

            # Estado: usuario seleccionado
            selected_user_id_state = gr.State(value=None)

            # Handlers - Gradio soporta async nativamente
            # Refresh conversaciones
            refresh_btn.click(
                self.get_conversations_list,
                None,
                conversations_html,
            )

            # TODO: Implementar seleccion de conversacion (requiere JavaScript custom)
            # Por ahora, usaremos un selector manual

            # Enviar mensaje
            async def handle_send_message(user_id, message):
                if user_id is None:
                    return "Por favor selecciona una conversacion primero", []
                return await self.send_manual_message(user_id, message)

            send_btn.click(
                handle_send_message,
                [selected_user_id_state, manual_msg_input],
                [send_status, chat_display],
            )

            # Toggle modo
            async def handle_toggle_mode(user_id):
                if user_id is None:
                    return "Por favor selecciona una conversacion primero"
                return await self.toggle_conversation_mode(user_id)

            toggle_mode_btn.click(
                handle_toggle_mode,
                selected_user_id_state,
                mode_status,
            )

        return col
