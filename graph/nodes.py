"""LangGraph nodes for sales conversation workflow."""

from datetime import datetime, timedelta
from typing import Dict, Any

from langchain_core.messages import AIMessage, HumanMessage

from graph.state import ConversationState
from services.llm_service import get_llm_service
from services.rag_service import get_rag_service
from services.hubspot_sync import get_hubspot_service
from utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_enhanced_system_prompt(config: Dict[str, Any]) -> str:
    """
    Build an enhanced system prompt that includes product/service information.

    Args:
        config: Configuration dictionary with system_prompt and product info

    Returns:
        Enhanced system prompt string
    """
    base_prompt = config.get("system_prompt", "You are a friendly sales assistant.")

    # Get product information
    product_name = config.get("product_name", "").strip()
    product_description = config.get("product_description", "").strip()
    product_features = config.get("product_features", "").strip()
    product_benefits = config.get("product_benefits", "").strip()
    product_price = config.get("product_price", "").strip()
    product_target = config.get("product_target_audience", "").strip()

    # If no product info is available, return base prompt
    if not product_name and not product_description:
        return base_prompt

    # Build enhanced prompt with product context
    enhanced_prompt = f"{base_prompt}\n\n"
    enhanced_prompt += "=== INFORMACIÓN DEL PRODUCTO/SERVICIO ===\n"

    if product_name:
        enhanced_prompt += f"Producto/Servicio: {product_name}\n"

    if product_description:
        enhanced_prompt += f"\nDescripción:\n{product_description}\n"

    if product_features:
        enhanced_prompt += f"\nCaracterísticas principales:\n{product_features}\n"

    if product_benefits:
        enhanced_prompt += f"\nBeneficios para el cliente:\n{product_benefits}\n"

    if product_price:
        enhanced_prompt += f"\nPrecio: {product_price}\n"

    if product_target:
        enhanced_prompt += f"\nPúblico objetivo: {product_target}\n"

    enhanced_prompt += "\n=== INSTRUCCIONES ===\n"
    enhanced_prompt += "Usa esta información para responder preguntas sobre el producto/servicio de manera natural y conversacional. "
    enhanced_prompt += "NO menciones que tienes esta información directamente, simplemente úsala para dar respuestas precisas y útiles."

    return enhanced_prompt


# ============================================================================
# NODE 1: WELCOME
# ============================================================================


async def welcome_node(state: ConversationState) -> Dict[str, Any]:
    """
    Generate warm welcome message for new conversations.

    Uses GPT-4o for high-quality, personalized greeting.
    Includes product/service information if available.
    """
    logger.info("Executing welcome_node")

    llm_service = get_llm_service()

    # Check if this is first message
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if len(user_messages) <= 1:
        # Generate welcome message with product context
        enhanced_prompt = build_enhanced_system_prompt(state["config"])
        welcome_prompt = f"{enhanced_prompt}\n\nGenera un mensaje de bienvenida cálido y breve (máximo 2-3 oraciones) para un nuevo cliente que se comunica por WhatsApp."

        response = await llm_service.generate_response(
            messages=[HumanMessage(content=welcome_prompt)],
            system_prompt=enhanced_prompt,
            use_emojis=state["config"].get("use_emojis", True),
        )

        return {
            "current_response": response,
            "stage": "welcome",
        }

    # Not first message, skip welcome
    return {}


# ============================================================================
# NODE 2: INTENT CLASSIFIER
# ============================================================================


async def intent_classifier_node(state: ConversationState) -> Dict[str, Any]:
    """
    Classify user intent and update intent score.

    Runs on EVERY turn. Uses GPT-4o-mini for efficiency.
    """
    logger.info("Executing intent_classifier_node")

    llm_service = get_llm_service()

    # Get last user message
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if not user_messages:
        return {}

    last_message = user_messages[-1].content

    # Classify intent
    intent_data = await llm_service.classify_intent(last_message, state["messages"])

    logger.info(f"Intent: {intent_data['category']}, Score: {intent_data['score']}")

    return {
        "intent_score": intent_data["score"],
    }


