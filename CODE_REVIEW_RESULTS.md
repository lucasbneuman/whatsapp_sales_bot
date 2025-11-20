# Revisión de Código - WhatsApp Sales Bot v2.2

**Tag:** v2.2-pre-testing
**Fecha:** 2025-11-20

---

## ✅ Código que Funciona Correctamente

### 1. Preview de Voces TTS
- **Archivo:** `gradio_ui/config_panel_v2.py:109-132`
- **Estado:** ✅ Correcto
- **Método:** `preview_voice(voice_name: str)` es async
- **Retorna:** Path temporal del archivo MP3
- **Event handler:** Conectado correctamente con `inputs=[tts_voice]`

### 2. Generación de Notas con LLM
- **Archivo:** `services/llm_service.py:402-467`
- **Estado:** ✅ Correcto
- **Método:** `generate_conversation_notes()` usa GPT-4o-mini
- **Llamada:** En `gradio_app_v2.py:391-425`

### 3. Mensajes Multiparte
- **Archivo:** `gradio_app_v2.py:259-276`
- **Estado:** ✅ Correcto
- **Regex:** `r'\s*\[PAUSA\]\s*'` reemplaza correctamente
- **División:** Split en partes y agrega como mensajes separados

### 4. Detección de Humano
- **Archivo:** `graph/nodes.py:337-350`
- **Estado:** ✅ Correcto
- **Keywords:** Detecta "humano", "persona", "supervisor", etc.
- **Respuesta:** Retorna mensaje personalizado sin error

### 5. Recolección de Datos
- **Archivo:** `gradio_app_v2.py:303-346`
- **Estado:** ✅ Mejorado
- **Nombre:** Regex y detección de mensajes cortos
- **Email:** Regex pattern robusto
- **Teléfono:** Detecta con keywords y números largos

---

## ⚠️ Posibles Problemas Detectados

### 1. Configuración - Guardar con Dropdown vs Radio
- **Archivo:** `gradio_ui/config_panel_v2.py:366-372`
- **Problema Potencial:** Cambiamos de Dropdown a Radio pero save_all_configs sigue esperando el valor
- **Verificar:** Que tts_voice se guarde correctamente
- **Fix Necesario:** Probablemente NO (Radio y Dropdown retornan valor igual)

### 2. User ID - Generación
- **Archivo:** `gradio_app_v2.py:271-283`
- **Verificar:** Que se genere correctamente en cada nueva sesión
- **Condición:** `if not user_id or user_id.startswith("user_")`
- **Nota:** Podría no detectar IDs vacíos correctamente

### 3. Notas - Conversión de Historial
- **Archivo:** `gradio_app_v2.py:410-417`
- **Problema Potencial:** Conversión de history (dict) a Messages para LLM
- **Verificar:** Que todos los roles se mapeen correctamente
- **Podría fallar:** Si history tiene formato inesperado

---

## 🔍 Áreas que Requieren Pruebas Manuales

### Alta Prioridad
1. **Preview de Voces TTS** - Verificar que genera y reproduce audio
2. **Mensajes Multiparte** - Verificar que se separan visualmente
3. **Notas LLM** - Verificar que se generan en hitos correctos
4. **Recolección de Datos** - Verificar detección de nombre/email/teléfono

### Media Prioridad
5. **User ID** - Verificar formato USRPRUEBAS_XXXXXXXX
6. **Emojis** - Verificar que flag use_emojis funciona
7. **Límite de Palabras** - Verificar rangos 5-500
8. **RAG** - Verificar auto-activación con documentos

### Baja Prioridad
9. **Guardar Configuración** - Verificar todos los campos
10. **Limpiar Chat** - Verificar que resetea todos los datos

---

## 🛠️ Fixes Preventivos Recomendados

### Fix 1: Validación de User ID
**Problema:** Condición podría no detectar IDs vacíos

**Actual:**
```python
if not user_id or user_id.startswith("user_") or user_id == "USR_00" or user_id == "USRPRUEBAS_00":
```

**Recomendado:**
```python
if not user_id or user_id in ["user_12345678", "USR_00", "USRPRUEBAS_00", "USRPRUEBAS_"]:
```

### Fix 2: Manejo de Errores en Notas LLM
**Problema:** Si history está malformado, podría fallar silenciosamente

**Recomendado:** Agregar try-except más específico en la conversión

### Fix 3: Logging Mejorado
**Recomendado:** Agregar más logs para debugging:
- Log cuando se genera User ID
- Log cuando se activa flag "Solicita Humano"
- Log cuando se generan notas

---

## 📝 Próximos Pasos

1. ✅ Tag creado: `v2.2-pre-testing`
2. ⏳ Ejecutar testing manual con checklist
3. ⏳ Documentar resultados en `TESTING_CHECKLIST.md`
4. ⏳ Implementar fixes necesarios
5. ⏳ Crear tag final: `v2.2-stable`
