# Agente IA Personalizado de Notion

Agente conversacional construido con Python, Google Gemini y la API de Notion.
Permite buscar, crear y editar páginas de Notion mediante lenguaje natural.

## Stack
- Python 3.14
- Google Gemini 2.0 Flash
- Notion API
- Streamlit

## Instalación
1. Clonar el repositorio
2. Crear entorno virtual: `python -m venv venv --without-pip`
3. Activar: `venv\Scripts\activate`
4. Instalar pip: `curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py`
5. Instalar dependencias: `pip install notion-client google-generativeai streamlit python-dotenv`
6. Copiar `.env.example` a `.env` y llenar las keys

## Variables de entorno
Crear un archivo `.env` con:
\```
NOTION_TOKEN=secret_...
GEMINI_API_KEY=AIza...
NOTION_PARENT_PAGE_ID=...
\```