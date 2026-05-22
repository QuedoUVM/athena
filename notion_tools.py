import os
import time
import logging
import unicodedata
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

log = logging.getLogger("athena.notion")

# ── In-process content cache (page_id → (text, timestamp)) ──────────────────
_CONTENT_CACHE: dict = {}
_CACHE_TTL = 600  # 10 minutes


def _norm(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def _leer_contenido(page_id: str) -> str:
    lineas = []
    try:
        bloques = notion.blocks.children.list(block_id=page_id)
    except Exception as e:
        log.warning("No se pudieron leer bloques de %s: %s", page_id, e)
        return ""
    for bloque in bloques.get("results", []):
        tipo = bloque["type"]
        if tipo in ["paragraph", "bulleted_list_item", "numbered_list_item",
                    "heading_1", "heading_2", "heading_3"]:
            textos = bloque[tipo].get("rich_text", [])
            texto = "".join(t.get("plain_text", "") for t in textos)
            if texto:
                prefijo = "- " if "list" in tipo else ""
                lineas.append(f"{prefijo}{texto}")
            if bloque.get("has_children"):
                try:
                    hijos = notion.blocks.children.list(block_id=bloque["id"])
                except Exception as e:
                    log.warning("No se pudieron leer hijos de bloque %s: %s", bloque["id"], e)
                    continue
                for hijo in hijos.get("results", []):
                    htipo = hijo["type"]
                    if htipo in ["paragraph", "bulleted_list_item", "numbered_list_item"]:
                        htextos = hijo[htipo].get("rich_text", [])
                        htexto = "".join(t.get("plain_text", "") for t in htextos)
                        if htexto:
                            lineas.append(f"  - {htexto}")
    return "\n".join(lineas)


def _leer_contenido_cached(page_id: str) -> str:
    """Lee el contenido de una página con cache de 10 minutos."""
    now = time.time()
    entry = _CONTENT_CACHE.get(page_id)
    if entry and now - entry[1] < _CACHE_TTL:
        return entry[0]
    content = _leer_contenido(page_id)
    _CONTENT_CACHE[page_id] = (content, now)
    return content


def _invalidar_cache(page_id: str | None = None) -> None:
    if page_id:
        _CONTENT_CACHE.pop(page_id, None)
    else:
        _CONTENT_CACHE.clear()


def _titulo(r: dict) -> str:
    for prop in r.get("properties", {}).values():
        if prop.get("type") == "title":
            ts = prop.get("title", [])
            return ts[0].get("plain_text", "Sin título") if ts else "Sin título"
    return "Sin título"


# ── Herramientas públicas ─────────────────────────────────────────────────────

def buscar_paginas(query: str) -> list:
    """Busca páginas en Notion por título o contenido. Devuelve hasta 8 resultados con resumen."""
    log.info("buscar_paginas: query=%r", query)
    try:
        resp = notion.search(
            query=query,
            filter={"property": "object", "value": "page"},
            page_size=8,
        )
    except Exception as e:
        log.error("Error en búsqueda Notion: %s", e)
        return [{"error": f"No se pudo buscar en Notion: {e}"}]

    paginas = []
    for r in resp.get("results", []):
        contenido = _leer_contenido_cached(r["id"])
        paginas.append({
            "id_pagina": r["id"],
            "titulo_pagina": _titulo(r),
            "contenido_resumen": contenido[:900] if len(contenido) > 900 else contenido,
        })

    log.info("buscar_paginas: %d resultados", len(paginas))
    return paginas


def leer_pagina(page_id: str) -> dict:
    """Lee y devuelve el contenido completo de una página de Notion dado su ID."""
    log.info("leer_pagina: page_id=%s", page_id)
    return {"contenido": _leer_contenido_cached(page_id)}


def crear_pagina(titulo: str, contenido: str) -> dict:
    """Crea una nueva página en Notion con un título y contenido inicial."""
    log.info("crear_pagina: titulo=%r", titulo)
    parent_id = os.getenv("NOTION_PARENT_PAGE_ID")
    try:
        nueva = notion.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties={"title": [{"type": "text", "text": {"content": titulo}}]},
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": contenido}}]},
            }],
        )
    except Exception as e:
        log.error("Error al crear página '%s': %s", titulo, e)
        return {"error": f"No se pudo crear la página: {e}"}
    log.info("crear_pagina: creada id=%s", nueva["id"])
    return {"id": nueva["id"], "url": nueva.get("url", "")}


def agregar_a_pagina(page_id: str, contenido: str) -> dict:
    """Agrega una viñeta al final de una página existente en Notion sin borrar el contenido actual."""
    log.info("agregar_a_pagina: page_id=%s", page_id)
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[{
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": contenido}}]},
            }],
        )
    except Exception as e:
        log.error("Error al agregar a página %s: %s", page_id, e)
        return {"error": f"No se pudo agregar contenido: {e}"}
    _invalidar_cache(page_id)
    return {"id": page_id, "status": "contenido agregado"}


