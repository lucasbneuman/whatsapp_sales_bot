# 📱 WhatsApp Sales Bot

Complete conversational sales automation system using WhatsApp, LangGraph, and Gradio.

## 🌟 Features

- **9-Node LangGraph Architecture**: Specialized nodes for intent classification, sentiment analysis, data collection, conversation, closing, payment, follow-ups, and handoffs
- **Intelligent LLM Routing**: Uses GPT-4o for responses and GPT-4o-mini for analysis tasks
- **WhatsApp Integration**: Full Twilio integration for sending/receiving messages
- **Gradio Control Panel**: Beautiful web interface for testing, monitoring, and manual control
- **RAG Support**: Upload documents (PDF, TXT, DOCX) to enhance bot knowledge
- **Text-to-Speech**: OpenAI TTS with 6 voice options
- **HubSpot Sync**: Automatic CRM synchronization (non-blocking)
- **Smart Follow-ups**: Automated follow-up scheduling with 3-tier strategy
- **Manual Handoff**: Seamless transition from bot to human agent
- **Real-time Monitoring**: Live conversation state, intent scores, and sentiment tracking

## 🏗️ Architecture

```
whatsapp-sales-bot/
├── app.py                      # FastAPI + Gradio entry point
├── whatsapp_webhook.py         # Twilio webhook handler
├── requirements.txt
├── .env.example
├── README.md
│
├── graph/                      # LangGraph components
│   ├── state.py               # ConversationState definition
│   ├── nodes.py               # 9 specialized nodes
│   └── workflow.py            # Graph compilation
│
├── services/                   # Business logic layer
│   ├── llm_service.py         # LLM routing (GPT-4o/mini)
│   ├── tts_service.py         # Text-to-speech
│   ├── rag_service.py         # Document RAG
│   ├── twilio_service.py      # WhatsApp messaging
│   ├── config_manager.py      # Configuration management
│   ├── hubspot_sync.py        # CRM synchronization
│   └── scheduler_service.py   # Follow-up scheduling
│
├── database/                   # Data persistence
│   ├── models.py              # SQLAlchemy models
│   └── crud.py                # Database operations
│
├── gradio_ui/                  # Web interface
│   ├── interface.py           # Main layout
│   ├── chat_component.py      # Chat testing
│   ├── data_viewer.py         # Real-time metrics
│   ├── conversations_panel.py # Active conversations
│   └── config_panel.py        # System configuration
│
└── utils/                      # Utilities
    ├── logging_config.py      # Logging setup
    └── helpers.py             # Helper functions
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- OpenAI API key
- Twilio account (for WhatsApp)
- (Optional) HubSpot API key

### 2. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required:
# - OPENAI_API_KEY
# - TWILIO_ACCOUNT_SID
# - TWILIO_AUTH_TOKEN
# - TWILIO_WHATSAPP_NUMBER

# Optional:
# - HUBSPOT_API_KEY (leave empty to disable)
```

### 4. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:8000`

- **Gradio UI**: http://localhost:8000/gradio
- **API Docs**: http://localhost:8000/docs
- **Webhook**: http://localhost:8000/webhook/whatsapp

## 🎮 Using the Gradio Interface

### Chat Testing

1. Navigate to the "Chat Testing" panel (left column)
2. Type messages to simulate customer conversations
3. Watch the bot respond according to configured behavior
4. No WhatsApp integration needed for testing!

### Real-Time Data Viewer

- View live conversation metrics (right column)
- Monitor intent scores (0-1 scale)
- Track sentiment (positive/neutral/negative)
- See current conversation stage
- View collected customer data

### Active Conversations Panel

- See all active WhatsApp conversations
- Filter by mode: 🟢 AUTO | 🔴 MANUAL | ⚠️ NEEDS_ATTENTION
- **Take Control**: Switch conversation to manual mode
- **Manual Messaging**: Send messages directly to customers
- **Return to Bot**: Switch back to automatic mode

### Configuration Panel

#### System Tab
- **System Prompt**: Define bot personality and behavior
- **Payment Link**: URL to send when customer is ready to buy
- **Response Delay**: Simulate typing (0-10 seconds)
- **Use Emojis**: Toggle emoji usage in responses

#### Text-to-Speech Tab
- **Text/Audio Ratio**: 0-49 = text only, 50-100 = text + audio
- **TTS Voice**: Choose from 6 OpenAI voices
  - alloy, echo, fable, onyx, nova, shimmer

#### RAG Tab
- **Upload Documents**: Add PDF, TXT, or DOCX files
- **Enable RAG**: Toggle document-based knowledge
- **Clear Documents**: Remove all uploaded files

#### Deployment Tab
- Quick deployment checklist
- Production readiness verification

## 📞 Twilio WhatsApp Setup

### 1. Configure Twilio Sandbox (Testing)

1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Join your sandbox by sending the code to the Twilio WhatsApp number
3. Copy your credentials to `.env`

### 2. Set Up Webhook (Local Testing with ngrok)

