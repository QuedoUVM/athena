# Athena — Agente IA de Notion

Agente conversacional construido con Python, Groq (llama-3.3-70b-versatile) y la API de Notion.
Permite buscar, crear, leer, actualizar y eliminar páginas de Notion mediante lenguaje natural en español.

## Stack
- Python 3.9+
- Groq API (`llama-3.3-70b-versatile`)
- Notion API (`notion-client`)
- FastAPI + Uvicorn (servidor REST)
- Expo React Native (app móvil — proyecto `apex_app`)

## Instalación

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales
```

## Variables de entorno

```
NOTION_TOKEN=secret_...
GROQ_API_KEY=gsk_...
NOTION_PARENT_PAGE_ID=...   # ID de la página padre donde se crean nuevas páginas
```

El servidor valida estas variables al arrancar y falla con un mensaje claro si alguna falta.

## Cómo correr

```bash
# Servidor API (entrada principal)
python app_api.py
# o con auto-reload:
uvicorn app_api:app --host 0.0.0.0 --port 8000 --reload

# Verificar salud
curl http://localhost:8000/health

# Enviar mensaje de prueba
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿Qué páginas tengo?"}'
```

## Arquitectura

```
App React Native (apex_app)
    ↓ POST /chat
app_api.py   — FastAPI REST server
    ↓
agent.py     — Groq agentic loop (llama-3.3-70b-versatile, máx. 10 turnos)
    ↓ tool calls
notion_tools.py  — CRUD wrappers sobre notion-client SDK
    ↓
Notion API
```
