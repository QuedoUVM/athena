# Reporte Técnico — Fase 1
## Proyecto Athena: Agente IA Financiero Personal con Integración a Notion

**Universidad del Valle de México**
**Materia:** Proyecto Integrador / Desarrollo de Software Avanzado
**Equipo:** 5 integrantes (Juan Pablo, Oscar, Gabriel, Mariel, Alexis)
**Periodo:** Semanas 1–3 | 13 de abril – 3 de mayo de 2026
**Entregable:** Reporte Escrito — Fase 1

---

## 1. Descripción General del Proyecto

**Athena** es un asistente financiero personal impulsado por inteligencia artificial. El sistema permite a usuarios mexicanos consultar, registrar y analizar su información financiera personal —ingresos, gastos, score crediticio, inversiones— mediante conversación en lenguaje natural en español.

A diferencia de un chatbot genérico, Athena combina dos capacidades:

1. **Conocimiento financiero contextualizado para México:** CETES, AFORE, Buró de Crédito, SAT, CONDUSEF, tasas del Banco de México.
2. **Acceso directo al workspace personal de Notion:** El agente puede buscar, crear, leer y actualizar páginas y bases de datos del usuario sin que este tenga que abrir la aplicación.

El proyecto nació de la observación de que las herramientas de productividad como Notion acumulan información financiera valiosa (presupuestos, gastos, metas), pero acceder a ella de forma rápida requiere navegación manual. Al conectar un LLM con la API de Notion mediante *tool use*, cualquier instrucción en lenguaje natural se traduce en una operación real sobre los datos del usuario.

---

## 2. Arquitectura del Sistema

La arquitectura sigue el patrón **Agente + Herramientas (Tool Use / Function Calling)**:

```
[Usuario]
    │  lenguaje natural (español)
    ▼
[Interfaz]  ←  terminal (Sprint 1) / Streamlit (Sprint 2) / App móvil (Sprint 3)
    │
    ▼
[agent.py — Agentic Loop]
    │  Groq API  (llama-3.3-70b-versatile)
    │  Decide qué herramienta invocar según el contexto
    ▼
[notion_tools.py — 4 herramientas CRUD]
    │  notion-client SDK
    ▼
[Notion API — Workspace del usuario]
    Búsqueda · Lectura · Creación · Actualización de páginas
```

### 2.1 Justificación del patrón Tool Use

El agente no genera texto inventado sobre los datos del usuario. En cambio, se le otorga un conjunto finito de herramientas Python, y el LLM decide cuál invocar según la instrucción recibida. Los resultados vienen de la API de Notion (datos reales), y el LLM solo se encarga de interpretar y redactar la respuesta.

| Criterio | Tool Use | Prompt puro |
|----------|----------|-------------|
| Datos verídicos | ✅ Siempre (vienen de Notion) | ❌ Puede alucinar |
| Control sobre acciones | ✅ Acotado y auditable | ❌ Difícil de restringir |
| Escalabilidad | ✅ Agregar una tool es modular | ❌ Requiere reescribir el prompt |
| Trazabilidad | ✅ Cada call es loggeable | ❌ Opaco |

### 2.2 Elección del stack

| Componente | Tecnología elegida | Justificación |
|------------|-------------------|---------------|
| Lenguaje | Python 3.14 | SDK oficial de Notion disponible; ecosistema IA maduro |
| LLM | Groq — `llama-3.3-70b-versatile` | Gratuito, sin tarjeta, latencia baja (LPU™), function calling robusto |
| Integración Notion | `notion-client` SDK | SDK oficial, mantenido activamente |
| Variables de entorno | `python-dotenv` | Separación de credenciales del código |
| Interfaz inicial | Terminal (ANSI colors) | Validación rápida sin overhead de UI |

**Nota sobre la migración de Google Gemini a Groq:** el plan original usaba modelos Gemini mediante el convenio institucional UVM–Google. En la Semana 2 se detectó el error `429 RESOURCE_EXHAUSTED (limit: 0)`, indicando cuota de free tier cero por falta de billing en el proyecto de Google Cloud. Se evaluaron Ollama (local, latencia alta), OpenRouter (limitado) y Groq. Groq fue seleccionado por su acceso gratuito sin tarjeta, API compatible con el estándar OpenAI (migración mínima de código) y soporte probado para *multi-step tool use* con LLaMA 3.3 70B.

---

## 3. Implementación — Semana 1: Capa de Integración con Notion

### 3.1 Configuración de Notion

Se creó una **Internal Integration** en el panel de desarrolladores de Notion:

- Nombre de la integración: *Agente IA (Demo 1)*
- Workspace: *Juan Pablo's Notion*
- Permisos: lectura, escritura y eliminación de bloques
- Token almacenado en `.env` como `NOTION_TOKEN`

Se configuró la página padre del proyecto (`NOTION_PARENT_PAGE_ID`) y se conectó a la integración. Todas las páginas creadas por el agente son subpáginas de esta página raíz, lo que mantiene el workspace organizado.

