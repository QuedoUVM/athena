import os
import unicodedata
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

def _norm(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()

def _leer_contenido(page_id: str) -> str:
    lineas = []
    bloques = notion.blocks.children.list(block_id=page_id)
    for bloque in bloques.get("results", []):
        tipo = bloque["type"]
        if tipo in ["paragraph", "bulleted_list_item", "numbered_list_item", "heading_1", "heading_2", "heading_3"]:
            textos = bloque[tipo].get("rich_text", [])
            texto = "".join(t.get("plain_text", "") for t in textos)
            if texto:
                prefijo = "- " if "list" in tipo else ""
                lineas.append(f"{prefijo}{texto}")
            if bloque.get("has_children"):
                hijos = notion.blocks.children.list(block_id=bloque["id"])
                for hijo in hijos.get("results", []):
                    htipo = hijo["type"]
                    if htipo in ["paragraph", "bulleted_list_item", "numbered_list_item"]:
                        htextos = hijo[htipo].get("rich_text", [])
                        htexto = "".join(t.get("plain_text", "") for t in htextos)
                        if htexto:
                            lineas.append(f"  - {htexto}")
    return "\n".join(lineas)

def buscar_paginas(query: str) -> list:
    """Busca páginas en Notion por título o contenido de texto. Devuelve título, URL e contenido de cada página encontrada."""
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
            "id_pagina": r["id"],
            "titulo_pagina": titulo,
            "url_pagina": r.get("url", ""),
            "contenido": _leer_contenido(r["id"])
        })

    # Buscar también en el contenido de todas las páginas
    ids_encontrados = {p["id_pagina"] for p in paginas}
    todas = notion.search(filter={"property": "object", "value": "page"})
    palabras = _norm(query).split()
    for r in todas.get("results", []):
        page_id = r["id"]
        if page_id in ids_encontrados:
            continue
        bloques = notion.blocks.children.list(block_id=page_id)
        for bloque in bloques.get("results", []):
            if bloque["type"] in ["paragraph", "bulleted_list_item"]:
                textos = bloque[bloque["type"]].get("rich_text", [])
                for t in textos:
                    texto = _norm(t.get("plain_text", ""))
                    if all(p in texto for p in palabras):
                        titulo = ""
                        for prop in r.get("properties", {}).values():
                            if prop.get("type") == "title":
                                tts = prop.get("title", [])
                                if tts:
                                    titulo = tts[0].get("plain_text", "Sin título")
                        paginas.append({
                            "id_pagina": page_id,
                            "titulo_pagina": titulo,
                            "url_pagina": r.get("url", ""),
                            "fragmento": t.get("plain_text", "")
                        })
                        ids_encontrados.add(page_id)
                        break
    return paginas

def leer_pagina(page_id: str) -> dict:
    """Lee y devuelve el contenido completo de una página de Notion dado su ID."""
    return {"contenido": _leer_contenido(page_id)}

def crear_pagina(titulo: str, contenido: str) -> dict:
    """Crea una nueva página en Notion con un título y contenido inicial."""
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
    """Reemplaza el contenido de una página existente en Notion dado su ID."""
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