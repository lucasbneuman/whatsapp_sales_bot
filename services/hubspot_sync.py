"""HubSpot CRM synchronization service."""

import os
from typing import Any, Dict, Optional

import requests

from utils.logging_config import get_logger

logger = get_logger(__name__)


class HubSpotService:
    """Service for syncing customer data to HubSpot CRM."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HubSpot service.

        Args:
            api_key: HubSpot API key
        """
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        if not self.api_key:
            logger.warning("HubSpot API key not found, sync will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = "https://api.hubapi.com"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            logger.info("HubSpot service initialized")

    async def sync_contact(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Sync contact to HubSpot (create or update).

        Strategy:
        1. Search for existing contact by phone or email
        2. If exists: UPDATE only new fields (don't overwrite)
        3. If not exists: CREATE new contact

        Args:
            user_data: User data dict with fields:
                - phone: required
                - name, email, intent_score, sentiment, stage: optional

        Returns:
            HubSpot contact ID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("HubSpot sync skipped: API key not configured")
            return None

        phone = user_data.get("phone")
        if not phone:
            logger.error("Cannot sync to HubSpot: phone is required")
            return None

        try:
            # Search for existing contact
            existing_contact = await self._search_contact(phone, user_data.get("email"))

            if existing_contact:
                # Update existing contact
                contact_id = existing_contact["id"]
                logger.info(f"Updating existing HubSpot contact: {contact_id}")
                await self._update_contact(contact_id, user_data, existing_contact)
                return contact_id
            else:
                # Create new contact
                logger.info(f"Creating new HubSpot contact for phone: {phone}")
                contact_id = await self._create_contact(user_data)
                return contact_id

        except Exception as e:
            logger.error(f"HubSpot sync error: {e}")
            return None

    async def _search_contact(self, phone: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for existing contact by phone or email.

        Args:
            phone: Phone number
            email: Email address (optional)

        Returns:
            Contact data if found, None otherwise
        """
        try:
            # Search by phone
            search_payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "phone",
                                "operator": "EQ",
                                "value": phone,
                            }
                        ]
                    }
                ]
            }

            # Add email filter if available
            if email:
                search_payload["filterGroups"].append({
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                })

            response = requests.post(
                f"{self.base_url}/crm/v3/objects/contacts/search",
                headers=self.headers,
                json=search_payload,
                timeout=10,
            )

            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    contact = results[0]
                    logger.info(f"Found existing HubSpot contact: {contact['id']}")
                    return contact

            return None

        except Exception as e:
            logger.error(f"Error searching HubSpot contact: {e}")
            return None

    async def _create_contact(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new HubSpot contact.

        Args:
            user_data: User data

        Returns:
            Contact ID if successful, None otherwise
        """
        try:
            # Prepare properties
            properties = self._prepare_properties(user_data)

            payload = {"properties": properties}

            response = requests.post(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=self.headers,
                json=payload,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                contact_id = response.json()["id"]
                logger.info(f"Created HubSpot contact: {contact_id}")
                return contact_id
            else:
                logger.error(f"Failed to create HubSpot contact: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating HubSpot contact: {e}")
            return None

    async def _update_contact(
        self,
        contact_id: str,
        user_data: Dict[str, Any],
        existing_contact: Dict[str, Any],
    ) -> bool:
        """
        Update existing HubSpot contact (only update new/changed fields).

        Args:
            contact_id: HubSpot contact ID
            user_data: New user data
            existing_contact: Existing contact data from HubSpot

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare properties, but only include new/changed ones
            new_properties = self._prepare_properties(user_data)
            existing_properties = existing_contact.get("properties", {})

            # Filter to only update new or changed fields
            update_properties = {}
            for key, value in new_properties.items():
                existing_value = existing_properties.get(key)
                # Only update if: field doesn't exist OR value is different OR existing is empty
                if not existing_value or existing_value != str(value):
                    update_properties[key] = value

            if not update_properties:
                logger.info(f"No new data to update for contact {contact_id}")
                return True

            payload = {"properties": update_properties}

            response = requests.patch(
                f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                headers=self.headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(f"Updated HubSpot contact {contact_id}: {list(update_properties.keys())}")
                return True
            else:
                logger.error(f"Failed to update HubSpot contact: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error updating HubSpot contact: {e}")
            return False

    def _prepare_properties(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare HubSpot properties from user data.

        Args:
            user_data: User data

        Returns:
            Dict of HubSpot properties
        """
        properties = {}

        # Map user_data fields to HubSpot properties
        if user_data.get("phone"):
            properties["phone"] = user_data["phone"]

        if user_data.get("name"):
            # Split name into firstname and lastname if possible
            name_parts = user_data["name"].split(maxsplit=1)
            properties["firstname"] = name_parts[0]
            if len(name_parts) > 1:
                properties["lastname"] = name_parts[1]

        if user_data.get("email"):
            properties["email"] = user_data["email"]

        if user_data.get("intent_score") is not None:
            properties["intent_score"] = str(user_data["intent_score"])

        if user_data.get("sentiment"):
            properties["sentiment"] = user_data["sentiment"]

        if user_data.get("stage"):
            properties["lifecyclestage"] = user_data["stage"]

        return properties


# Global instance (will be initialized in app.py)
hubspot_service: Optional[HubSpotService] = None


def get_hubspot_service() -> HubSpotService:
    """Get the global HubSpot service instance."""
    global hubspot_service
    if hubspot_service is None:
        hubspot_service = HubSpotService()
    return hubspot_service