# ============================================================================
# NODE 3: SENTIMENT ANALYZER
# ============================================================================


async def sentiment_analyzer_node(state: ConversationState) -> Dict[str, Any]:
    """
    Analyze sentiment of user's message.

    Runs on EVERY turn. Uses GPT-4o-mini for efficiency.
    Triggers handoff if negative sentiment persists.
    """
    logger.info("Executing sentiment_analyzer_node")

    llm_service = get_llm_service()

    # Get last user message
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if not user_messages:
        return {}

    last_message = user_messages[-1].content

    # Analyze sentiment
    sentiment = await llm_service.analyze_sentiment(last_message)

    logger.info(f"Sentiment: {sentiment}")

    # Check for consecutive negative sentiments
    updates = {"sentiment": sentiment}

    # If negative and previous was also negative, trigger handoff
    if sentiment == "negative":
        # Count recent negative sentiments
        recent_messages = state["messages"][-4:]  # Last 4 messages
        negative_count = sum(
            1
            for m in recent_messages
            if isinstance(m, HumanMessage) and getattr(m, "metadata", {}).get("sentiment") == "negative"
        )

        if negative_count >= 2:
            logger.warning("Multiple negative sentiments detected, will trigger handoff")
            updates["conversation_mode"] = "NEEDS_ATTENTION"

    return updates


# ============================================================================
# NODE 4: DATA COLLECTOR
# ============================================================================


async def data_collector_node(state: ConversationState) -> Dict[str, Any]:
    """
    Extract structured data from user messages.

    Uses GPT-4o-mini with structured output.
    Does NOT block the sale waiting for complete data.
    """
    logger.info("Executing data_collector_node")

    llm_service = get_llm_service()

    # Get last user message
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if not user_messages:
        return {}

    last_message = user_messages[-1].content

    # Extract data
    extracted_data = await llm_service.extract_data(last_message, state["messages"])

    if extracted_data:
        logger.info(f"Extracted data: {extracted_data}")

        # Merge with existing collected data
        collected_data = state.get("collected_data", {})
        collected_data.update(extracted_data)

        # Update user_name and user_email in state if found
        updates = {"collected_data": collected_data}

        if "name" in extracted_data and not state.get("user_name"):
            updates["user_name"] = extracted_data["name"]

        if "email" in extracted_data and not state.get("user_email"):
            updates["user_email"] = extracted_data["email"]

        # Async sync to HubSpot (non-blocking)
        hubspot_service = get_hubspot_service()
        if hubspot_service.enabled:
            user_data = {
                "phone": state["user_phone"],
                "name": state.get("user_name"),
                "email": state.get("user_email"),
                "intent_score": state.get("intent_score"),
                "sentiment": state.get("sentiment"),
                "stage": state.get("stage"),
            }
            try:
                await hubspot_service.sync_contact(user_data)
            except Exception as e:
                logger.error(f"HubSpot sync failed (non-blocking): {e}")

        return updates

    return {}


# ============================================================================
# NODE 5: ROUTER
# ============================================================================


def router_node(state: ConversationState) -> str:
    """
    Route to next node based on state.

    This is a CONDITIONAL EDGE function, not a regular node.
    Returns the name of the next node to execute.

    Routing logic:
    - If conversation_mode is NEEDS_ATTENTION → handoff_node
    - If intent_score > 0.8 → closing_node
    - If stage == 'closing' and not payment_link_sent → payment_node
    - If user wants to leave / come back later → follow_up_node
    - Otherwise → conversation_node
    """
    logger.info("Executing router_node")

    # Check conversation mode
    if state.get("conversation_mode") == "NEEDS_ATTENTION":
        logger.info("Routing to handoff_node (NEEDS_ATTENTION)")
        return "handoff"

    # Check if negative sentiment triggered handoff
    if state.get("sentiment") == "negative":
        # Check if this should trigger handoff
        user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
        if len(user_messages) >= 2:
            # If last 2 messages were negative, go to handoff
            recent_sentiments = [state.get("sentiment")]  # Current
            if len(recent_sentiments) >= 2 and all(s == "negative" for s in recent_sentiments[-2:]):
                logger.info("Routing to handoff_node (negative sentiment)")
                return "handoff"

    # Check high intent score
    intent_score = state.get("intent_score", 0.0)
    if intent_score > 0.8:
        logger.info(f"Routing to closing_node (intent_score: {intent_score})")
        return "closing"

    # Check if in closing stage and payment link not sent
    if state.get("stage") == "closing" and not state.get("payment_link_sent"):
        logger.info("Routing to payment_node (closing stage)")
        return "payment"

    # Check for leaving intent
    if intent_score < 0.2:
        logger.info("Routing to follow_up_node (low intent / leaving)")
        return "follow_up"

    # Default: continue conversation
    logger.info("Routing to conversation_node (default)")
    return "conversation"