Se creó una base de conocimiento de prueba con tres páginas iniciales: *Juntas*, *Ideas de proyecto* y *Tareas pendientes*, con contenido real para validar las funciones de búsqueda.

### 3.2 `notion_tools.py` — Herramientas implementadas

#### `buscar_paginas(query: str) → list`

Búsqueda en dos pasos:

1. **Búsqueda nativa de Notion** por título mediante `notion.search()`. Rápida pero limitada: Notion solo indexa títulos y no siempre devuelve resultados relevantes por contenido.
2. **Búsqueda de contenido manual** (fallback): itera sobre los bloques de texto de las páginas del workspace, aplica `unicodedata.NFD` para normalizar acentos, y agrega páginas no encontradas en el paso 1. Resuelve el caso frecuente de "busco algo en el contenido de una página, no en su título."

La función devuelve directamente el contenido de cada página encontrada (hasta 900 caracteres), evitando que el agente necesite hacer una segunda llamada a `leer_pagina`.

#### `leer_pagina(page_id: str) → dict`

Lee el contenido completo de una página dado su ID, incluyendo:
- Bloques de tipo `paragraph`, `bulleted_list_item`, `numbered_list_item`, `heading_1/2/3`
- Sub-ítems anidados (un nivel de profundidad)

Necesaria cuando el resumen de `buscar_paginas` no es suficiente y el agente requiere el texto completo.

#### `crear_pagina(titulo: str, contenido: str) → dict`

Crea una nueva subpágina bajo `NOTION_PARENT_PAGE_ID` con el título y contenido especificados. Retorna el `id` y la `url` de la página creada, que el LLM puede incluir en la respuesta al usuario.

#### `actualizar_pagina(page_id: str, nuevo_contenido: str) → dict`

Reemplaza el contenido de una página existente. La implementación:
1. Lista los bloques actuales de la página
2. Elimina solo los bloques de tipo `paragraph` (preserva headings, listas, callouts)
3. Agrega el nuevo contenido como párrafo

**Limitación conocida:** si la página contiene headings o listas estructuradas, estos sobreviven la actualización. Se decidió preservar este comportamiento para evitar pérdida accidental de estructura.

### 3.3 Decisiones de diseño relevantes

**Normalización de acentos:** el modelo LLM escribe indistintamente "planeacion" y "planeación". La función `_norm()` aplica `unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()` en ambos lados de la comparación, haciendo el match insensible a tildes y mayúsculas.

**Docstrings descriptivos:** cada función incluye un docstring que explica qué hace, qué parámetros recibe y qué devuelve. Estos docstrings se pasan al LLM como `description` en la definición de la herramienta; su calidad afecta directamente la capacidad del modelo para elegir la herramienta correcta.

---

## 4. Implementación — Semana 2: Agente IA

### 4.1 Loop del agente (`agent.py`)

El agente ejecuta un loop iterativo con límite de MAX_TURNS = 10:

```
1. Enviar messages[] al LLM (incluyendo definiciones de tools)
2. Si la respuesta tiene tool_calls:
     a. Ejecutar la función Python correspondiente
     b. Agregar resultado a messages como rol "tool"
     c. Volver a 1
3. Si la respuesta es texto final (sin tool_calls):
     a. Retornar al usuario
4. Si ocurre tool_use_failed:
     a. Extraer función y args del failed_generation con regex
     b. Ejecutar manualmente
     c. Volver a 1
```

El historial de la conversación (`messages[]`) se construye concatenando system prompt, historial previo y mensaje del usuario en cada llamada, permitiendo continuidad en conversaciones multi-turno.

### 4.2 Manejo del error `tool_use_failed`

`llama-3.3-70b-versatile` genera ocasionalmente JSON malformado en el tool call, lo que produce el error `tool_use_failed` en la API de Groq. Se observaron tres formatos de `failed_generation`:

```
Formato A: <function=buscar_paginas>{"query": "sprint 5"}
Formato B: <function=buscar_paginas {"query": "sprint 5"} </function>
Formato C: <function=leer_pagina({"page_id": "abc123"})</function>
```

La función `_parsear_tool_call(raw: str)` usa dos expresiones regulares:
- `r"<function=(\w+)"` — extrae el nombre de la función
- `r"(\{.*?\})"` con `re.DOTALL` — extrae el primer bloque JSON

Si el JSON está truncado (termina sin `}`), se completa antes de llamar a `json.loads()`. El error se convierte en una operación transparente para el usuario.

### 4.3 Definiciones de herramientas (JSON Schema)

Las 4 herramientas se declaran en la lista `TOOLS` con el formato compatible con la API de Groq/OpenAI. Cada definición incluye:
- `name`: identificador Python de la función
- `description`: texto que el LLM usa para decidir cuándo llamar esta herramienta
- `parameters`: JSON Schema con los parámetros requeridos y sus tipos

El diccionario `HERRAMIENTAS` mapea cada nombre de función a su callable Python, lo que permite ejecutar dinámicamente cualquier tool que el modelo seleccione.

