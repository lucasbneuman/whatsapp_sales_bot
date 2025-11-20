"""LangGraph workflow compilation and execution."""

from typing import Any, Dict

from langgraph.graph import StateGraph, END

from graph.state import ConversationState
from graph.nodes import (
    welcome_node,
    intent_classifier_node,
    sentiment_analyzer_node,
    data_collector_node,
    router_node,
    conversation_node,
    closing_node,
    payment_node,
    follow_up_node,
    handoff_node,
    summary_node,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


def create_sales_graph():
    """
    Create and compile the sales conversation graph.

    Flow:
    1. welcome_node (if first message)
    2. intent_classifier_node (always)
    3. sentiment_analyzer_node (always)
    4. data_collector_node (always)
    5. router_node (decides next step)
        → conversation_node (default)
        → closing_node (high intent)
        → payment_node (ready to pay)
        → follow_up_node (leaving)
        → handoff_node (needs attention)
    6. END

    Returns:
        Compiled StateGraph
    """
    logger.info("Creating sales conversation graph")

    # Initialize graph
    workflow = StateGraph(ConversationState)

    # Add all nodes
    workflow.add_node("welcome", welcome_node)
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("sentiment_analyzer", sentiment_analyzer_node)
    workflow.add_node("data_collector", data_collector_node)
    workflow.add_node("conversation", conversation_node)
    workflow.add_node("closing", closing_node)
    workflow.add_node("payment", payment_node)
    workflow.add_node("follow_up", follow_up_node)
    workflow.add_node("handoff", handoff_node)
    workflow.add_node("summary", summary_node)

    # Set entry point
    workflow.set_entry_point("welcome")

    # Define edges (sequential analysis pipeline)
    workflow.add_edge("welcome", "intent_classifier")
    workflow.add_edge("intent_classifier", "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "data_collector")

    # Conditional routing from data_collector
    workflow.add_conditional_edges(
        "data_collector",
        router_node,  # Router function determines next node
        {
            "conversation": "conversation",
            "closing": "closing",
            "payment": "payment",
            "follow_up": "follow_up",
            "handoff": "handoff",
        },
    )

    # End points
    workflow.add_edge("conversation", END)
    workflow.add_edge("closing", "payment")  # Closing leads to payment
    workflow.add_edge("payment", "summary")  # Generate summary after payment
    workflow.add_edge("follow_up", "summary")  # Generate summary after follow-up
    workflow.add_edge("summary", END)  # Summary leads to end
    workflow.add_edge("handoff", END)

    # Compile graph
    graph = workflow.compile()

    logger.info("Sales conversation graph compiled successfully")

    return graph


# Global graph instance
sales_graph = None


def get_sales_graph():
    """Get the compiled sales graph instance."""
    global sales_graph
    if sales_graph is None:
        sales_graph = create_sales_graph()
    return sales_graph


async def process_message(
    user_phone: str,
    message: str,
    conversation_history: list,
    config: Dict[str, Any],
    db_session: Any = None,
) -> Dict[str, Any]:
    """
    Process a user message through the sales graph.

    Args:
        user_phone: User's phone number
        message: User's message text
        conversation_history: List of previous messages (BaseMessage objects)
        config: Configuration dict
        db_session: Database session for CRUD operations

    Returns:
        Updated state dict with response
    """
    logger.info(f"Processing message from {user_phone}")

    from langchain_core.messages import HumanMessage

    # Get graph
    graph = get_sales_graph()

    # Prepare initial state
    initial_state: ConversationState = {
        "messages": conversation_history + [HumanMessage(content=message)],
        "user_phone": user_phone,
        "user_name": None,  # Will be populated from DB or extracted
        "user_email": None,
        "intent_score": 0.0,
        "sentiment": "neutral",
        "stage": "welcome",
        "conversation_mode": "AUTO",
        "collected_data": {},
        "payment_link_sent": False,
        "follow_up_scheduled": None,
        "follow_up_count": 0,
        "current_response": None,
        "config": config,
        "db_session": db_session,
    }

    try:
        # Execute graph
        result = await graph.ainvoke(initial_state)

        logger.info("Graph execution completed successfully")

        return result

    except Exception as e:
        import traceback
        logger.error(f"Error executing graph: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return fallback response
        return {
            **initial_state,
            "current_response": "I apologize, I'm having trouble responding right now. Could you please try again?",
        }
