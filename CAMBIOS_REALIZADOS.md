# Cambios Realizados - WhatsApp Sales Bot

## 📋 Estado Actual del Proyecto

### ✅ Sistema Base (Completado)
- ✅ Gradio UI v2 con 3 pestañas principales (Chats, Configuración, Pruebas)
- ✅ LangGraph workflow completo con nodos de conversación
- ✅ Integración con OpenAI (GPT-4o y GPT-4o-mini)
- ✅ Sistema de configuración con base de datos SQLite
- ✅ RAG con ChromaDB para documentos
- ✅ TTS con OpenAI
- ✅ Sistema de prompts adaptables a producto/servicio

### ✅ Configuración Mejorada (Completado)
- ✅ Reorganización en 2 pestañas:
  - 🤖 Chatbot: Configuración del comportamiento
  - 📦 Producto/Servicio: Información del producto
  - 📚 Base de Conocimientos: Carga de documentos (TXT, PDF, DOC, DOCX)
- ✅ Prompts se adaptan automáticamente según producto configurado
- ✅ System prompt enriquecido con contexto de producto

### ✅ Datos Recolectados Compactos (Completado)
- ✅ Formato compacto: `📝 Nombre: Valor` en una sola línea
- ✅ Campo "Último contacto" agregado
- ✅ Campos: Nombre, Email, Teléfono, Último contacto, Intención, Sentimiento, Etapa, Necesidades

### ✅ Sistema RAG (Completado)
- ✅ Carga múltiple de archivos (TXT, PDF, DOC, DOCX)
- ✅ Estadísticas de fragmentos indexados
- ✅ Opción para limpiar base de conocimientos
- ✅ Integración con ChromaDB

---

## 🔧 Tareas en Progreso - Sprint Actual

### 1. Configuración - Ajustes
- [ ] Cambiar rango "Máximo de Palabras por Respuesta" a 5-200
- [ ] Eliminar checkbox "Habilitar RAG" (siempre activo si hay archivos)
- [ ] Agregar campo "Mensaje de Bienvenida" personalizado en configuración

### 2. Comportamiento del Chatbot - Core
- [ ] Corregir uso de emojis (no se están usando actualmente)
- [ ] Implementar división de mensajes en partes:
  - Si respuesta ≥20 palabras y multi_part activo
  - Dividir en 3 partes máximo: intro + respuesta + pregunta final
- [ ] Implementar flujo de bienvenida:
  - Primero enviar mensaje de bienvenida
  - Hacer preguntas iniciales: nombre, necesidades, expectativas

### 3. Datos Recolectados - Mejoras
- [ ] Agregar "ID de Usuario" único
- [ ] Hacer el teléfono editable (actualmente fijo en +1234567890)
- [ ] Agregar campo "Notas": resumen después de calificar/avanzar/enviar link
- [ ] Agregar flag "Solicita Humano":
  - Detectar cuando usuario pide hablar con persona
  - Responder: "Si claro, dame unos minutos que aviso a mi supervisor, mientras tanto te gustaría saber más sobre..."
  - Marcar en datos recolectados

### 4. Testing y Validación
- [ ] Probar todos los cambios de configuración
- [ ] Validar división de mensajes con diferentes longitudes
- [ ] Probar detección de solicitud de humano
- [ ] Verificar que emojis funcionen correctamente
- [ ] Probar actualización de datos recolectados

---

## 📝 Notas Técnicas

### Comportamiento de Multi-part Messages
- **Condición**: Respuesta ≥20 palabras Y multi_part_messages=true
- **División**: 3 partes máximo
  1. Intro/saludo
  2. Contenido principal
  3. Pregunta de cierre
- **Ubicación**: `services/llm_service.py` método `generate_response()`

### RAG - Siempre Activo
- Eliminar checkbox de UI
- Lógica: Si `rag_service.get_collection_stats()['total_chunks'] > 0` → usar RAG
- Ubicación: `graph/nodes.py` método `conversation_node()`

### Emojis
- Verificar flag `use_emojis` se pasa correctamente
- Ubicación: `services/llm_service.py` y `graph/nodes.py`

### ID de Usuario
- Generar UUID único en `gradio_app_v2.py`
- Mantener durante toda la sesión de prueba
- Formato: `user_XXXXXXXX`

---

## 🚀 Próximos Pasos (Post-Sprint)

1. **Integración con WhatsApp Real**
   - Conectar Twilio webhook
   - Probar flujo completo con números reales

2. **Sincronización CRM**
   - HubSpot sync para contactos
   - Enviar "Notas" al CRM
   - Sync de flag "Solicita Humano"

3. **Analytics y Métricas**
   - Dashboard de conversaciones
   - Métricas de conversión
   - Análisis de sentimiento agregado

