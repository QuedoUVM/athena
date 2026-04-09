import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

def buscar_paginas(query: str) -> list:
    resultados = notion.search(query=query, filter={"property": "object", "value": "page"})
    paginas = []
    for r in resultados.get("results", []):
        titulo = ""
        props = r.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                textos = prop.get("title", [])
                if textos:
                    titulo = textos[0].get("plain_text", "Sin título")
                break
        paginas.append({
            "id": r["id"],
            "titulo": titulo,
            "url": r.get("url", "")
        })

    # Si no hay resultados, buscar en el contenido de todas las páginas
    if not paginas:
        todas = notion.search(filter={"property": "object", "value": "page"})
        for r in todas.get("results", []):
            page_id = r["id"]
            bloques = notion.blocks.children.list(block_id=page_id)
            for bloque in bloques.get("results", []):
                if bloque["type"] == "paragraph":
                    textos = bloque["paragraph"].get("rich_text", [])
                    for t in textos:
                        if query.lower() in t.get("plain_text", "").lower():
                            titulo = ""
                            for prop in r.get("properties", {}).values():
                                if prop.get("type") == "title":
                                    tts = prop.get("title", [])
                                    if tts:
                                        titulo = tts[0].get("plain_text", "Sin título")
                            paginas.append({
                                "id": page_id,
                                "titulo": titulo,
                                "url": r.get("url", "")
                            })
                            break
    return paginas

def crear_pagina(titulo: str, contenido: str) -> dict:
    parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
    nueva = notion.pages.create(
        parent={"type": "page_id", "page_id": parent_id},
        properties={
            "title": [{"type": "text", "text": {"content": titulo}}]
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": contenido}}]
                }
            }
        ]
    )
    return {"id": nueva["id"], "url": nueva.get("url", "")}

def actualizar_pagina(page_id: str, nuevo_contenido: str) -> dict:
    bloques = notion.blocks.children.list(block_id=page_id)
    for bloque in bloques.get("results", []):
        if bloque["type"] == "paragraph":
            notion.blocks.delete(block_id=bloque["id"])
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": nuevo_contenido}}]
                }
            }
        ]
    )
    return {"id": page_id, "status": "actualizado"}