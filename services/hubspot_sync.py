"""HubSpot CRM synchronization service."""

import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from utils.logging_config import get_logger

logger = get_logger(__name__)


class HubSpotService:
    """Service for syncing customer data to HubSpot CRM."""

    # HubSpot Lifecycle Stages
    LIFECYCLE_STAGES = {
        "welcome": "lead",
        "qualifying": "lead",
        "nurturing": "marketingqualifiedlead",
        "closing": "salesqualifiedlead",
        "sold": "customer",
        "follow_up": "opportunity",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HubSpot service.

        Args:
            api_key: HubSpot API key (Private App Access Token)
        """
        self.api_key = api_key or os.getenv("HUBSPOT_ACCESS_TOKEN")
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

    async def sync_contact(
        self,
        user_data: Dict[str, Any],
        db_user: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sync contact to HubSpot (create or update).

        Strategy:
        1. Check if we have hubspot_contact_id in our DB
        2. If yes: Verify it still exists in HubSpot, then UPDATE
        3. If no: Search by phone/email in HubSpot
        4. If found: UPDATE and save hubspot_contact_id
        5. If not found: CREATE new contact and save hubspot_contact_id

        Args:
            user_data: User data dict with fields:
                - phone: required
                - name, email, intent_score, sentiment, stage: optional
            db_user: Database User object (to check/update hubspot_contact_id)

        Returns:
            Dict with:
                - contact_id: HubSpot contact ID
                - lifecyclestage: HubSpot lifecycle stage
                - action: 'created', 'updated', or 'skipped'
        """
        if not self.enabled:
            logger.warning("HubSpot sync skipped: API key not configured")
            return None

        phone = user_data.get("phone")
        if not phone:
            logger.error("Cannot sync to HubSpot: phone is required")
            return None

        try:
            contact_id = None
            action = "skipped"
            lifecyclestage = None

            # Step 1: Check if we have hubspot_contact_id in DB
            if db_user and db_user.hubspot_contact_id:
                logger.info(f"Found hubspot_contact_id in DB: {db_user.hubspot_contact_id}")
                # Verify contact still exists in HubSpot
                existing_contact = await self._get_contact_by_id(db_user.hubspot_contact_id)

                if existing_contact:
                    # Update existing contact
                    logger.info(f"Updating existing HubSpot contact: {db_user.hubspot_contact_id}")
                    success = await self._update_contact(db_user.hubspot_contact_id, user_data, existing_contact)
                    if success:
                        contact_id = db_user.hubspot_contact_id
                        lifecyclestage = existing_contact.get("properties", {}).get("lifecyclestage")
                        action = "updated"
                else:
                    logger.warning(f"HubSpot contact {db_user.hubspot_contact_id} no longer exists, will search/create")
                    db_user.hubspot_contact_id = None  # Reset since it doesn't exist

            # Step 2: If no valid contact_id, search by phone/email
            if not contact_id:
                existing_contact = await self._search_contact(phone, user_data.get("email"))

                if existing_contact:
                    # Found in HubSpot, update it
                    contact_id = existing_contact["id"]
                    logger.info(f"Found HubSpot contact by search: {contact_id}")
                    await self._update_contact(contact_id, user_data, existing_contact)
                    lifecyclestage = existing_contact.get("properties", {}).get("lifecyclestage")
                    action = "updated"
                else:
                    # Not found, create new contact
                    logger.info(f"Creating new HubSpot contact for phone: {phone}")
                    result = await self._create_contact(user_data)
                    if result:
                        contact_id = result["id"]
                        lifecyclestage = result.get("lifecyclestage")
                        action = "created"

            if contact_id:
                logger.info(f"✅ HubSpot sync successful: {action} contact {contact_id}")
                return {
                    "contact_id": contact_id,
                    "lifecyclestage": lifecyclestage,
                    "action": action,
                    "synced_at": datetime.utcnow()
                }
            else:
                logger.error("HubSpot sync failed: no contact_id returned")
                return None

        except Exception as e:
            logger.error(f"HubSpot sync error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _get_contact_by_id(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contact by HubSpot contact ID.

        Args:
            contact_id: HubSpot contact ID

        Returns:
            Contact data if found, None otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                headers=self.headers,
                timeout=10,
            )

            if response.status_code == 200:
                contact = response.json()
                logger.info(f"Retrieved HubSpot contact: {contact_id}")
                return contact
            elif response.status_code == 404:
                logger.warning(f"HubSpot contact {contact_id} not found (404)")
                return None
            else:
                logger.error(f"Error retrieving HubSpot contact: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting HubSpot contact by ID: {e}")
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
            # Search by phone first
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
                    logger.info(f"Found HubSpot contact by phone: {contact['id']}")
                    return contact

            # If not found by phone and email is available, try email
            if email:
                search_payload = {
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email,
                                }
                            ]
                        }
                    ]
                }

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
                        logger.info(f"Found HubSpot contact by email: {contact['id']}")
                        return contact

            logger.info(f"No existing HubSpot contact found for phone: {phone}")
            return None

        except Exception as e:
            logger.error(f"Error searching HubSpot contact: {e}")
            return None

    async def _create_contact(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new HubSpot contact.

        Args:
            user_data: User data

        Returns:
            Dict with contact_id and lifecyclestage if successful, None otherwise
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
                result = response.json()
                contact_id = result["id"]
                lifecyclestage = result.get("properties", {}).get("lifecyclestage")
                logger.info(f"✅ Created HubSpot contact: {contact_id} (stage: {lifecyclestage})")
                return {
                    "id": contact_id,
                    "lifecyclestage": lifecyclestage
                }
            elif response.status_code == 400 and "PROPERTY_DOESNT_EXIST" in response.text:
                # If custom field doesn't exist, retry without it
                logger.warning(f"Some custom fields don't exist in HubSpot, retrying without them...")

                # Remove problematic fields and retry (keep commonly available fields)
                standard_properties = {k: v for k, v in properties.items()
                                     if k in ['phone', 'firstname', 'lastname', 'email', 'lifecyclestage',
                                             'intent_score', 'sentiment', 'needs', 'pain_points', 'budget',
                                             'hs_content_membership_notes', 'hs_lead_status']}

                retry_payload = {"properties": standard_properties}
                retry_response = requests.post(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    headers=self.headers,
                    json=retry_payload,
                    timeout=10,
                )

                if retry_response.status_code in [200, 201]:
                    result = retry_response.json()
                    contact_id = result["id"]
                    lifecyclestage = result.get("properties", {}).get("lifecyclestage")
                    logger.info(f"✅ Created HubSpot contact {contact_id} (without custom fields, stage: {lifecyclestage})")
                    return {
                        "id": contact_id,
                        "lifecyclestage": lifecyclestage
                    }

                logger.error(f"Failed to create HubSpot contact even without custom fields")
                return None
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
                # Only update if: field doesn't exist OR value is different OR existing is empty/null
                if not existing_value or str(existing_value).lower() in ['none', 'null', ''] or existing_value != str(value):
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
                logger.info(f"✅ Updated HubSpot contact {contact_id}: {list(update_properties.keys())}")
                return True
            elif response.status_code == 400 and "PROPERTY_DOESNT_EXIST" in response.text:
                # If custom field doesn't exist, retry without it
                logger.warning(f"Some custom fields don't exist in HubSpot, retrying without them...")

                # Remove problematic fields and retry (keep commonly available fields)
                standard_properties = {k: v for k, v in update_properties.items()
                                     if k in ['phone', 'firstname', 'lastname', 'email', 'lifecyclestage',
                                             'intent_score', 'sentiment', 'needs', 'pain_points', 'budget',
                                             'hs_content_membership_notes', 'hs_lead_status']}

                if standard_properties:
                    retry_payload = {"properties": standard_properties}
                    retry_response = requests.patch(
                        f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                        headers=self.headers,
                        json=retry_payload,
                        timeout=10,
                    )

                    if retry_response.status_code == 200:
                        logger.info(f"✅ Updated HubSpot contact {contact_id} (without custom fields): {list(standard_properties.keys())}")
                        return True

                logger.error(f"Failed to update HubSpot contact even without custom fields")
                return False
            else:
                logger.error(f"Failed to update HubSpot contact: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error updating HubSpot contact: {e}")
            return False

    def _prepare_properties(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare HubSpot properties from user data.

        Maps our internal fields to HubSpot standard properties.

        Args:
            user_data: User data

        Returns:
            Dict of HubSpot properties
        """
        properties = {}

        # Required: Phone
        if user_data.get("phone"):
            properties["phone"] = user_data["phone"]

        # Name: Split into firstname and lastname
        if user_data.get("name"):
            name_parts = user_data["name"].strip().split(maxsplit=1)
            properties["firstname"] = name_parts[0]
            if len(name_parts) > 1:
                properties["lastname"] = name_parts[1]
            else:
                properties["lastname"] = ""  # HubSpot likes having both

        # Email
        if user_data.get("email"):
            properties["email"] = user_data["email"]

        # Lifecycle Stage: Map our internal stage to HubSpot lifecycle
        if user_data.get("stage"):
            internal_stage = user_data["stage"]
            hubspot_stage = self.LIFECYCLE_STAGES.get(internal_stage, "lead")
            properties["lifecyclestage"] = hubspot_stage

        # Intent Score (0-1 scale) - Custom field
        if user_data.get("intent_score") is not None:
            properties["intent_score"] = str(round(user_data["intent_score"], 2))

        # Sentiment - Custom field
        if user_data.get("sentiment"):
            properties["sentiment"] = user_data["sentiment"]

        # Customer Needs - Custom field
        if user_data.get("needs"):
            properties["needs"] = user_data["needs"]

        # Pain Points - Custom field
        if user_data.get("pain_points"):
            properties["pain_points"] = user_data["pain_points"]

        # Budget Range - Custom field
        if user_data.get("budget"):
            properties["budget"] = user_data["budget"]

        # Conversation Summary (Notes) - Use HubSpot's standard Notes field
        if user_data.get("conversation_summary"):
            properties["hs_content_membership_notes"] = user_data["conversation_summary"]

        # Lead Source
        properties["hs_lead_status"] = "NEW"  # or "OPEN", "IN_PROGRESS", etc.

        return properties


# Global instance (will be initialized in app.py)
hubspot_service: Optional[HubSpotService] = None


def get_hubspot_service() -> HubSpotService:
    """Get the global HubSpot service instance."""
    global hubspot_service
    if hubspot_service is None:
        hubspot_service = HubSpotService()
    return hubspot_service
