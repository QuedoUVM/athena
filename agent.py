import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from notion_tools import (
    buscar_paginas, leer_pagina, crear_pagina, actualizar_pagina,
    eliminar_pagina, agregar_a_pagina,
    listar_bases_de_datos, agregar_entrada_a_tabla,
)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Prompt usado cuando NO hay contexto financiero del usuario (preguntas generales)
SYSTEM_PROMPT = """Eres Athena, asistente financiero personal para usuarios mexicanos.
Responde en español, de forma directa y en máximo 100 palabras.
No menciones herramientas, sistemas ni bases de datos internas.
Usa tu conocimiento sobre finanzas personales MX (CETES, AFORE, Buró de Crédito, etc.).
Cierra con 1-2 acciones concretas."""

# Prompt usado cuando SÍ hay datos financieros del usuario
SYSTEM_PROMPT_PERSONAL = """Eres Athena, asistente financiero personal mexicano. Los datos financieros del usuario están en este system prompt — úsalos para personalizar CADA respuesta.

ESTILO:
- Máximo 80 palabras. Responde solo lo que se preguntó.
- Cita los números reales del usuario cuando sean relevantes (score, %, MXN, años).
- Varía el tono: a veces directo, a veces motivador, nunca robótico ni repetitivo.
- Cierra con una acción concreta solo cuando aporta valor a ESA pregunta.
- Habla siempre en primera persona cuando te refieras a lo que dijiste ("me refiero a...", "quise decir...", nunca "te refieres a...").
- Prohibido mencionar Notion, herramientas internas, búsquedas ni bases de datos."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_paginas",
            "description": "Busca páginas en Notion por título o contenido de texto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a buscar en Notion"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leer_pagina",
            "description": "Lee el contenido completo de una página de Notion dado su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "ID de la página a leer"}
                },
                "required": ["page_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_pagina",
            "description": "Crea una nueva página en Notion con un título y contenido inicial.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Título de la nueva página"},
                    "contenido": {"type": "string", "description": "Contenido inicial de la página"}
                },
                "required": ["titulo", "contenido"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agregar_a_pagina",
            "description": "Agrega contenido al final de una página existente en Notion sin borrar lo que ya tiene.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "ID de la página donde agregar contenido"},
                    "contenido": {"type": "string", "description": "Texto a agregar como nueva viñeta"}
                },
                "required": ["page_id", "contenido"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "eliminar_pagina",
            "description": "Archiva (elimina) una página de Notion dado su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "ID de la página a eliminar"}
                },
                "required": ["page_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_pagina",
            "description": "Reemplaza el contenido de una página existente en Notion dado su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "ID de la página a actualizar"},
                    "nuevo_contenido": {"type": "string", "description": "Nuevo contenido para la página"}
                },
                "required": ["page_id", "nuevo_contenido"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_bases_de_datos",
            "description": "Lista todas las bases de datos (tablas) disponibles en el workspace de Notion, con sus columnas.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "agregar_entrada_a_tabla",
            "description": "Agrega una nueva fila a una base de datos (tabla) de Notion. Usa listar_bases_de_datos primero para obtener el ID y columnas disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "ID de la base de datos de Notion"},
                    "propiedades": {
                        "type": "object",
                        "description": "Objeto con los valores de cada columna, p.ej: {\"Nombre\": \"Gasto\", \"Monto\": 500, \"Fecha\": \"2026-05-19\"}"
                    }
                },
                "required": ["database_id", "propiedades"]
            }
        }
    },
]

HERRAMIENTAS = {
    "buscar_paginas": buscar_paginas,
    "leer_pagina": leer_pagina,
    "crear_pagina": crear_pagina,
    "actualizar_pagina": actualizar_pagina,
    "eliminar_pagina": eliminar_pagina,
    "agregar_a_pagina": agregar_a_pagina,
    "listar_bases_de_datos": listar_bases_de_datos,
    "agregar_entrada_a_tabla": agregar_entrada_a_tabla,
}

MAX_TURNS = 10

def _parsear_tool_call(raw: str):
    nombre_m = re.search(r"<function=(\w+)", raw)
    if not nombre_m:
        return None, None
    nombre = nombre_m.group(1)
    json_m = re.search(r"(\{.*?\})", raw, re.DOTALL)
    if not json_m:
        return None, None
    args_str = json_m.group(1)
    if not args_str.endswith("}"):
        args_str += "}"
    try:
        return nombre, json.loads(args_str)
    except json.JSONDecodeError:
        return None, None

def ejecutar_agente(mensaje_usuario: str, historial: list = None, contexto_usuario: str = "") -> dict:
    """Ejecuta el agente y devuelve {"respuesta": str, "historial": list}.

    historial: lista de {"role": "user"|"assistant", "content": str} de turnos anteriores.
    """
    if historial is None:
        historial = []

    ctx = contexto_usuario.strip()

    if ctx:
        # Con datos personales: contexto en el system prompt + modelo grande.
        # El contexto NO se repite en cada user message para que la conversación
        # fluya naturalmente en múltiples turnos.
        system_content    = SYSTEM_PROMPT_PERSONAL + f"\n\n--- DATOS DEL USUARIO ---\n{ctx}"
        model_to_use      = "llama-3.3-70b-versatile"
        tools_param       = None
        tool_choice_param = None
    else:
        # Sin datos personales: modelo rápido con acceso a Notion.
        system_content    = SYSTEM_PROMPT
        model_to_use      = "llama-3.1-8b-instant"
        tools_param       = TOOLS
        tool_choice_param = "auto"

    messages = [
        {"role": "system", "content": system_content},
        *historial,
        {"role": "user", "content": mensaje_usuario},
    ]

    turns = 0
    while turns < MAX_TURNS:
        turns += 1
        try:
            call_kwargs = dict(
                model=model_to_use,
                messages=messages,
            )
            if tools_param:
                call_kwargs["tools"] = tools_param
                call_kwargs["tool_choice"] = tool_choice_param
                call_kwargs["parallel_tool_calls"] = False

            response = client.chat.completions.create(**call_kwargs)
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                content = msg.content or ""
                if "<function=" not in content:
                    nuevo_historial = historial + [
                        {"role": "user", "content": mensaje_usuario},
                        {"role": "assistant", "content": content},
                    ]
                    return {"respuesta": content, "historial": nuevo_historial}
                nombre, args = _parsear_tool_call(content)
                if not nombre:
                    nuevo_historial = historial + [
                        {"role": "user", "content": mensaje_usuario},
                        {"role": "assistant", "content": content},
                    ]
                    return {"respuesta": content, "historial": nuevo_historial}
                try:
                    resultado = HERRAMIENTAS[nombre](**args)
                except Exception as tool_err:
                    resultado = {"error": f"La herramienta '{nombre}' falló: {tool_err}"}
                messages.append({"role": "tool", "tool_call_id": "inline", "content": json.dumps(resultado, ensure_ascii=False)})
                continue

            for tc in msg.tool_calls:
                nombre = tc.function.name
                if nombre not in HERRAMIENTAS:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": f"Herramienta desconocida: {nombre}"}, ensure_ascii=False),
                    })
                    continue
                try:
                    args = json.loads(tc.function.arguments)
                    resultado = HERRAMIENTAS[nombre](**args)
                except Exception as tool_err:
                    resultado = {"error": f"La herramienta '{nombre}' falló: {tool_err}"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })

        except Exception as e:
            err = str(e)
            if "tool_use_failed" not in err:
                raise
            fg = re.search(r"'failed_generation':\s*'(.*?)'[,}]", err, re.DOTALL)
            if not fg:
                raise
            nombre, args = _parsear_tool_call(fg.group(1))
            if not nombre:
                raise
            try:
                resultado = HERRAMIENTAS[nombre](**args) if nombre in HERRAMIENTAS else {"error": f"Herramienta desconocida: {nombre}"}
            except Exception as tool_err:
                resultado = {"error": f"La herramienta '{nombre}' falló: {tool_err}"}
            messages.append({
                "role": "tool",
                "tool_call_id": "recovered",
                "content": json.dumps(resultado, ensure_ascii=False),
            })

    # MAX_TURNS reached without a final text response
    nuevo_historial = historial + [{"role": "user", "content": mensaje_usuario}]
    return {"respuesta": "Lo siento, no pude completar la operación a tiempo. Por favor intenta de nuevo.", "historial": nuevo_historial}
