# Reporte Técnico — Sprint 1
## Agente IA Personalizado de Notion

**Universidad del Valle de México**
**Equipo:** 5 integrantes
**Sprint:** Semanas 1 y 2 (13–26 de abril de 2026)
**Entregable:** Semana 3

---

## 1. Introducción

Este reporte documenta las decisiones técnicas, la arquitectura implementada y los resultados obtenidos durante el Sprint 1 del proyecto *Agente IA Personalizado de Notion*. El sprint abarcó dos semanas de trabajo: la primera orientada a la integración con la API de Notion, y la segunda a la implementación del agente de inteligencia artificial con capacidad de razonamiento y ejecución de herramientas.

El objetivo central del proyecto es construir un sistema que permita al usuario interactuar con su workspace de Notion mediante lenguaje natural en español, sin necesidad de abrir la aplicación manualmente.

---

## 2. Justificación Técnica de Decisiones de Diseño

### 2.1 Python como lenguaje principal

Python fue seleccionado por tres razones concretas:

1. **Ecosistema de IA maduro:** Las librerías de los principales proveedores de LLMs (Google, Groq, OpenAI) tienen sus SDKs oficiales en Python y son actualizadas con mayor frecuencia que en otros lenguajes.
2. **SDK oficial de Notion:** `notion-client` es el SDK oficial mantenido por la comunidad de Notion, disponible exclusivamente para Python y JavaScript. Se eligió Python para unificar toda la lógica en un solo lenguaje.
3. **Curva de aprendizaje del equipo:** Python permite iterar rápidamente sobre el código del agente sin overhead sintáctico.

### 2.2 Patrón de arquitectura: Tool Use / Function Calling

El agente no ejecuta código arbitrario ni decide autónomamente qué hacer. En cambio, se le ofrece un conjunto finito de herramientas (funciones Python) y el modelo de lenguaje decide cuál invocar en función del mensaje del usuario.

Este patrón —conocido como *function calling* o *tool use*— tiene ventajas claras sobre alternativas como el prompt engineering puro:

| Aspecto | Tool Use | Prompt puro |
|---|---|---|
| Control sobre acciones | Explícito y acotado | Difícil de restringir |
| Trazabilidad | Cada llamada es visible | Opaca |
| Mantenimiento | Agregar tools es modular | Requiere reescribir el prompt |
| Confiabilidad | El resultado viene de código Python | Puede alucinar datos |

La arquitectura resultante es de tres capas bien diferenciadas:

```
Usuario → Agente (LLM + tools) → Notion API
```

Cada capa tiene una responsabilidad única: el LLM interpreta la intención, las funciones Python ejecutan las operaciones reales, y la API de Notion persiste los cambios.

### 2.3 Migración de Google Gemini a Groq

El plan original contemplaba usar los modelos Gemini de Google, accesibles mediante el convenio institucional de la UVM con Google. Sin embargo, durante la Semana 2 se detectó el siguiente error al ejecutar el agente:

```
google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED
limit: 0, model: gemini-2.0-flash (free_tier)
```

El error indica que el proyecto de Google Cloud asociado a la API Key no tenía billing activo, lo que resultaba en cuota de free tier igual a cero. Al no poder resolver esto de forma inmediata, se evaluaron alternativas gratuitas con soporte para *function calling*:

| Proveedor | Costo | Function Calling | Latencia |
|---|---|---|---|
| Google Gemini (institucional) | Gratuito (con billing) | ✅ | Media |
| **Groq** | **Gratuito (sin tarjeta)** | **✅** | **Muy baja** |
| Ollama (local) | Gratuito | Depende del modelo | Alta (CPU) |
| OpenRouter | Limitado | ✅ | Media |

**Groq** fue seleccionado por:
- Registro gratuito sin tarjeta de crédito
- API compatible con el estándar OpenAI (migración mínima de código)
- Latencia extremadamente baja gracias al hardware LPU™ propietario
- Modelo `llama-3.3-70b-versatile` con soporte robusto para function calling

### 2.4 Modelo: `llama-3.3-70b-versatile`

Se evaluaron múltiples modelos disponibles en Groq durante las pruebas:

| Modelo | Resultado en pruebas |
|---|---|
| `llama3-groq-70b-8192-tool-use-preview` | Dado de baja (deprecated) |
| `llama-3.1-8b-instant` | Genera tool calls como texto plano; incapaz de razonar en múltiples pasos |
| `llama-3.3-70b-versatile` | Funcional con recuperación de errores; razonamiento multi-paso correcto |

El modelo de 8B resultó insuficiente para el patrón de *multi-step tool use*: en lugar de llamar correctamente la herramienta mediante la API estructurada, devolvía el tool call embebido como texto en el campo `content`. El modelo de 70B maneja correctamente la secuencia buscar → leer → responder.

### 2.5 Manejo de errores: `tool_use_failed`

Durante las pruebas se observó que `llama-3.3-70b-versatile` genera ocasionalmente JSON malformado en el tool call, resultando en el error `tool_use_failed` de la API de Groq. El `failed_generation` presentó tres formatos distintos:

```
<function=buscar_paginas>{"query": "sprint 5"}          ← formato A
<function=buscar_paginas {"query": "sprint 5"} </function>  ← formato B
<function=leer_pagina({"page_id": "abc123"})</function>     ← formato C
```

En lugar de propagar el error al usuario, se implementó un sistema de recuperación (`_parsear_tool_call`) que:
1. Extrae el nombre de la función con regex
2. Localiza el primer bloque JSON `{...}` en el string, independientemente del formato
3. Completa el JSON si está truncado (falta el `}` de cierre)
4. Ejecuta la función y continúa el loop de conversación

Esto convierte un error de la API en una operación transparente para el usuario.

---

## 3. Descripción de la Arquitectura

