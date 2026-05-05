# Semana 2 — Implementación del Agente IA

**Periodo:** 20–26 de abril de 2026

---

## Objetivo

Implementar `agent.py`: el cerebro del sistema. Un agente capaz de interpretar lenguaje natural, decidir qué herramienta de Notion invocar y devolver una respuesta coherente al usuario. Adicionalmente, crear una interfaz de chat en terminal para pruebas de flujo completo.

---

## Qué se hizo

### 1. Migración de Google Gemini a Groq

La API Key institucional de Gemini presentó error `429 RESOURCE_EXHAUSTED` con `limit: 0` en el free tier, lo que indicaba que el proyecto de Google Cloud asociado no tenía billing habilitado para consumo real.

Se migró a **Groq** como proveedor de LLM:
- Registro gratuito en [console.groq.com](https://console.groq.com)
- Sin tarjeta de crédito, con cuota generosa
- Modelo seleccionado: `llama-3.3-70b-versatile`

```bash
pip install groq
```

Se actualizó `requirements.txt` y `.env.example` con la nueva variable `GROQ_API_KEY`.

---

### 2. Implementación de `agent.py`

El agente implementa un loop de conversación con **function calling** (tool use):

```
mensaje usuario
    ↓
LLM decide qué tool llamar
    ↓
se ejecuta la función Python
    ↓
resultado enviado de vuelta al LLM
    ↓
LLM genera respuesta final en lenguaje natural
```

Las herramientas se declaran en formato OpenAI-compatible (JSON Schema) y se pasan al modelo en cada llamada. El modelo responde con un `tool_call` estructurado que indica qué función ejecutar y con qué argumentos.

**Manejo de `tool_use_failed`:** el modelo `llama-3.3-70b-versatile` genera ocasionalmente JSON truncado o malformado en el tool call (e.g., `<function=buscar_paginas {"query": "..."}` sin cerrar). Se implementó un parser robusto (`_parsear_tool_call`) que extrae el nombre de la función y los argumentos del `failed_generation`, completa el JSON si está truncado, y ejecuta la función de todos modos — sin interrumpir el flujo.

El parser maneja tres formatos distintos observados durante las pruebas:
- `<function=nombre>{"args": ...}`
- `<function=nombre {"args": ...} </function>`
- `<function=nombre({"args": ...})</function>`

---

### 3. Correcciones y mejoras en `notion_tools.py`

Durante las pruebas del agente se detectaron y corrigieron varios problemas:

**Bug de claves inconsistentes:** el bloque de fallback de `buscar_paginas` devolvía `"id"`, `"titulo"`, `"url"` en lugar de `"id_pagina"`, `"titulo_pagina"`, `"url_pagina"`. Corregido para que ambos flujos devuelvan el mismo esquema.

**Búsqueda de contenido siempre activa:** la búsqueda por contenido de bloques solo corría cuando Notion no devolvía resultados por título. Se cambió para que siempre corra y agregue páginas adicionales no encontradas por el search inicial. Esto resolvió el caso donde Notion devolvía páginas irrelevantes pero omitía la página con el contenido buscado.

**Normalización de acentos:** el modelo a veces escribe "planeacion" sin tilde. La comparación ahora normaliza ambos strings con `unicodedata.NFD` antes de comparar, haciendo el match insensible a acentos.

**Docstrings en las tres funciones:** necesarios para que el LLM comprenda cuándo invocar cada herramienta.

**Nueva función `leer_pagina(page_id)`:** herramienta que lee el contenido completo de una página dado su ID, incluyendo bloques anidados (sub-ítems de listas). Se necesitó porque `buscar_paginas` inicialmente solo devolvía título y URL, y el modelo no tenía acceso al contenido real.

**`buscar_paginas` devuelve contenido:** para evitar que el modelo necesite hacer dos llamadas (buscar + leer), `buscar_paginas` ahora incluye el contenido de cada página encontrada en la respuesta. Esto permite al modelo responder preguntas sobre el contenido en un solo ciclo de tool use.

---

### 4. Interfaz de chat en terminal (`testing/test_agente.py`)

Se reemplazaron los casos de prueba fijos por un loop interactivo con colores ANSI:

- El usuario escribe su prompt en la terminal
- El agente responde en **azul claro** (`\033[96m`)
- Se escribe `salir` o `Ctrl+C` para terminar

```bash
python testing/test_agente.py
```

---

### 5. Estructura del proyecto al cierre de la semana

```
agente-notion/
├── venv/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt     ← nuevo
├── notion_tools.py      ← mejorado (4 funciones, normalización, contenido incluido)
├── agent.py             ← implementado (Groq + tool use + parser robusto)
├── app.py               ← vacío (Semana 4)
├── docs/
│   ├── bitacora_1.txt
│   ├── planeacion_proyecto.md
│   ├── semana1.md
│   └── semana2.md
└── testing/
    ├── test_tools.py
    └── test_agente.py   ← chat interactivo con colores
```

---

## Flujos probados

| Prompt de prueba | Herramienta invocada | Resultado |
|---|---|---|
| "¿Qué tareas tengo pendientes?" | `buscar_paginas` | Lista correcta con sub-ítems |
| "¿Cuándo es la planeación de sprint 5?" | `buscar_paginas` | Fecha extraída del contenido de "Juntas" |
| "Ideas de proyecto ordenadas alfabéticamente" | `buscar_paginas` + orden por LLM | Lista ordenada correctamente |
| "Crea una página llamada X con contenido Y" | `crear_pagina` | Página creada y visible en Notion |

---

## Resultado

El agente está operativo y conectado a Notion. Interpreta lenguaje natural en español, selecciona la herramienta correcta, la ejecuta y responde de forma coherente. El flujo completo (usuario → LLM → Notion → respuesta) funciona en terminal. Próximo paso: construir la interfaz Streamlit (`app.py`) en la Semana 4.
