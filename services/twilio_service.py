"""Twilio service for sending WhatsApp messages."""

import os
from typing import Optional

from twilio.rest import Client

from utils.logging_config import get_logger

logger = get_logger(__name__)


class TwilioService:
    """Service for sending WhatsApp messages via Twilio."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        whatsapp_number: Optional[str] = None,
    ):
        """
        Initialize Twilio service.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            whatsapp_number: Twilio WhatsApp number (format: whatsapp:+1234567890)
        """
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = whatsapp_number or os.getenv("TWILIO_WHATSAPP_NUMBER")

        if not all([self.account_sid, self.auth_token, self.whatsapp_number]):
            raise ValueError("Twilio credentials must be provided or set in environment")

        # Ensure whatsapp_number has correct format
        if not self.whatsapp_number.startswith("whatsapp:"):
            self.whatsapp_number = f"whatsapp:{self.whatsapp_number}"

        self.client = Client(self.account_sid, self.auth_token)
        logger.info(f"Twilio service initialized with number {self.whatsapp_number}")

    def send_message(self, to_phone: str, message: str, media_url: Optional[str] = None) -> dict:
        """
        Send a WhatsApp message.

        Args:
            to_phone: Recipient phone number (format: +1234567890)
            message: Message text
            media_url: Optional media URL for sending images/audio

        Returns:
            Dict with message details (sid, status, etc.)

        Raises:
            Exception: If message sending fails
        """
        # Ensure to_phone has correct format
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        try:
            logger.info(f"Sending WhatsApp message to {to_phone}")

            params = {
                "from_": self.whatsapp_number,
                "to": to_phone,
                "body": message,
            }

            if media_url:
                params["media_url"] = [media_url]

            message_obj = self.client.messages.create(**params)

            result = {
                "sid": message_obj.sid,
                "status": message_obj.status,
                "to": to_phone,
                "from": self.whatsapp_number,
            }

            logger.info(f"Message sent successfully: {message_obj.sid}")
            return result

        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {to_phone}: {e}")
            raise

    def send_audio(self, to_phone: str, text: str, audio_url: str) -> dict:
        """
        Send a WhatsApp message with audio.

        Args:
            to_phone: Recipient phone number
            text: Message text
            audio_url: URL to audio file

        Returns:
            Dict with message details
        """
        return self.send_message(to_phone, text, media_url=audio_url)

    def get_message_status(self, message_sid: str) -> str:
        """
        Get the status of a sent message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Message status (queued, sent, delivered, failed, etc.)
        """
        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
        except Exception as e:
            logger.error(f"Error fetching message status for {message_sid}: {e}")
            return "unknown"


# Global instance (will be initialized in app.py)
twilio_service: Optional[TwilioService] = None


def get_twilio_service() -> TwilioService:
    """Get the global Twilio service instance."""
    global twilio_service
    if twilio_service is None:
        twilio_service = TwilioService()
    return twilio_service