*Ver diagrama detallado: `docs/diagrama_arquitectura.drawio`*

### 3.1 Capas del sistema

**Capa 1 — Interfaz de usuario (`testing/test_agente.py`)**
Loop interactivo en terminal. El usuario escribe en texto plano; la respuesta del agente se muestra en color azul claro (ANSI `\033[96m`). Acepta cualquier prompt en lenguaje natural.

**Capa 2 — Agente IA (`agent.py`)**
Núcleo del sistema. Inicializa el cliente de Groq con las definiciones de herramientas en formato JSON Schema. Mantiene el historial de la conversación (`messages[]`) y ejecuta el siguiente loop:

```
1. Enviar messages al LLM (con tools disponibles)
2. Si la respuesta contiene tool_calls:
     → Ejecutar la función Python correspondiente
     → Agregar resultado a messages como rol "tool"
     → Volver a paso 1
3. Si la respuesta es texto final:
     → Retornar al usuario
4. Si ocurre tool_use_failed:
     → Parsear failed_generation y ejecutar manualmente
     → Volver a paso 1
```

**Capa 3 — Herramientas Notion (`notion_tools.py`)**
Cuatro funciones que encapsulan operaciones sobre la API de Notion:

- **`buscar_paginas(query)`:** Búsqueda dual (título + contenido de bloques), normalización de acentos, retorna contenido incluido para evitar llamadas secundarias.
- **`leer_pagina(page_id)`:** Lectura completa de bloques incluyendo sub-ítems anidados.
- **`crear_pagina(titulo, contenido)`:** Crea subpágina bajo la página padre configurada.
- **`actualizar_pagina(page_id, nuevo_contenido)`:** Reemplaza los párrafos existentes.

**Capa 4 — Servicios externos**
- **Groq API:** Recibe el historial de conversación y las definiciones de tools; retorna el tool call o el texto final.
- **Notion API (`notion-client`):** Ejecuta las operaciones reales sobre el workspace.

### 3.2 Flujo de datos completo

```
[Usuario] "¿Cuándo es la planeación de sprint 5?"
    ↓
[agent.py] Envía a Groq: messages + 4 tool definitions
    ↓
[Groq/LLM] Decide: llamar buscar_paginas("planeación de sprint 5")
    ↓
[notion_tools.py] buscar_paginas():
    1. notion.search("planeación de sprint 5") → 4 páginas (no incluye "Juntas")
    2. Fallback: scan contenido de páginas no encontradas
       → _norm("planeación...") vs _norm("Planeación de sprint 5 — 4 de junio")
       → Match → agrega "Juntas" con fragmento
    ↓
[agent.py] Agrega resultado a messages como rol "tool"
    ↓
[Groq/LLM] Genera respuesta: "La planeación de sprint 5 es el 4 de junio."
    ↓
[Usuario] Ve la respuesta en azul claro
```

---

## 4. Resultados del Sprint 1

### 4.1 Funcionalidades implementadas

| Funcionalidad | Estado |
|---|---|
| Integración con Notion API (CRUD) | ✅ Completo |
| Búsqueda por título | ✅ Completo |
| Búsqueda por contenido de bloques | ✅ Completo |
| Normalización de acentos en búsqueda | ✅ Completo |
| Lectura de sub-ítems anidados | ✅ Completo |
| Agente con function calling (Groq) | ✅ Completo |
| Recuperación de `tool_use_failed` | ✅ Completo |
| Chat interactivo en terminal con colores | ✅ Completo |
| Interfaz Streamlit (`app.py`) | 🔲 Pendiente (Semana 4) |
| Memoria conversacional | 🔲 Pendiente (Semana 6) |

### 4.2 Casos de uso probados exitosamente

- Consultar tareas pendientes con sub-ítems jerárquicos
- Buscar información dentro del contenido de una página (no solo por título)
- Ordenar y procesar datos extraídos de Notion (ej. lista alfabética de ideas)
- Crear nuevas páginas desde lenguaje natural
- Consultas con términos acentuados o con ortografía inconsistente

### 4.3 Limitaciones actuales

- **Paginación:** La API de Notion devuelve máximo 100 resultados por llamada. Workspaces grandes podrían requerir paginación.
- **Tipos de bloque:** Solo se procesan párrafos, listas y headings. Tablas, imágenes y bases de datos no están soportadas aún.
- **Sin memoria entre sesiones:** Cada invocación de `ejecutar_agente()` inicia una conversación nueva.
- **Cuota de Groq:** El free tier tiene límites de requests por minuto; uso intensivo podría requerir throttling.

---

## 5. Conclusiones

El Sprint 1 demostró la viabilidad técnica del sistema. En dos semanas se construyó una capa de integración funcional con Notion y un agente capaz de interpretar lenguaje natural y ejecutar operaciones reales. Los principales aprendizajes fueron:

1. **La elección del modelo importa:** Un modelo de 8B parámetros no es suficiente para *multi-step tool use* confiable; se requiere al menos 70B para este tipo de razonamiento.
2. **La robustez es esencial:** Los LLMs fallan de formas inesperadas (JSON truncado, tool calls como texto). El sistema debe manejar estos casos sin interrumpir al usuario.
3. **El diseño de las herramientas afecta la calidad de las respuestas:** Incluir el contenido directamente en `buscar_paginas` eliminó la necesidad de que el modelo tomara decisiones adicionales, mejorando la confiabilidad.

---

## 6. Próximos pasos (Sprint 2)

- **Semana 3:** Diagrama de arquitectura final + este reporte
- **Semana 4:** Implementar `app.py` con interfaz Streamlit
- **Semana 5:** Poblar workspace con 20+ páginas y diseñar escenarios de demo
- **Semana 6:** Agregar memoria conversacional entre turnos