# ============================================================================
# NODE 6: CONVERSATION
# ============================================================================


async def conversation_node(state: ConversationState) -> Dict[str, Any]:
    """
    Generate main conversational response.

    Uses GPT-4o + RAG if enabled.
    Applies all configurations (emojis, tone, system prompt).
    Includes product/service context automatically.
    """
    logger.info("Executing conversation_node")

    llm_service = get_llm_service()
    rag_service = get_rag_service()

    # Get configuration with enhanced product context
    enhanced_prompt = build_enhanced_system_prompt(state["config"])
    use_emojis = state["config"].get("use_emojis", True)
    rag_enabled = state["config"].get("rag_enabled", False)

    # Get last user message for RAG
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    last_message = user_messages[-1].content if user_messages else ""

    # Retrieve RAG context if enabled
    rag_context = None
    if rag_enabled and last_message:
        try:
            rag_context = await rag_service.retrieve_context(last_message, k=3)
            if rag_context:
                logger.info("Retrieved RAG context")
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")

    # Generate response with product-aware prompt
    response = await llm_service.generate_response(
        messages=state["messages"],
        system_prompt=enhanced_prompt,
        use_emojis=use_emojis,
        rag_context=rag_context,
    )

    # Update stage based on conversation
    current_stage = state.get("stage", "welcome")
    if current_stage == "welcome":
        new_stage = "qualifying"
    else:
        new_stage = current_stage

    return {
        "current_response": response,
        "stage": new_stage,
    }


# ============================================================================
# NODE 7: CLOSING
# ============================================================================


async def closing_node(state: ConversationState) -> Dict[str, Any]:
    """
    Handle closing/purchase intent.

    Validates minimum data and routes to payment if ready.
    """
    logger.info("Executing closing_node")

    # Check if we have at least name
    if not state.get("user_name"):
        logger.info("Missing user name, requesting it")
        return {
            "current_response": "¡Perfecto! Me encantaría ayudarte a completar tu compra. ¿Podrías decirme tu nombre primero?",
            "stage": "closing",
        }

    # Ready to send payment
    logger.info("User ready for payment, routing to payment_node")
    return {
        "stage": "closing",
    }


# ============================================================================
# NODE 8: PAYMENT
# ============================================================================


async def payment_node(state: ConversationState) -> Dict[str, Any]:
    """
    Send payment link to customer.

    Marks payment_link_sent and schedules follow-up.
    Uses product context for personalized closing message.
    """
    logger.info("Executing payment_node")

    llm_service = get_llm_service()
    payment_link = state["config"].get("payment_link", "https://example.com/pay")

    # Build product context for closing message
    product_name = state["config"].get("product_name", "nuestro producto")

    # Generate closing message with payment link
    user_data = {
        "name": state.get("user_name", "there"),
        "product_name": product_name,
    }

    response = await llm_service.generate_closing_message(user_data, payment_link)

    return {
        "current_response": response,
        "payment_link_sent": True,
        "stage": "closing",
    }


# ============================================================================
# NODE 9: FOLLOW-UP
# ============================================================================


