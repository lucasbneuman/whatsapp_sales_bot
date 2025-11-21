# 🤖 WhatsApp Sales Bot

Sistema inteligente de ventas conversacional para WhatsApp con IA, construido con LangGraph, OpenAI y Gradio.

## ✨ Características

### 🎯 Core Features
- **Conversaciones Inteligentes**: Workflow LangGraph con 11 nodos especializados
- **IA Multimodal**: Integración con GPT-4o y GPT-4o-mini
- **Text-to-Speech**: Voces configurables con OpenAI TTS (ratio 0-100%)
- **RAG (Retrieval Augmented Generation)**: ChromaDB para conocimiento empresarial
- **Recolección Inteligente de Datos**: Extracción y validación automática de información del cliente
- **Configuración Dinámica**: Panel completo de configuración en tiempo real
- **Persistencia**: Base de datos SQLite con historial completo por usuario

### 📊 Panel de Control Gradio
- **Chats en Vivo**: Monitoreo de conversaciones activas con datos recolectados
- **Configuración Avanzada**: System prompts, voces TTS, ratio audio/texto
- **Panel de Pruebas**: Simulación de conversaciones con datos en tiempo real
- **Gestión de Documentos**: Upload y gestión de base de conocimiento RAG

### 🔗 Integraciones
- **WhatsApp Business API** (Twilio)
- **HubSpot CRM** - Sincronización automática en tiempo real:
  - Campos estándar: name, email, phone, lifecyclestage
  - Campos personalizados: needs, pain_points, budget, intent_score, sentiment
  - Notas automáticas de conversación
  - Validación de datos antes de sincronizar
- **OpenAI** (GPT-4o, GPT-4o-mini, TTS)
- **ChromaDB** (Vector Store)

---

## 🚀 Quick Start

### 1. Requisitos Previos
- Python 3.11+
- Cuenta OpenAI con API key
- (Opcional) Cuenta Twilio para WhatsApp
- (Opcional) Cuenta HubSpot para CRM

### 2. Instalación

```bash
# Clonar repositorio
git clone https://github.com/lucasbneuman/whatsapp_sales_bot.git
cd whatsapp_sales_bot

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración

Crear archivo `.env` en la raíz del proyecto:

```env
# OpenAI (REQUERIDO)
OPENAI_API_KEY=sk-...

# Base de Datos
DATABASE_URL=sqlite+aiosqlite:///./sales_bot.db

# Twilio WhatsApp (Opcional - para producción)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# HubSpot CRM (Opcional)
HUBSPOT_ACCESS_TOKEN=pat-na1-...

# Logging
LOG_LEVEL=INFO

# Server (Opcional - solo para desarrollo local)
# En producción (Render, Railway, Heroku), PORT se asigna automáticamente
HOST=0.0.0.0
PORT=7860
```

### 4. Ejecución

#### Opción 1: Solo Gradio UI (Testing/Configuración)
```bash
python app.py
```
- Panel de control en `http://localhost:7860`
- Ideal para testing local y configuración

#### Opción 2: WhatsApp + Gradio UI (Producción Completa) ⭐
```bash
python main.py
```
- **Gradio UI**: `http://localhost:7860/`
- **WhatsApp Webhook**: `http://localhost:7860/webhook/whatsapp`
- **Health Check**: `http://localhost:7860/health`
- Las conversaciones de WhatsApp se ven **en tiempo real** en Gradio

**Recomendado para Render/Producción**: `python main.py`

**Nota**: En producción (Render, Railway, Heroku), la plataforma asigna automáticamente el `PORT`. No es necesario configurarlo manualmente.

**Pestañas Gradio disponibles:**
- 💬 **Chats**: Visualización de conversaciones en vivo (incluye WhatsApp)
- ⚙️ **Configuración**: Prompts, voces TTS, documentos RAG
- 🧪 **Pruebas**: Simulador de conversaciones con datos recolectados

---

## 📖 Uso

### Configuración Inicial

1. **System Prompt**: Define la personalidad y objetivo del bot
2. **Información del Producto/Servicio**: Contexto automático para RAG
3. **Voces TTS**: Selecciona voz y ratio audio/texto (0-100%)
4. **Documentos**: Sube PDFs/TXT para conocimiento adicional

### Panel de Pruebas

Simula conversaciones completas y visualiza:
- Datos recolectados (nombre, email, teléfono, necesidades, presupuesto, pain points)
- Intent Score (0-1): Probabilidad de compra
- Sentiment: positive/neutral/negative
- Stage: welcome → qualifying → nurturing → closing → sold
- Notas LLM: Observaciones del asistente
- Historial de mensajes completo

### Integración HubSpot CRM

#### Setup Automático

Los campos personalizados se crean automáticamente en la primera sincronización:
- `intent_score` (Number)
- `sentiment` (Dropdown: positive/neutral/negative)
- `needs` (Textarea)
- `pain_points` (Textarea)
- `budget` (Text)

#### Sincronización en Tiempo Real

