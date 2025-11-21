# TODO - WhatsApp Sales Bot

## 📋 Tareas Completadas ✅

### MVP v1.0 - Funcionalidades Core
- ✅ Sistema de configuración dinámica (Config Manager)
- ✅ Workflow LangGraph completo con 11 nodos
- ✅ Integración con OpenAI (GPT-4o y GPT-4o-mini)
- ✅ Sistema RAG con ChromaDB
- ✅ Text-to-Speech con voces configurables
- ✅ Panel de configuración Gradio v2
- ✅ Panel de chats en vivo
- ✅ Panel de pruebas con datos recolectados
- ✅ Persistencia en base de datos SQLite
- ✅ Integración con HubSpot (opcional)
- ✅ Sistema de follow-ups automáticos
- ✅ Detección de solicitud de humano
- ✅ Generación de notas con LLM
- ✅ Validación de configuración vacía
- ✅ Lógica de audio proporcional (0-100%)
- ✅ Limpieza de código para producción

---

## 🚀 Próximas Tareas - MVP v1.1

### Prioridad Alta
- [ ] Testing completo en Render
- [ ] Configurar variables de entorno en Render
- [ ] Webhook de WhatsApp funcional en producción
- [ ] Documentación de deployment
- [ ] Monitoreo de errores y logs

### Prioridad Media
- [ ] Mejorar manejo de errores en TTS
- [ ] Optimizar consultas a la base de datos
- [ ] Agregar tests unitarios críticos
- [ ] Implementar rate limiting
- [ ] Agregar health check endpoint

### Prioridad Baja
- [ ] Dashboard de métricas
- [ ] Exportar conversaciones a CSV
- [ ] Modo oscuro en UI
- [ ] Soporte para múltiples idiomas
- [ ] Plantillas de mensajes pre-configuradas

---

## 🐛 Bugs Conocidos

- [ ] HubSpot token expirado (requiere actualización manual)
- [ ] Archivos temporales de audio no se limpian automáticamente

---

## 🔧 Mejoras Técnicas Futuras

### Infraestructura
- [ ] Migrar de SQLite a PostgreSQL en producción
- [ ] Implementar Redis para caché
- [ ] Configurar CI/CD con GitHub Actions
- [ ] Agregar Docker support

### Features Avanzadas
- [ ] Soporte para imágenes en WhatsApp
- [ ] Análisis de sentimiento avanzado
- [ ] Recomendaciones de productos con IA
- [ ] A/B testing de mensajes
- [ ] Multi-tenancy (múltiples negocios)

---

## 📝 Notas de Desarrollo

### Entorno de Testing
- Variable `ENVIRONMENT=testing` para pruebas
- User IDs con prefijo `USRPRUEBAS_`

### Entorno de Producción
- Variable `ENVIRONMENT=production` para PRD
- User IDs con prefijo `USR_`

### Configuración Mínima Requerida
1. `system_prompt` (obligatorio)
2. `welcome_message` (obligatorio)
3. `OPENAI_API_KEY` en .env

### Archivos Importantes
- `app.py` - Aplicación principal Gradio
- `whatsapp_webhook.py` - Webhook para WhatsApp
- `reset_config.py` - Script para resetear configuración
- `.env` - Variables de entorno (NO incluir en Git)

---

**Última actualización:** 2025-11-21
