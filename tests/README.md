# Tests

Este directorio contiene los tests unitarios para el proyecto WhatsApp Sales Bot.

## Estructura

```
tests/
├── __init__.py              # Inicialización del paquete de tests
├── conftest.py              # Configuración de pytest y fixtures compartidos
├── test_llm_service.py      # Tests para el servicio LLM
├── test_message_formatting.py  # Tests para formateo de mensajes
├── test_nodes.py            # Tests para los nodos del grafo
└── README.md               # Este archivo
```

## Ejecutar los tests

### Instalar dependencias

```bash
pip install pytest pytest-asyncio pytest-mock
```

O instalar desde el archivo de requirements de desarrollo:

```bash
pip install -r requirements-dev.txt
```

### Ejecutar todos los tests

```bash
pytest tests/
```

### Ejecutar tests específicos

```bash
# Ejecutar tests de LLM service
pytest tests/test_llm_service.py

# Ejecutar tests de formateo de mensajes
pytest tests/test_message_formatting.py

# Ejecutar tests de nodos
pytest tests/test_nodes.py
```

### Ejecutar con modo verbose

```bash
pytest tests/ -v
```

### Ejecutar con coverage

```bash
pytest tests/ --cov=services --cov=graph --cov-report=html
```

## Tests incluidos

### test_llm_service.py

Tests para el servicio LLM que incluyen:

- Generación de respuestas con mensajes BaseMessage
- Manejo de mensajes en formato diccionario
- Manejo de mensajes mixtos
- Integración con RAG context
- Manejo de errores
- Clasificación de intención
- Análisis de sentimiento
- Extracción de datos
- Selección de modelo según tarea

### test_message_formatting.py

Tests para el formateo y conversión de mensajes:

- Validación de objetos HumanMessage, AIMessage, SystemMessage
- Verificación de formato de contenido
- Conversión de diccionarios a BaseMessage
- Manejo de contenido vacío o None
- Concatenación de listas de mensajes

### test_nodes.py

Tests para los nodos del grafo de conversación:

- welcome_node: Generación de mensaje de bienvenida
- intent_classifier_node: Clasificación de intención
- sentiment_analyzer_node: Análisis de sentimiento
- data_collector_node: Extracción de datos del usuario
- conversation_node: Generación de respuesta conversacional
- router_node: Enrutamiento basado en estado

## Configuración

La configuración de pytest se encuentra en `pytest.ini` en la raíz del proyecto.

Los fixtures compartidos y la configuración de mocks se encuentran en `conftest.py`.
