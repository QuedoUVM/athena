# Semana 1 — Fundamentos y Arquitectura Base

**Periodo:** 13–19 de abril de 2026

---

## Objetivo

Configurar el entorno de desarrollo completo y construir la capa de integración con la API de Notion: las funciones Python que permiten buscar, crear y actualizar páginas en el workspace.

---

## Qué se hizo

### 1. Configuración de Notion

Se creó una cuenta de Notion y se configuró una **Internal Integration** desde el panel de desarrolladores:

- **Nombre:** Agente IA (Demo 1)
- **Workspace:** Juan Pablo's Notion
- **Capacidades:** lectura, escritura y eliminación de bloques dentro de las páginas autorizadas

La integración genera un token (`NOTION_TOKEN`) que se usa para autenticar todas las llamadas a la API.

Se creó también una **base de conocimiento de prueba**: una página principal con tres subpáginas:
- `Juntas` — reuniones del equipo con fechas
- `Ideas de proyecto` — lista de ideas
- `Tareas pendientes` — tareas con sus materias y fechas de entrega

La página principal se conectó a la integración para que tenga acceso a ella.

---

### 2. Obtención de API Key del modelo IA

La UVM provee acceso a modelos de Google Gemini mediante un convenio institucional. Se obtuvo la API Key desde [aistudio.google.com](https://aistudio.google.com) con el correo institucional.

> **Nota:** Durante la Semana 2 se detectó que esa key tenía problemas de cuota, por lo que se migró a **Groq** como proveedor de LLM.

---

### 3. Setup del proyecto Python

```bash
mkdir agente-notion
cd agente-notion
python -m venv venv                         # entorno virtual aislado
venv\Scripts\activate
pip install notion-client google-generativeai streamlit python-dotenv
```

Se creó el archivo `.env` con las credenciales:

```
NOTION_TOKEN=secret_...
GEMINI_API_KEY=...
NOTION_PARENT_PAGE_ID=...
```

Y `.env.example` como plantilla para el equipo, sin valores reales.

---

### 4. Implementación de `notion_tools.py`

Se implementaron tres funciones que encapsulan las operaciones CRUD sobre Notion:

#### `buscar_paginas(query: str) -> list`
Busca páginas por título usando la API de Notion. Si no encuentra resultados directos, hace una búsqueda secundaria revisando el contenido de los bloques de cada página (párrafos y listas).

#### `crear_pagina(titulo: str, contenido: str) -> dict`
Crea una nueva subpágina bajo la página padre configurada en `.env`. Retorna el `id` y la `url` de la página creada.

#### `actualizar_pagina(page_id: str, nuevo_contenido: str) -> dict`
Elimina los bloques de párrafo existentes en una página y agrega el nuevo contenido como un bloque de párrafo nuevo.

---

### 5. Estructura del proyecto al cierre de la semana

```
agente-notion/
├── venv/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── notion_tools.py      ← implementado
├── agent.py             ← vacío (placeholder)
├── app.py               ← vacío (placeholder)
├── docs/
│   └── bitacora_1.txt
└── testing/
    └── test_tools.py
```

---

## Cómo se probó

Se ejecutó `testing/test_tools.py` manualmente con diferentes queries para verificar que:
- `buscar_paginas("Tareas pendientes")` devolviera la página correcta
- `crear_pagina(...)` creara una página visible en Notion
- El fallback de búsqueda por contenido encontrara páginas cuyo título no coincidía con la búsqueda

---

## Resultado

Capa de integración con Notion funcional y probada. El proyecto tiene entorno, credenciales y las tres operaciones base operativas. El siguiente paso es conectar estas funciones a un modelo de IA que decida cuándo y cómo llamarlas.
