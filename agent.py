import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from notion_tools import buscar_paginas, leer_pagina, crear_pagina, actualizar_pagina

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Eres un asistente que gestiona el workspace de Notion del usuario.
Usa las herramientas disponibles para buscar, crear o actualizar páginas según lo que pida.
Cuando busques, usa las palabras clave tal como las mencionó el usuario, respetando el orden original.
Responde siempre en español de forma concisa."""

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
    }
]

HERRAMIENTAS = {
    "buscar_paginas": buscar_paginas,
    "leer_pagina": leer_pagina,
    "crear_pagina": crear_pagina,
    "actualizar_pagina": actualizar_pagina,
}

def _parsear_tool_call(raw: str):
    nombre_m = re.match(r"<function=(\w+)", raw)
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

def ejecutar_agente(mensaje_usuario: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": mensaje_usuario},
    ]

    while True:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
            )
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                content = msg.content or ""
                if "<function=" not in content:
                    return content
                nombre, args = _parsear_tool_call(content)
                if not nombre:
                    return content
                resultado = HERRAMIENTAS[nombre](**args)
                messages.append({"role": "tool", "tool_call_id": "inline", "content": json.dumps(resultado, ensure_ascii=False)})
                continue

            for tc in msg.tool_calls:
                nombre = tc.function.name
                args = json.loads(tc.function.arguments)
                resultado = HERRAMIENTAS[nombre](**args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })

        except Exception as e:
            err = str(e)
            if "tool_use_failed" not in err:
                raise
            # Parsear el tool call truncado y ejecutarlo manualmente
            fg = re.search(r"'failed_generation':\s*'(.*?)'[,}]", err, re.DOTALL)
            if not fg:
                raise
            nombre, args = _parsear_tool_call(fg.group(1))
            if not nombre:
                raise
            resultado = HERRAMIENTAS[nombre](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": "recovered",
                "content": json.dumps(resultado, ensure_ascii=False),
            })
