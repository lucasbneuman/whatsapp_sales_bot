# Testing Checklist - WhatsApp Sales Bot v2.2

**Versión:** v2.2-pre-testing
**Fecha:** 2025-11-20
**Tag Git:** v2.2-pre-testing

---

## 🧪 Funcionalidades a Probar

### 1. Configuración UI

#### Tab: Chatbot
- [ ] System Prompt se guarda correctamente
- [ ] Mensaje de Bienvenida se guarda correctamente
- [ ] Payment Link se guarda
- [ ] Response Delay se guarda (0-10 minutos)
- [ ] Máximo de Palabras por Respuesta (5-500)
- [ ] Checkbox "Usar Emojis" funciona
- [ ] Checkbox "Mensajes en Múltiples Partes" funciona
- [ ] Dropdown "Voz TTS" se guarda
- [ ] Radio selector de voces muestra las 6 opciones
- [ ] Botón "🔊 Escuchar Voz" genera preview de audio
- [ ] Audio preview se reproduce automáticamente

#### Tab: Producto/Servicio
- [ ] Product Name se guarda
- [ ] Product Description se guarda
- [ ] Product Features se guarda
- [ ] Product Benefits se guarda
- [ ] Product Price se guarda
- [ ] Product Target Audience se guarda

#### Tab: Base de Conocimientos
- [ ] Subida de archivos TXT funciona
- [ ] Subida de archivos PDF funciona
- [ ] Estadísticas de fragmentos se actualizan
- [ ] Botón "Limpiar Base de Conocimientos" funciona
- [ ] Estado muestra mensaje de éxito/error

---

### 2. Chat de Prueba

#### Welcome Message
- [ ] Primer mensaje usa el mensaje de bienvenida personalizado
- [ ] Incluye pregunta inicial: "¿Podrías decirme tu nombre?"
- [ ] Usa emojis si está activado

#### Recolección de Datos
- [ ] Nombre se detecta ("me llamo Lucas")
- [ ] Nombre se detecta (mensaje corto con mayúscula: "Lucas")
- [ ] Email se detecta (regex pattern)
- [ ] Teléfono se detecta (con keywords: "mi teléfono es")
- [ ] Teléfono se detecta (solo números largos: "43517455086")
- [ ] Intención se clasifica correctamente
- [ ] Sentimiento se analiza correctamente
- [ ] Etapa se actualiza según la conversación

#### Datos Recolectados Panel
- [ ] User ID se genera con formato correcto (USRPRUEBAS_XXXXXXXX)
- [ ] Nombre se actualiza en tiempo real
- [ ] Email se actualiza en tiempo real
- [ ] Teléfono se actualiza en tiempo real (editable)
- [ ] Último contacto muestra fecha/hora actual
- [ ] Intención se actualiza
- [ ] Sentimiento se actualiza
- [ ] Etapa se actualiza
- [ ] Necesidades se capturan
- [ ] Flag "Solicita Humano" se activa correctamente

#### Notas con GPT-4 Mini
- [ ] Se generan notas en etapa Cierre
- [ ] Se generan notas cuando se solicita humano
- [ ] Se generan notas después de 10+ mensajes
- [ ] Notas son resumen inteligente (no concatenación)
- [ ] Formato profesional (3-4 oraciones)

#### Mensajes Multiparte
- [ ] Con multi_part_messages=true y ≥20 palabras se divide
- [ ] Respuesta se divide en máximo 3 partes
- [ ] NO se muestra texto "[PAUSA]" en UI
- [ ] Cada parte aparece como mensaje separado del bot

#### Solicitud de Humano
- [ ] Detecta "quiero hablar con un humano"
- [ ] Detecta "necesito ayuda de una persona"
- [ ] Detecta "quiero hablar con alguien"
- [ ] Responde: "¡Claro que sí! 😊 Dame unos minutos..."
- [ ] NO genera error (NoneType)
- [ ] Marca flag "Solicita Humano: Sí"

#### RAG (Base de Conocimientos)
- [ ] Si hay documentos cargados, RAG se activa automáticamente
- [ ] Respuestas usan información de los documentos
- [ ] Log muestra: "Retrieved RAG context (X chunks available)"

#### System Prompt
- [ ] Bot confirma que recolecta datos cuando usuario comparte info
- [ ] No dice "No manejo información personal"
- [ ] Agradece cuando recibe nombre/email/teléfono

---

### 3. Comportamiento del Bot

#### Emojis
- [ ] Con use_emojis=true, usa emojis en respuestas
- [ ] Con use_emojis=false, NO usa emojis

#### Límite de Palabras
- [ ] Con max_words=30, respuestas son cortas (~30 palabras)
- [ ] Con max_words=200, respuestas pueden ser largas
- [ ] Con max_words=500, respuestas muy detalladas

---

## 🐛 Bugs Conocidos (a verificar si persisten)

1. **Audio TTS en UI de Pruebas**
   - Limitación de Gradio Chatbot
   - Audio funciona en WhatsApp real (Twilio)

---

## 📋 Resultados de Pruebas

### ✅ Funcionalidades que Funcionan Correctamente

_(Se completará después de las pruebas)_

---

### ❌ Funcionalidades con Problemas

_(Se completará después de las pruebas)_

---

## 🔧 Acciones Correctivas

_(Se completará después de identificar problemas)_
