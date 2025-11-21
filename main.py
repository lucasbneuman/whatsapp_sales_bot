"""Main application combining FastAPI webhook and Gradio UI.

This allows running both:
- WhatsApp webhook (FastAPI) for receiving messages from Twilio
- Gradio UI for monitoring conversations in real-time

Both share the same database, so Gradio shows WhatsApp conversations in real-time.
"""

import os
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import gradio as gr

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from whatsapp_webhook import handle_whatsapp_webhook
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""
    # Startup
    logger.info("Starting application...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp Sales Bot",
    description="Webhook + UI for WhatsApp AI Sales Bot",
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "WhatsApp Sales Bot",
        "version": "1.1.0",
        "endpoints": {
            "webhook": "/webhook/whatsapp",
            "gradio_ui": "/gradio (auto-redirects)",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "whatsapp-sales-bot"}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Webhook endpoint for Twilio WhatsApp messages.

    Configure in Twilio Console:
    Webhook URL: https://your-app.onrender.com/webhook/whatsapp
    Method: POST
    """
    result = await handle_whatsapp_webhook(request, AsyncSessionLocal)
    return JSONResponse(content=result)


# Import Gradio demo from app.py
# Note: We import at module level to avoid running demo.launch()
import sys
import importlib.util

# Load app.py without executing the __main__ block
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

# Get the demo instance
demo = app_module.demo

logger.info("Gradio UI loaded successfully")

# Mount Gradio app to FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# Note: Gradio will be available at root path "/"
# FastAPI endpoints are still available at their paths


if __name__ == "__main__":
    import uvicorn

    # Get host and port from environment (for production platforms like Render)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))

    logger.info("="*60)
    logger.info("Starting WhatsApp Sales Bot (FastAPI + Gradio)")
    logger.info("="*60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Gradio UI: http://localhost:{port}/")
    logger.info(f"WhatsApp Webhook: http://localhost:{port}/webhook/whatsapp")
    logger.info(f"Health Check: http://localhost:{port}/health")
    logger.info("="*60)

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