```bash
# Install ngrok
# Download from: https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

3. In Twilio Console → WhatsApp Sandbox → Configuration:
   - Set "When a message comes in" to: `https://abc123.ngrok.io/webhook/whatsapp`
   - Method: POST

### 3. Production Deployment

For production, replace ngrok URL with your deployed domain:
```
https://yourdomain.com/webhook/whatsapp
```

## 🎯 How the Bot Works

### Conversation Flow

1. **Welcome**: Greets new customers warmly (GPT-4o)
2. **Intent Classification**: Analyzes buying intent (GPT-4o-mini)
   - 0.0-0.3: Browsing
   - 0.3-0.6: Interested
   - 0.6-0.9: Ready to buy
3. **Sentiment Analysis**: Tracks customer mood (GPT-4o-mini)
   - Positive / Neutral / Negative
   - Auto-escalates on 2+ negative messages
4. **Data Collection**: Extracts name, email, needs, budget
5. **Routing**: Decides next action based on state
6. **Conversation**: Generates contextual responses (GPT-4o + RAG)
7. **Closing**: Detects buying signals
8. **Payment**: Sends payment link when ready
9. **Follow-up**: Schedules smart follow-ups
   - 1st: 2 hours later
   - 2nd: 24 hours later
   - 3rd+: Escalates to human
10. **Handoff**: Transfers to human when needed

### Sales Philosophy

**"Always Be Closing"** - If customer says "I want to buy":
1. Send payment link IMMEDIATELY
2. Collect missing data AFTER (non-blocking)
3. Never wait for complete information before closing

## 🔄 Follow-up Strategy

The bot uses a 3-tier follow-up system:

1. **First Follow-up** (2 hours)
   - Automatic, friendly check-in
   - "Just checking if you have questions"

2. **Second Follow-up** (24 hours)
   - Automatic, value reminder
   - "Still here to help!"

3. **Third Follow-up** (48+ hours)
   - Escalates to NEEDS_ATTENTION
   - Requires human review
   - No automatic message sent

## 🔐 Security Best Practices

- Never commit `.env` file to git
- Use environment variables for all secrets
- Set `DEBUG=False` in production
- Use HTTPS for webhooks
- Rotate API keys regularly
- Implement rate limiting for production

## 📊 Database Schema

### Users Table
- Phone (unique), name, email
- Intent score, sentiment, stage
- Conversation mode (AUTO/MANUAL/NEEDS_ATTENTION)
- Total messages, last message time

### Messages Table
- User ID (FK), message text, sender (user/bot)
- Timestamp, metadata (JSON)

### FollowUps Table
- User ID (FK), scheduled time, message
- Status (pending/sent/cancelled)
- Follow-up count

### Configs Table
- Key (unique), value (JSON)
- Stores all system configurations

## 🚢 Deployment

### Deploy to Render

1. Create new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`
6. Deploy!

### Environment Variables for Production

Set these in Render dashboard:
```
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=+14155238886
DATABASE_URL=sqlite+aiosqlite:///./sales_bot.db
DEBUG=False
LOG_LEVEL=INFO
```

## 🐛 Troubleshooting

### Bot not responding in WhatsApp

1. Check Twilio webhook is configured correctly
2. Verify ngrok tunnel is running (for local)
3. Check logs: Look for "WhatsApp webhook called"
4. Verify Twilio credentials in `.env`

### Gradio interface not loading

1. Ensure all dependencies installed: `pip install -r requirements.txt`
2. Check port 8000 is not in use
3. Try different port: `PORT=8080 python app.py`

### Database errors

1. Delete `sales_bot.db` and restart (resets database)
2. Check write permissions in directory
3. Verify SQLAlchemy installed correctly

### OpenAI API errors

1. Verify API key is valid
2. Check API quota/billing
3. Test with: `openai api models.list`

## 📝 Customization

### Change Bot Personality

Edit system prompt in Gradio Config Panel or directly in database:
```python
system_prompt = """
You are [YOUR PERSONALITY].
Your goal is [YOUR GOAL].
"""
```

### Add New LangGraph Nodes

1. Define node function in `graph/nodes.py`
2. Add node to workflow in `graph/workflow.py`
3. Update routing logic in `router_node`

### Modify RAG Behavior

Edit `services/rag_service.py`:
- Change chunk size: `chunk_size=1000`
- Adjust overlap: `chunk_overlap=200`
- Modify retrieval count: `k=3`

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Follow existing code style
4. Add tests if applicable
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **LangGraph**: For powerful conversation orchestration
- **OpenAI**: For GPT-4o and embeddings
- **Gradio**: For beautiful UI framework
- **Twilio**: For WhatsApp integration
- **FastAPI**: For robust API framework

## 📞 Support

For issues and questions:
- Open GitHub issue
- Check existing documentation
- Review logs for error messages

---

**Built with ❤️ using LangGraph, OpenAI, and Gradio**

*Happy Selling! 🚀*