### 4.4 Chat interactivo en terminal

Para validar el flujo completo sin overhead de UI, se implementó un loop interactivo en `testing/test_agente.py`:
- Entrada del usuario en blanco sobre fondo oscuro
- Respuesta del agente en azul claro (ANSI `\033[96m`)
- Soporte para Ctrl+C y comando `salir`

---

## 5. Semana 3: Arquitectura y Documentación

### 5.1 Diagrama de arquitectura

Se generó el diagrama de arquitectura del sistema completo (incluyendo las fases futuras del proyecto) en dos formatos:
- **PNG** (`docs/arquitectura.png`): generado con Python/matplotlib para insertar en reportes
- **Mermaid** (`docs/arquitectura_mermaid.md`): renderizable en Notion, GitHub y draw.io

El diagrama cubre todas las capas: frontend React Native, Streamlit, FastAPI, agente, notion_tools, Groq API y Notion Workspace.

### 5.2 Estructura del proyecto al cierre de Fase 1

```
athena/
├── .env                      # Credenciales (no commiteado)
├── .env.example              # Plantilla pública
├── .gitignore
├── requirements.txt
├── notion_tools.py           # 4 herramientas CRUD + búsqueda dual
├── agent.py                  # Agentic loop con recuperación de errores
├── app.py                    # placeholder (Fase 2)
├── app_api.py                # placeholder (Fase 2)
├── docs/
│   ├── arquitectura.png
│   ├── arquitectura_mermaid.md
│   ├── planeacion_proyecto.md
│   ├── semana1.md
│   ├── semana2.md
│   └── reporte_fase1.md      # este documento
└── testing/
    ├── test_tools.py
    └── test_agente.py        # chat interactivo en terminal
```

---

## 6. Resultados y Validación

### 6.1 Funcionalidades completadas en Fase 1

| Funcionalidad | Estado |
|---------------|--------|
| Integración con Notion API | ✅ |
| Búsqueda por título (nativa) | ✅ |
| Búsqueda por contenido de bloques (fallback) | ✅ |
| Normalización de acentos | ✅ |
| Lectura de bloques anidados | ✅ |
| Creación de páginas | ✅ |
| Actualización de páginas | ✅ |
| Agente con function calling (Groq + LLaMA 3.3 70B) | ✅ |
| Loop multi-turno con historial | ✅ |
| Recuperación de `tool_use_failed` | ✅ |
| Chat interactivo en terminal | ✅ |
| Diagrama de arquitectura | ✅ |

### 6.2 Casos de uso validados

| Prompt | Herramienta invocada | Resultado |
|--------|---------------------|-----------|
| "¿Qué tareas tengo pendientes?" | `buscar_paginas` | Lista con sub-ítems jerárquicos |
| "¿Cuándo es la planeación de sprint 5?" | `buscar_paginas` (fallback) | Fecha extraída del contenido |
| "Lista mis ideas ordenadas alfabéticamente" | `buscar_paginas` + orden por LLM | Lista ordenada correctamente |
| "Crea una página con título X y contenido Y" | `crear_pagina` | Página visible en Notion |
| "Actualiza la página de tareas con Z" | `buscar_paginas` + `actualizar_pagina` | Contenido reemplazado |

### 6.3 Limitaciones identificadas

- **Sin memoria entre sesiones:** cada ejecución de `ejecutar_agente()` inicia conversación nueva.
- **Paginación no implementada:** máximo 100 resultados por llamada a Notion.
- **Tipos de bloque limitados:** tablas, imágenes y bases de datos (databases) no soportadas aún.
- **Sin interfaz gráfica:** la interacción ocurre en terminal; `app.py` queda para Fase 2.

---

## 7. Aprendizajes del Equipo

**El tamaño del modelo importa.** `llama-3.1-8b-instant` no es capaz de ejecutar *multi-step tool use* de forma confiable: devuelve los tool calls como texto plano en el campo `content` en lugar de usar la API estructurada. Se requiere mínimo 70B para razonamiento con herramientas en múltiples pasos.

**El diseño de las herramientas afecta la calidad de las respuestas.** Incluir el contenido directamente en la respuesta de `buscar_paginas` (en lugar de devolver solo IDs) eliminó la necesidad de que el modelo tomara decisiones adicionales para obtener la información, reduciendo errores y latencia.

**Los LLMs fallan de formas predecibles.** El error `tool_use_failed` no es aleatorio: ocurre cuando el modelo genera JSON muy largo o con estructuras anidadas complejas. Implementar el parser de recuperación desde el principio fue la decisión correcta; de lo contrario, aproximadamente el 5% de las interacciones habrían terminado en error.

---

## 8. Próximos Pasos (Fase 2)

| Semana | Entregable |
|--------|------------|
| Sem 4 | `app.py` — Interfaz Streamlit con sidebar de configuración |
| Sem 5 | `app_api.py` — Servidor FastAPI + Docker; demo con workspace poblado |
| Sem 6 | React Native / Expo — App móvil (Apex) con Firebase Auth + Firestore |