4. **Optimizaciones**
   - Mejorar velocidad de respuesta
   - Reducir tokens de OpenAI
   - Cache de embeddings

---

## 📌 Decisiones de Diseño

### ¿Por qué eliminar checkbox RAG?
- Simplifica UX: menos opciones para configurar
- Comportamiento intuitivo: si subes documentos, se usan automáticamente
- Evita confusión: usuario no necesita "activar" nada

### ¿Por qué 3 partes para mensajes?
- Simula conversación humana más natural
- No satura al usuario con texto largo
- Mantiene engagement con preguntas intermedias

### ¿Por qué campo "Notas"?
- Preparación para CRM sync
- Contexto para handoff humano
- Auditoría de conversaciones

---

## 🔧 Sprint Actual - Mejoras Post-Testing Round 2

### Bugs Detectados en Pruebas (Round 2)

1. **Audio no funciona con ratio 100% en UI de Pruebas**
   - ❌ Configurado text_audio_ratio al 100% pero solo responde con texto
   - ℹ️ NOTA: Limitación de Gradio Chatbot - no soporta audio en mensajes
   - ✅ Audio TTS funciona correctamente en WhatsApp real (Twilio)
   - 📋 Para testing: Implementar componente Audio separado (futuro)

2. **Preview de voces TTS**
   - ❌ No se puede escuchar la voz antes de elegir
   - ✅ Agregar botón de preview para cada voz en configuración

3. **Notas de baja calidad**
   - ❌ Formato simple, concatenación de strings
   - ✅ Usar GPT-4 mini para generar resumen inteligente en hitos importantes

4. **Recolección de datos podría mejorar**
   - ❌ Ya usa GPT-4 mini pero podría ser más preciso
   - ✅ Mejorar prompt de extracción de datos

5. **Mensajes multiparte no se separan en UI**
   - ❌ Backend divide correctamente pero Gradio los muestra juntos
   - ❌ [PAUSA] aún visible en algunos casos
   - ✅ Revisar lógica de proceso_chat_with_data

6. **Rango máximo de palabras limitado**
   - ❌ Actualmente 5-200
   - ✅ Cambiar a 5-500

---

## 🔧 Sprint Anterior - Correcciones Post-Testing

### Bugs Detectados en Pruebas (Round 1)

1. **Bot no hace preguntas iniciales**
   - ❌ Solo responde, no pregunta nombre, necesidades, expectativas
   - ✅ Debe preguntar activamente en welcome_node

2. **No registra datos del usuario**
   - ❌ Nombre y email no se capturan en proceso_chat_with_data
   - ❌ Teléfono no se actualiza
   - ✅ Debe extraer datos en CADA mensaje del usuario

3. **Bot dice que no maneja información**
   - ❌ Responde "No, yo no manejo información personal"
   - ✅ System prompt debe indicar que SÍ recolecta datos para mejorar experiencia

4. **Mensajes multiparte muestran [PAUSA]**
   - ❌ No se envían como mensajes separados
   - ❌ Se muestra el texto literal "[PAUSA]"
   - ✅ Debe implementarse en Gradio para enviar múltiples mensajes

5. **Notas poco completas**
   - ❌ Solo captura datos básicos
   - ✅ Crear nodo especializado para generar notas detalladas

6. **Error al solicitar humano**
   - ❌ Error: 'NoneType' object is not subscriptable
   - ✅ Revisar router_node y handoff_node

7. **User ID sin prefijos**
   - ❌ Genera solo "user_XXXXXXXX"
   - ✅ Debe usar USR_00XXXXXX (PRD) o USRPRUEBAS_00XXXXXX (testing)

### Tareas Pendientes

- [ ] Modificar welcome_node para hacer preguntas iniciales (nombre, necesidades, expectativas)
- [ ] Corregir system_prompt para indicar recolección de datos
- [ ] Mejorar extracción de datos en process_chat_with_data (nombre, email, teléfono en cada mensaje)
- [ ] Implementar envío de mensajes multiparte en Gradio (separar por [PAUSA] y enviar múltiples respuestas)
- [ ] Crear notes_generator_node para generar resúmenes detallados
- [ ] Arreglar error de handoff_node (revisar conversación mode None)
- [ ] Implementar prefijos de User ID (detectar entorno PRD vs testing)

---

## 🐛 Bugs Corregidos (Sprint Anterior)

1. ✅ **Emojis no se usan**: Flag ahora se aplica correctamente con instrucciones explícitas al LLM
2. ✅ **Teléfono fijo**: Campo ahora es editable en UI
3. ✅ **Multi-part implementado**: División en 3 partes cuando ≥20 palabras

---

**Última actualización**: 2025-11-20
**Versión actual**: v2.2-dev