async def follow_up_node(state: ConversationState) -> Dict[str, Any]:
    """
    Handle follow-up scheduling.

    Strategy:
    - count = 0: Schedule in 2 hours
    - count = 1: Schedule in 24 hours
    - count >= 2: Change to NEEDS_ATTENTION, no automatic follow-up
    """
    logger.info("Executing follow_up_node")

    follow_up_count = state.get("follow_up_count", 0)

    if follow_up_count >= 2:
        logger.info("Max follow-ups reached, escalating to NEEDS_ATTENTION")
        return {
            "current_response": "¡Entendido! No dudes en contactarme cuando estés listo. ¡Estoy aquí para ayudarte!",
            "conversation_mode": "NEEDS_ATTENTION",
            "stage": "follow_up",
        }

    # Schedule follow-up
    if follow_up_count == 0:
        delay_hours = 2
        response = "¡No hay problema! Te contactaré en un par de horas. ¡Tómate tu tiempo!"
    else:  # count == 1
        delay_hours = 24
        response = "¡Por supuesto! Te contactaré mañana. ¡Que tengas un excelente día!"

    scheduled_time = datetime.utcnow() + timedelta(hours=delay_hours)

    logger.info(f"Scheduled follow-up #{follow_up_count + 1} for {scheduled_time}")

    return {
        "current_response": response,
        "follow_up_scheduled": scheduled_time,
        "follow_up_count": follow_up_count + 1,
        "stage": "follow_up",
    }


# ============================================================================
# NODE 10: HANDOFF
# ============================================================================


async def handoff_node(state: ConversationState) -> Dict[str, Any]:
    """
    Hand off conversation to human agent.

    Changes mode to NEEDS_ATTENTION and pauses bot.
    """
    logger.info("Executing handoff_node")

    return {
        "current_response": "Quiero asegurarme de que recibas la mejor ayuda posible. Déjame conectarte con uno de nuestros especialistas que podrá asistirte mejor.",
        "conversation_mode": "NEEDS_ATTENTION",
        "stage": "handoff",
    }


# ============================================================================
# NODE 11: CONVERSATION SUMMARY
# ============================================================================


async def summary_node(state: ConversationState) -> Dict[str, Any]:
    """
    Generate conversation summary when user leaves or reaches milestone.

    Creates summary and syncs to HubSpot.
    """
    logger.info("Executing summary_node")

    llm_service = get_llm_service()
    hubspot_service = get_hubspot_service()

    # Build conversation text
    conversation_text = []
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            conversation_text.append(f"Cliente: {msg.content}")
        elif isinstance(msg, AIMessage):
            conversation_text.append(f"Bot: {msg.content}")

    full_conversation = "\n".join(conversation_text)

    # Generate summary
    summary_prompt = f"""Genera un resumen conciso de esta conversación de ventas.

Conversación:
{full_conversation}

El resumen debe incluir:
1. Tema principal de la conversación
2. Necesidades o intereses del cliente
3. Productos o servicios discutidos
4. Objeciones o preocupaciones mencionadas
5. Próximos pasos o estado actual

Genera SOLO el resumen en formato de párrafo conciso (máximo 150 palabras)."""

    try:
        summary = await llm_service.generate_response(
            messages=[HumanMessage(content=summary_prompt)],
            system_prompt="Eres un asistente que genera resúmenes concisos de conversaciones de ventas.",
            use_emojis=False,
        )

        logger.info(f"Summary generated: {summary[:100]}...")

        # Sync to HubSpot if available
        user_phone = state.get("user_phone", "")
        user_data = {
            "name": state.get("user_name", ""),
            "email": state.get("user_email", ""),
            "phone": user_phone,
            "conversation_summary": summary,
            "intent_score": state.get("intent_score", 0.0),
            "sentiment": state.get("sentiment", "neutral"),
            "stage": state.get("stage", "unknown"),
        }

        try:
            await hubspot_service.sync_contact(user_data)
            logger.info(f"Summary synced to HubSpot for {user_phone}")
        except Exception as e:
            logger.warning(f"Failed to sync to HubSpot: {e}")

        return {
            "conversation_summary": summary,
            "stage": "completed",
        }

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return {
            "conversation_summary": "Error al generar resumen",
        }
