# 🤖 WhatsApp Sales Bot

Sistema inteligente de ventas conversacional para WhatsApp con IA, construido con LangGraph, OpenAI y Gradio.

## ✨ Características

### 🎯 Core Features
- **Conversaciones Inteligentes**: Workflow LangGraph con 11 nodos especializados
- **IA Multimodal**: Integración con GPT-4o y GPT-4o-mini
- **Text-to-Speech**: Voces configurables con OpenAI TTS (ratio 0-100%)
- **RAG (Retrieval Augmented Generation)**: ChromaDB para conocimiento empresarial
- **Configuración Dinámica**: Panel completo de configuración en tiempo real
- **Persistencia**: Base de datos SQLite con historial completo por usuario

### 📊 Panel de Control Gradio
- **Chats en Vivo**: Monitoreo de conversaciones activas
- **Configuración Avanzada**: System prompts, voces TTS, ratio audio/texto
- **Panel de Pruebas**: Simulación de conversaciones con datos recolectados en tiempo real
- **Gestión de Documentos**: Upload y gestión de base de conocimiento

### 🔗 Integraciones
- WhatsApp Business API (Twilio)
- HubSpot CRM (opcional)
- OpenAI (GPT-4o, GPT-4o-mini, TTS)
- ChromaDB (Vector Store)

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
git clone <tu-repo>
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

# Entorno
ENVIRONMENT=testing  # testing o production

# Base de Datos
DATABASE_URL=sqlite+aiosqlite:///./sales_bot.db

# Twilio WhatsApp (Opcional - para producción)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# HubSpot (Opcional)
HUBSPOT_ACCESS_TOKEN=pat-...

# Logging
LOG_LEVEL=INFO
```

### 4. Ejecución

#### Panel de Control Gradio (Testing)
```bash
python app.py
```

Acceder a: `http://localhost:7860`

#### Webhook WhatsApp (Producción)
```bash
uvicorn whatsapp_webhook:app --host 0.0.0.0 --port 8000
```

---

## 📖 Uso

### Primera Configuración

1. **Ejecutar**: `python app.py`
2. **Acceder**: `http://localhost:7860`
3. **Ir a "⚙️ Configuración"**
4. **Configurar campos obligatorios**:
   - **System Prompt**: Personalidad y objetivo del bot
   - **Mensaje de Bienvenida**: Primer mensaje al usuario
5. **Configurar producto/servicio** (opcional pero recomendado)
6. **Guardar configuración**

⚠️ **Importante**: El bot NO funcionará hasta configurar al menos `system_prompt` y `welcome_message`

### Probar el Bot

1. **Ir a "🧪 Pruebas"**
2. **Escribir mensaje en el chat**
3. **Ver respuesta del bot** (texto y/o audio según configuración)
4. **Observar datos recolectados** (nombre, email, intención, sentimiento, etc.)

### Configuraciones Avanzadas

#### Text/Audio Ratio
- **0-49%**: Solo texto (sin audio)
- **50%**: 50% probabilidad de enviar audio + texto
- **75%**: 75% probabilidad de enviar audio + texto
- **100%**: Solo audio (sin texto)

#### Voces TTS Disponibles
`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

#### Multi-part Messages
Activar para enviar mensajes largos en partes separadas con `[PAUSA]`

#### Límite de Palabras por Respuesta
Configurar máximo de palabras (default: 100)

---

## 🏗️ Arquitectura

### Workflow LangGraph (11 Nodos)

```
1. Welcome Node → Mensaje de bienvenida personalizado
2. Intent Classifier → Clasifica intención de compra (GPT-4o-mini)
3. Sentiment Analyzer → Analiza sentimiento del cliente
4. Data Collector → Extrae datos (nombre, email, necesidades)
5. Router → Decide siguiente paso basado en estado
    ├─→ Conversation Node (conversación general)
    ├─→ Closing Node (alta intención de compra)
    ├─→ Payment Node (listo para pagar)
    ├─→ Follow-up Node (usuario se va)
    └─→ Handoff Node (necesita atención humana)
6. Conversation Node → Respuesta contextual con RAG
7. Closing Node → Manejo de cierre de venta
8. Payment Node → Envío de link de pago
9. Follow-up Node → Programa seguimientos automáticos
10. Handoff Node → Transferencia a humano
11. Summary Node → Genera resumen de conversación
```

### Estructura del Proyecto

```
whatsapp_sales_bot/
├── app.py                      # Aplicación principal Gradio ⭐
├── whatsapp_webhook.py         # Webhook para WhatsApp
├── reset_config.py             # Script para resetear config
├── requirements.txt            # Dependencias
├── .env                        # Variables de entorno (NO commitear)
├── TODO.md                     # Lista de tareas y roadmap
│
├── database/
│   ├── models.py              # Modelos SQLAlchemy (User, Message, Config, FollowUp)
│   └── crud.py                # Operaciones CRUD
│
├── graph/
│   ├── state.py               # Estado del grafo LangGraph
│   ├── nodes.py               # 11 nodos del workflow
│   └── workflow.py            # Compilación y ejecución del grafo
│
├── services/
│   ├── llm_service.py         # Servicio OpenAI (GPT-4o/mini)
│   ├── tts_service.py         # Text-to-Speech con ratio proporcional
│   ├── rag_service.py         # RAG con ChromaDB
│   ├── config_manager.py      # Gestor de configuración dinámica
│   ├── hubspot_sync.py        # Integración HubSpot CRM
│   └── twilio_service.py      # Servicio WhatsApp (Twilio)
│
├── gradio_ui/
│   ├── config_panel_v2.py     # Panel de configuración completo
│   └── live_chats_panel.py    # Panel de chats en vivo
│
└── utils/
    └── logging_config.py       # Configuración de logs
