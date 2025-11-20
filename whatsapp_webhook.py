"""WhatsApp webhook handler for Twilio integration."""

import asyncio
from datetime import datetime
from typing import Dict

from fastapi import Request
from langchain_core.messages import AIMessage, HumanMessage

from database import crud
from graph.workflow import process_message
from services.config_manager import get_config_manager
from services.twilio_service import get_twilio_service
from services.tts_service import get_tts_service
from services.scheduler_service import get_scheduler_service
from utils.logging_config import get_logger
from utils.helpers import format_phone_number

logger = get_logger(__name__)


async def handle_whatsapp_webhook(request: Request, db_session_factory) -> Dict[str, str]:
    """
    Handle incoming WhatsApp webhook from Twilio.

    Process flow:
    1. Parse incoming message
    2. Find or create user in DB
    3. Check conversation_mode:
       - MANUAL: Save message, don't process, return
       - AUTO/NEEDS_ATTENTION: Process with LangGraph
    4. Execute graph
    5. Save response to DB
    6. Apply response delay
    7. Decide text vs audio
    8. Send response via Twilio
    9. Return 200 (Twilio requires fast response)

    Args:
        request: FastAPI request object
        db_session_factory: Database session factory

    Returns:
        Dict with status
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()

        from_number = form_data.get("From", "")  # Format: whatsapp:+1234567890
        message_body = form_data.get("Body", "")
        media_url = form_data.get("MediaUrl0")  # Optional media

        logger.info(f"Received WhatsApp message from {from_number}")

        # Format phone number
        phone = format_phone_number(from_number)

        # Get or create user
        async with db_session_factory() as db:
            user = await crud.get_user_by_phone(db, phone)
            if not user:
                logger.info(f"Creating new user: {phone}")
                user = await crud.create_user(db, phone)

            # Save incoming message
            await crud.create_message(
                db,
                user_id=user.id,
                message_text=message_body,
                sender="user",
            )

            # Check conversation mode
            conversation_mode = user.conversation_mode

            if conversation_mode == "MANUAL":
                logger.info(f"Conversation {phone} is in MANUAL mode, skipping bot processing")
                return {"status": "ok", "mode": "manual"}

            # Load conversation history
            messages = await crud.get_user_messages(db, user.id, limit=50)
            conversation_history = []
            for msg in messages[:-1]:  # Exclude the message we just saved
                if msg.sender == "user":
                    conversation_history.append(HumanMessage(content=str(msg.message_text)))
                else:
                    conversation_history.append(AIMessage(content=str(msg.message_text)))

            # Load configuration
            config_manager = get_config_manager()
            config = await config_manager.load_all_configs(db)

            # Process message through LangGraph
            logger.info(f"Processing message through LangGraph for {phone}")
            result = await process_message(
                user_phone=phone,
                message=message_body,
                conversation_history=conversation_history,
                config=config,
                db_session=db,
            )

            # Get response
            bot_response = result.get("current_response")
            if not bot_response:
                logger.error("No response generated from graph")
                return {"status": "error", "message": "No response generated"}

            # Update user state in database
            user_updates = {
                "intent_score": result.get("intent_score", user.intent_score),
                "sentiment": result.get("sentiment", user.sentiment),
                "stage": result.get("stage", user.stage),
                "conversation_mode": result.get("conversation_mode", user.conversation_mode),
            }

            # Update name and email if collected
            if result.get("user_name"):
                user_updates["name"] = result["user_name"]
            if result.get("user_email"):
                user_updates["email"] = result["user_email"]

            await crud.update_user(db, user.id, **user_updates)

            # Save bot response to DB
            await crud.create_message(
                db,
                user_id=user.id,
                message_text=bot_response,
                sender="bot",
                metadata={
                    "intent_score": result.get("intent_score"),
                    "sentiment": result.get("sentiment"),
                    "stage": result.get("stage"),
                },
            )

            # Handle follow-up scheduling if needed
            if result.get("follow_up_scheduled"):
                scheduled_time = result["follow_up_scheduled"]
                follow_up_count = result.get("follow_up_count", 0)

                # Create follow-up in DB
                from services.llm_service import get_llm_service

                llm_service = get_llm_service()
                follow_up_message = await llm_service.generate_follow_up_message(
                    user_data={
                        "name": user.name,
                        "stage": result.get("stage"),
                    },
                    follow_up_count=follow_up_count,
                )

                follow_up = await crud.create_follow_up(
                    db,
                    user_id=user.id,
                    scheduled_time=scheduled_time,
                    message=follow_up_message,
                    follow_up_count=follow_up_count,
                )

                # Schedule with APScheduler
                scheduler_service = get_scheduler_service()

                async def send_follow_up_message(phone, message):
                    """Async function to send scheduled follow-up."""
                    try:
                        twilio_service = get_twilio_service()
                        twilio_service.send_message(phone, message)

                        # Update follow-up status in DB
                        async with db_session_factory() as db:
                            await crud.update_follow_up_status(db, follow_up.id, "sent")

                        logger.info(f"Follow-up sent to {phone}")
                    except Exception as e:
                        logger.error(f"Error sending follow-up: {e}")

                job_id = f"followup_{user.id}_{follow_up.id}"
                await scheduler_service.add_follow_up_job(
                    job_id=job_id,
                    phone=phone,
                    message=follow_up_message,
                    scheduled_time=scheduled_time,
                    send_function=send_follow_up_message,
                )

                logger.info(f"Scheduled follow-up for {phone} at {scheduled_time}")

        # Apply response delay (outside DB session)
        response_delay = config.get("response_delay", 1.0)
        if response_delay > 0:
            await asyncio.sleep(response_delay)

        # Determine if we should send audio
        text_audio_ratio = config.get("text_audio_ratio", 0)
        tts_service = get_tts_service()

        if tts_service.should_generate_audio(text_audio_ratio):
            # Generate and send audio
            logger.info("Generating audio for response")
            try:
                voice = config.get("tts_voice", "nova")
                audio_base64 = await tts_service.generate_audio_base64(bot_response, voice)

                # TODO: Upload audio to a public URL and send via Twilio
                # For now, just send text
                twilio_service = get_twilio_service()
                twilio_service.send_message(phone, bot_response)
            except Exception as e:
                logger.error(f"Error generating audio, falling back to text: {e}")
                twilio_service = get_twilio_service()
                twilio_service.send_message(phone, bot_response)
        else:
            # Send text only
            twilio_service = get_twilio_service()
            twilio_service.send_message(phone, bot_response)

        logger.info(f"Response sent to {phone}")

        return {"status": "ok", "message": "Processed successfully"}

    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