def eliminar_pagina(page_id: str) -> dict:
    """Archiva (elimina) una página de Notion dado su ID."""
    log.info("eliminar_pagina: page_id=%s", page_id)
    try:
        notion.pages.update(page_id=page_id, archived=True)
    except Exception as e:
        log.error("Error al eliminar página %s: %s", page_id, e)
        return {"error": f"No se pudo eliminar la página: {e}"}
    _invalidar_cache(page_id)
    return {"id": page_id, "status": "eliminada"}


def actualizar_pagina(page_id: str, nuevo_contenido: str) -> dict:
    """Reemplaza el contenido de una página existente en Notion dado su ID."""
    log.info("actualizar_pagina: page_id=%s", page_id)
    try:
        bloques = notion.blocks.children.list(block_id=page_id)
        for bloque in bloques.get("results", []):
            if bloque["type"] == "paragraph":
                notion.blocks.delete(block_id=bloque["id"])
        notion.blocks.children.append(
            block_id=page_id,
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": nuevo_contenido}}]},
            }],
        )
    except Exception as e:
        log.error("Error al actualizar página %s: %s", page_id, e)
        return {"error": f"No se pudo actualizar la página: {e}"}
    _invalidar_cache(page_id)
    return {"id": page_id, "status": "actualizado"}


def listar_bases_de_datos() -> list:
    """Lista todas las bases de datos (tablas) disponibles en el workspace de Notion."""
    log.info("listar_bases_de_datos")
    try:
        resp = notion.search(
            filter={"property": "object", "value": "database"},
            page_size=20,
        )
    except Exception as e:
        log.error("Error al listar bases de datos: %s", e)
        return [{"error": f"No se pudieron listar las bases de datos: {e}"}]

    bases = []
    for r in resp.get("results", []):
        # Extraer título de la base de datos
        titulo_props = r.get("title", [])
        titulo = titulo_props[0].get("plain_text", "Sin título") if titulo_props else "Sin título"

        # Extraer nombres de columnas/propiedades
        propiedades = list(r.get("properties", {}).keys())

        bases.append({
            "id": r["id"],
            "titulo": titulo,
            "url": r.get("url", ""),
            "columnas": propiedades[:10],  # máximo 10 columnas
            "total_columnas": len(propiedades),
        })

    log.info("listar_bases_de_datos: %d bases encontradas", len(bases))
    return bases


def agregar_entrada_a_tabla(database_id: str, propiedades: dict) -> dict:
    """
    Agrega una nueva fila/entrada a una base de datos (tabla) de Notion.

    database_id: ID de la base de datos destino (obtenido con listar_bases_de_datos).
    propiedades: dict con los valores de cada columna, p.ej:
        {"Nombre": "Gasto extra", "Monto": 500, "Categoría": "Comida", "Fecha": "2026-05-19"}
    """
    log.info("agregar_entrada_a_tabla: db=%s props=%s", database_id, list(propiedades.keys()))

    # Obtener esquema de la base de datos para mapear tipos de propiedades
    try:
        db_meta = notion.databases.retrieve(database_id=database_id)
    except Exception as e:
        log.error("Error al obtener esquema de DB %s: %s", database_id, e)
        return {"error": f"No se pudo acceder a la base de datos: {e}"}

    esquema = db_meta.get("properties", {})
    page_props: dict = {}

    for nombre_col, valor in propiedades.items():
        # Buscar la columna (case-insensitive)
        col_key = next((k for k in esquema if k.lower() == nombre_col.lower()), None)
        if not col_key:
            log.warning("Columna '%s' no encontrada en la DB, se omite", nombre_col)
            continue

        tipo = esquema[col_key]["type"]

        if tipo == "title":
            page_props[col_key] = {"title": [{"text": {"content": str(valor)}}]}
        elif tipo == "rich_text":
            page_props[col_key] = {"rich_text": [{"text": {"content": str(valor)}}]}
        elif tipo == "number":
            try:
                page_props[col_key] = {"number": float(valor)}
            except (ValueError, TypeError):
                page_props[col_key] = {"number": None}
        elif tipo == "select":
            page_props[col_key] = {"select": {"name": str(valor)}}
        elif tipo == "multi_select":
            opciones = [str(valor)] if not isinstance(valor, list) else [str(v) for v in valor]
            page_props[col_key] = {"multi_select": [{"name": o} for o in opciones]}
        elif tipo == "date":
            page_props[col_key] = {"date": {"start": str(valor)}}
        elif tipo == "checkbox":
            page_props[col_key] = {"checkbox": bool(valor)}
        elif tipo == "url":
            page_props[col_key] = {"url": str(valor)}
        elif tipo == "email":
            page_props[col_key] = {"email": str(valor)}
        elif tipo == "phone_number":
            page_props[col_key] = {"phone_number": str(valor)}
        else:
            log.warning("Tipo de columna '%s' no soportado: %s", col_key, tipo)

    if not page_props:
        return {"error": "No se encontró ninguna columna válida para insertar."}

    try:
        nueva = notion.pages.create(
            parent={"database_id": database_id},
            properties=page_props,
        )
    except Exception as e:
        log.error("Error al agregar entrada a DB %s: %s", database_id, e)
        return {"error": f"No se pudo agregar la entrada: {e}"}

    log.info("agregar_entrada_a_tabla: entrada creada id=%s", nueva["id"])
    return {"id": nueva["id"], "url": nueva.get("url", ""), "status": "entrada creada"}