```

---

## 🌐 Deployment en Render

### 1. Preparar Repositorio

```bash
# Inicializar Git (si no está inicializado)
git init

# Agregar archivos
git add .

# Commit
git commit -m "Initial commit: WhatsApp Sales Bot MVP v1.0"

# Agregar remote (reemplazar con tu URL)
git remote add origin https://github.com/tu-usuario/whatsapp-sales-bot.git

# Push
git push -u origin main
```

### 2. Configurar Render

1. Ir a [Render Dashboard](https://dashboard.render.com/)
2. Crear nuevo **Web Service**
3. Conectar repositorio de GitHub
4. Configurar:
   - **Name**: `whatsapp-sales-bot`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py` (para Gradio) o `uvicorn whatsapp_webhook:app --host 0.0.0.0 --port $PORT` (para webhook)
   - **Instance Type**: Starter (gratis)

### 3. Variables de Entorno en Render

Agregar en Render Dashboard → Environment:

```
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
HUBSPOT_ACCESS_TOKEN=pat-...
LOG_LEVEL=INFO
```

### 4. Configurar Webhook de Twilio

Una vez desplegado, copiar URL de Render (ej: `https://whatsapp-sales-bot.onrender.com`)

En Twilio Console:
1. Ir a **Messaging** → **Try it out** → **WhatsApp** → **Sandbox settings**
2. **When a message comes in**: `https://tu-app.onrender.com/webhook/whatsapp`
3. **Method**: POST

---

## 🛠️ Scripts Útiles

### Resetear Configuración a Valores Vacíos
```bash
python reset_config.py
```

### Ver Base de Datos
```bash
# Instalar DB Browser for SQLite
# Abrir: sales_bot.db
```

### Limpiar Base de Datos (Reset Completo)
```bash
rm sales_bot.db
python app.py  # Se creará nueva BD automáticamente
```

---

## 📝 Notas Importantes

### Seguridad
- ⚠️ **NUNCA** commitear `.env` con credenciales (ya está en `.gitignore`)
- ⚠️ Rotar API keys regularmente
- ⚠️ Usar HTTPS en producción (Render lo provee automáticamente)

### Performance
- **SQLite** OK para testing; considerar **PostgreSQL** para producción
- **ChromaDB** puede ser pesado; evaluar alternativas si es necesario
- Implementar **rate limiting** en producción

### Límites de OpenAI
- **GPT-4o**: ~128k tokens de contexto
- **TTS**: Límites de caracteres por request
- **Revisar costos** regularmente en OpenAI Dashboard

### Diferencia Testing vs Producción
- **Testing**: User IDs con prefijo `USRPRUEBAS_`
- **Production**: User IDs con prefijo `USR_`
- Controlar con variable `ENVIRONMENT` en `.env`

---

## 🐛 Troubleshooting

### Bot no responde en Gradio
1. Verificar que `system_prompt` y `welcome_message` estén configurados
2. Revisar logs en consola
3. Verificar que OpenAI API key sea válida

### Bot envía solo texto (no audio) con ratio 100%
1. Verificar que `text_audio_ratio` esté en 100
2. Revisar logs: Debe mostrar "🔊 Generating TTS audio"
3. Verificar saldo de OpenAI (TTS consume créditos)

### Error de ChromaDB en Render
1. ChromaDB requiere dependencias del sistema
2. Agregar `apt-packages.txt` en Render si es necesario
3. Considerar deshabilitar RAG temporalmente

### Webhook de WhatsApp no responde
1. Verificar URL del webhook en Twilio
2. Revisar logs de Render
3. Probar manualmente con Postman/curl

---

## 🤝 Contribuir

Revisar `TODO.md` para ver tareas pendientes y roadmap.

---

## 📄 Licencia

Este proyecto es privado y confidencial.

---

## 📞 Soporte

Para preguntas o issues:
- Revisar `TODO.md`
- Contactar al equipo de desarrollo

---

**Versión**: MVP v1.0
**Última actualización**: 2025-11-21
**Built with**: LangGraph + OpenAI + Gradio 🚀
