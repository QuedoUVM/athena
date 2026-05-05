"""
app_api.py — Servidor FastAPI que expone el agente Notion como API REST.

La app de React Native (athena-app) se comunica con este servidor.

Cómo correr:
    python app_api.py
    o bien:
    uvicorn app_api:app --host 0.0.0.0 --port 8000 --reload

La app React Native debe apuntar a la IP local de esta máquina, puerto 8000.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import ejecutar_agente

load_dotenv()

app = FastAPI(
    title="Athena — Agente Notion API",
    description="API REST que conecta la app móvil con el agente IA de Notion",
    version="1.0.0",
)

# CORS abierto para desarrollo — en producción restringir a la IP/dominio de la app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    mensaje: str


class ChatResponse(BaseModel):
    respuesta: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Verificación de que el servidor está corriendo."""
    return {"status": "ok", "agente": "Athena Notion Agent v1.0"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Recibe un mensaje del usuario y retorna la respuesta del agente.

    El agente puede llamar herramientas de Notion internamente (buscar,
    leer, crear, actualizar páginas) antes de generar la respuesta.
    """
    if not req.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    try:
        respuesta = ejecutar_agente(req.mensaje)
        return ChatResponse(respuesta=respuesta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el agente: {str(e)}")


# ── Punto de entrada ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("app_api:app", host="0.0.0.0", port=8000, reload=True)