El bot sincroniza automáticamente:
1. Extrae datos del cliente (con validación estricta)
2. Valida formato de email, teléfono, etc.
3. Sincroniza a HubSpot (create o update automático)
4. Actualiza notas con resumen de conversación
5. Mapea lifecycle stages:
   - `welcome/qualifying` → lead
   - `nurturing` → marketingqualifiedlead
   - `closing` → salesqualifiedlead
   - `sold` → customer

#### Testing HubSpot

```bash
python test_hubspot.py
```

Ver `HUBSPOT_SETUP.md` para instrucciones detalladas.

---

## 🏗️ Arquitectura

### LangGraph Workflow (11 Nodos)

```
welcome_node
    ↓
intent_classifier_node (GPT-4o-mini: 0-1 score)
    ↓
sentiment_analyzer_node (GPT-4o-mini: positive/neutral/negative)
    ↓
data_collector_node (Extracción + Validación + HubSpot Sync)
    ↓
router_node (Conditional routing)
    ├── conversation_node (GPT-4o + RAG)
    ├── closing_node (High intent)
    ├── payment_node (Ready to buy)
    ├── follow_up_node (Leaving)
    └── handoff_node (Needs attention)
```

### Validación de Datos

**Nombre:**
- ❌ Rechaza saludos: "hola", "buenos días"
- ✅ Capitaliza: "lucas" → "Lucas"

**Email:**
- ✅ Formato válido: `usuario@dominio.com`
- ❌ Rechaza: `usuario@dominio` (sin TLD)

**Teléfono:**
- ✅ Números con formato: `+54 911 1234-5678`
- ✅ Mínimo 7 dígitos
- ❌ Rechaza texto no numérico

**Needs/Pain Points:**
- ✅ Mínimo 5 caracteres
- ✅ Descripciones concretas
- ❌ Rechaza frases vacías

**Budget:**
- ✅ Debe mencionar números o keywords monetarios
- ❌ Rechaza texto sin referencia a dinero

---

## 📁 Estructura del Proyecto

```
whatsapp_sales_bot/
├── app.py                    # Aplicación Gradio principal
├── whatsapp_webhook.py       # Webhook para Twilio WhatsApp
├── requirements.txt          # Dependencias
├── .env                      # Variables de entorno (crear)
├── database/
│   ├── models.py            # SQLAlchemy models
│   ├── crud.py              # Database operations
│   └── database.py          # DB connection
├── graph/
│   ├── state.py             # ConversationState definition
│   ├── nodes.py             # 11 workflow nodes
│   └── workflow.py          # LangGraph compilation
├── services/
│   ├── llm_service.py       # OpenAI GPT + data extraction
│   ├── rag_service.py       # ChromaDB + RAG
│   ├── tts_service.py       # Text-to-Speech
│   └── hubspot_sync.py      # HubSpot CRM sync
├── utils/
│   ├── config_manager.py    # Configuration management
│   └── logging_config.py    # Logging setup
├── HUBSPOT_SETUP.md         # HubSpot integration guide
└── test_hubspot.py          # HubSpot integration test
```

---

## 🧪 Testing

### Test HubSpot Integration

```bash
python test_hubspot.py
```

Verifica:
- ✅ Creación de contactos con todos los campos
- ✅ Actualización de contactos existentes
- ✅ Validación de datos
- ✅ Sincronización de notas

---

## 🔧 Configuración Avanzada

### Modelos OpenAI

- **Intent Classifier**: `gpt-4o-mini` (rápido, económico)
- **Sentiment Analyzer**: `gpt-4o-mini` (rápido, económico)
- **Data Extraction**: `gpt-4o-mini` (structured output)
- **Conversation**: `gpt-4o` (conversación principal)
- **Summary**: `gpt-4o` (resúmenes finales)

### Text-to-Speech

**Voces disponibles:**
- `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

**Ratio Audio/Texto:**
- `0-49%`: Solo texto
- `50%`: 50% probabilidad de audio + texto
- `51-99%`: Probabilidad proporcional
- `100%`: Solo audio (sin texto)

### RAG (ChromaDB)

- **Chunk Size**: 1000 caracteres
- **Chunk Overlap**: 200 caracteres
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Top K Results**: 3 documentos más relevantes

---

## 📝 Roadmap

- [ ] Multi-tenancy (múltiples empresas)
- [ ] Dashboard de analytics
- [ ] A/B testing de prompts
- [ ] Integración con más CRMs (Salesforce, Pipedrive)
- [ ] Soporte para más idiomas
- [ ] Voice input (Speech-to-Text)
- [ ] Integración con calendarios (scheduling)

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration
- [OpenAI](https://openai.com/) - GPT-4o, GPT-4o-mini, TTS
- [Gradio](https://gradio.app/) - UI framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [HubSpot](https://www.hubspot.com/) - CRM integration

---

**Version**: 1.1.0 - HubSpot CRM Integration
**Last Updated**: 2025-11-21
**Author**: Lucas Neuman

🤖 Generated with [Claude Code](https://claude.com/claude-code)
