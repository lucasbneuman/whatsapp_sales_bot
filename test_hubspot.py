"""Test script for HubSpot CRM synchronization.

This script tests the complete HubSpot integration including:
- Contact creation
- Contact updates
- Data validation
- Field synchronization (name, email, phone, needs, pain_points, budget, intent_score, sentiment, notes)
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import services
from services.hubspot_sync import HubSpotService


class MockUser:
    """Mock User object for testing."""

    def __init__(self, hubspot_contact_id=None):
        self.id = 999
        self.phone = "+1234567890"
        self.name = None
        self.email = None
        self.hubspot_contact_id = hubspot_contact_id
        self.hubspot_lifecyclestage = None
        self.hubspot_synced_at = None


async def test_create_contact():
    """Test creating a new contact in HubSpot with all fields."""
    print("\n" + "=" * 60)
    print("TEST 1: CREATE NEW CONTACT WITH ALL FIELDS")
    print("=" * 60)

    hubspot = HubSpotService()

    if not hubspot.enabled:
        print("[ERROR] HubSpot not enabled. Check HUBSPOT_ACCESS_TOKEN in .env")
        return None

    # Mock user without hubspot_contact_id
    mock_user = MockUser(hubspot_contact_id=None)

    # Complete test data with all fields
    user_data = {
        "phone": "+5491112345678_PRUEBA",
        "name": "Lucas Neuman PRUEBA",
        "email": "lucas.prueba@test.com",
        "needs": "Busca CRM para automatizar ventas y marketing",
        "pain_points": "Pierde oportunidades por seguimiento manual de leads",
        "budget": "5000-8000 USD mensuales",
        "intent_score": 0.75,
        "sentiment": "positive",
        "stage": "nurturing",
        "conversation_summary": "Cliente interesado en CRM | Necesita automatizacion | Budget: 5000-8000 USD",
    }

    print(f"\n[DATA] Datos a sincronizar:")
    print(f"   Phone: {user_data['phone']}")
    print(f"   Name: {user_data['name']}")
    print(f"   Email: {user_data['email']}")
    print(f"   Needs: {user_data['needs']}")
    print(f"   Pain Points: {user_data['pain_points']}")
    print(f"   Budget: {user_data['budget']}")
    print(f"   Intent Score: {user_data['intent_score']}")
    print(f"   Sentiment: {user_data['sentiment']}")
    print(f"   Stage: {user_data['stage']}")
    print(f"   Notes: {user_data['conversation_summary']}")

    print(f"\n[SYNC] Sincronizando con HubSpot...")

    result = await hubspot.sync_contact(user_data, db_user=mock_user)

    if result:
        print(f"\n[SUCCESS] EXITO: {result['action'].upper()}")
        print(f"   Contact ID: {result['contact_id']}")
        print(f"   Lifecycle Stage: {result['lifecyclestage']}")
        print(f"   Synced At: {result['synced_at']}")
        print(f"\n[INFO] Mock User actualizado:")
        print(f"   hubspot_contact_id: {mock_user.hubspot_contact_id}")
        print(f"   hubspot_lifecyclestage: {mock_user.hubspot_lifecyclestage}")

        return result
    else:
        print(f"\n[ERROR] FALLO: No se pudo crear el contacto")
        return None


async def test_update_contact(existing_contact_id):
    """Test updating an existing contact in HubSpot."""
    print("\n" + "=" * 60)
    print("TEST 2: UPDATE EXISTING CONTACT")
    print("=" * 60)

    hubspot = HubSpotService()

    if not hubspot.enabled:
        print("[ERROR] HubSpot not enabled. Check HUBSPOT_ACCESS_TOKEN in .env")
        return

    # Mock user WITH hubspot_contact_id
    mock_user = MockUser(hubspot_contact_id=existing_contact_id)

    # Updated data
    user_data = {
        "phone": "+5491112345678_PRUEBA",
        "name": "Lucas Neuman PRUEBA",
        "email": "lucas.prueba.updated@test.com",  # Email actualizado
        "needs": "CRM con automatizacion avanzada y AI",  # Updated
        "pain_points": "Necesita escalar equipo de ventas rapidamente",  # Updated
        "budget": "8000-10000 USD mensuales",  # Updated
        "intent_score": 0.85,  # Score actualizado
        "sentiment": "positive",
        "stage": "closing",  # Stage cambiado
        "conversation_summary": "Cliente muy interesado | Listo para demo | Alta prioridad",
    }

    print(f"\n[DATA] Datos actualizados:")
    print(f"   Email: {user_data['email']} (NUEVO)")
    print(f"   Needs: {user_data['needs']} (ACTUALIZADO)")
    print(f"   Pain Points: {user_data['pain_points']} (ACTUALIZADO)")
    print(f"   Budget: {user_data['budget']} (ACTUALIZADO)")
    print(f"   Intent Score: {user_data['intent_score']} (ACTUALIZADO)")
    print(f"   Stage: {user_data['stage']} (CAMBIADO)")
    print(f"   Notes: {user_data['conversation_summary']} (ACTUALIZADO)")

    print(f"\n[SYNC] Actualizando contacto {existing_contact_id}...")

    result = await hubspot.sync_contact(user_data, db_user=mock_user)

    if result:
        print(f"\n[SUCCESS] EXITO: {result['action'].upper()}")
        print(f"   Contact ID: {result['contact_id']}")
        print(f"   Lifecycle Stage: {result.get('lifecyclestage', 'N/A')}")
    else:
        print(f"\n[ERROR] FALLO: No se pudo actualizar el contacto")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("HUBSPOT CRM SYNC - TEST SUITE")
    print("=" * 60)

    # Check if HubSpot is configured
    token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not token:
        print("\n[ERROR] HUBSPOT_ACCESS_TOKEN not found in .env")
        print("\nPara ejecutar este test:")
        print("1. Agregar HUBSPOT_ACCESS_TOKEN a tu archivo .env")
        print("2. Los campos personalizados se crean automaticamente si no existen:")
        print("   - intent_score (Number)")
        print("   - sentiment (Dropdown)")
        print("   - needs (Textarea)")
        print("   - pain_points (Textarea)")
        print("   - budget (Text)")
        print("\nVer HUBSPOT_SETUP.md para instrucciones completas.")
        return

    print(f"\n[OK] HubSpot Access Token configurado")
    print(f"   Token: {token[:10]}...{token[-10:]}")

    # Test 1: Create
    result = await test_create_contact()

    if result:
        contact_id = result["contact_id"]

        # Wait a bit
        print(f"\n[WAIT] Esperando 2 segundos...")
        await asyncio.sleep(2)

        # Test 2: Update
        await test_update_contact(contact_id)

    print("\n" + "=" * 60)
    print("TESTS COMPLETADOS")
    print("=" * 60)
    print("\n[INFO] Verifica en HubSpot:")
    print("   1. Ir a Contacts")
    print("   2. Buscar: +5491112345678_PRUEBA")
    print("   3. Verificar que TODOS los campos esten correctos:")
    print("      - Name, Email, Phone")
    print("      - Needs, Pain Points, Budget")
    print("      - Intent Score, Sentiment")
    print("      - Lifecycle Stage")
    print("      - Notes (hs_content_membership_notes)")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
