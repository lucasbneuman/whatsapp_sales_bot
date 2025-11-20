"""Main FastAPI application with Gradio integration."""

import os
from contextlib import asynccontextmanager

import gradio as gr
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from gradio_ui.interface import create_gradio_interface
from services.llm_service import LLMService, llm_service
from services.tts_service import TTSService, tts_service
from services.rag_service import RAGService, rag_service
from services.twilio_service import TwilioService, twilio_service
from services.config_manager import ConfigManager, config_manager
from services.hubspot_sync import HubSpotService, hubspot_service
from services.scheduler_service import SchedulerService, scheduler_service
from utils.logging_config import setup_logging, get_logger
from whatsapp_webhook import handle_whatsapp_webhook

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sales_bot.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session():
    """Database session factory."""
    async with AsyncSessionLocal() as session:
        yield session


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    logger.info("Starting application...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Initialize services
    global llm_service, tts_service, rag_service, twilio_service
    global config_manager, hubspot_service, scheduler_service

    llm_service = LLMService()
    tts_service = TTSService()
    rag_service = RAGService()

    try:
        twilio_service = TwilioService()
    except ValueError as e:
        logger.warning(f"Twilio service not initialized: {e}")
        twilio_service = None

    config_manager = ConfigManager()
    hubspot_service = HubSpotService()
    scheduler_service = SchedulerService(database_url=DATABASE_URL)

    # Initialize default configurations
    async with AsyncSessionLocal() as db:
        await config_manager.initialize_defaults(db)

    logger.info("All services initialized")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    if scheduler_service:
        scheduler_service.shutdown()
    logger.info("Application shut down")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="WhatsApp Sales Bot",
    description="Conversational sales bot with LangGraph and Gradio",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp Sales Bot API",
        "status": "running",
        "endpoints": {
            "webhook": "/webhook/whatsapp",
            "gradio": "/gradio",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "database": "ok",
            "llm": "ok" if llm_service else "not initialized",
            "twilio": "ok" if twilio_service else "not configured",
            "scheduler": "ok" if scheduler_service else "not initialized",
        },
    }


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp webhook endpoint.

    Receives incoming messages and processes them.
    """
    logger.info("WhatsApp webhook called")

    result = await handle_whatsapp_webhook(request, AsyncSessionLocal)

    return JSONResponse(content=result)


# ============================================================================
# GRADIO INTERFACE MOUNT
# ============================================================================

# Create Gradio interface
gradio_interface = create_gradio_interface(AsyncSessionLocal)

# Mount Gradio app
app = gr.mount_gradio_app(app, gradio_interface, path="/gradio")

logger.info("Gradio interface mounted at /gradio")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Gradio UI available at: http://{host}:{port}/gradio")
    logger.info(f"Twilio webhook URL: http://{host}:{port}/webhook/whatsapp")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true",
    )
