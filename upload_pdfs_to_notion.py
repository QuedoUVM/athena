"""
upload_pdfs_to_notion.py — Extrae texto de PDFs y los carga como páginas
en la base de conocimiento de Notion para que Athena pueda leerlos.

Instalar dependencias:
    pip3 install pymupdf python-dotenv notion-client

Uso:
    # Subir un PDF específico:
    python3 upload_pdfs_to_notion.py ruta/al/documento.pdf

    # Subir todos los PDFs de una carpeta:
    python3 upload_pdfs_to_notion.py pdfs/

    # Vista previa sin subir:
    python3 upload_pdfs_to_notion.py documento.pdf --preview

PDFs recomendados para la base de conocimiento:
    - Ley para Regular las Instituciones de Tecnología Financiera (Ley Fintech MX)
    - Ley del Mercado de Valores (LMV)
    - Ley de Protección y Defensa al Usuario de Servicios Financieros (CONDUSEF)
    - Informe Anual Banco de México (inflación, tasas CETES)
    - Guía de Inversiones BIVA / BMV
    - Manual del Buró de Crédito
    - Ley Federal de Protección al Consumidor (PROFECO — créditos)
    - Guía AFORE — CONSAR
    Fuentes: banxico.org.mx · condusef.gob.mx · cnbv.gob.mx · consar.gob.mx
"""

import os
import sys
import time
import argparse
import textwrap
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Instala PyMuPDF: pip3 install pymupdf")

try:
    from notion_client import Client
except ImportError:
    sys.exit("Instala notion-client: pip3 install notion-client")

notion = Client(auth=os.getenv("NOTION_TOKEN"))
PARENT_ID = os.getenv("NOTION_PARENT_PAGE_ID")

# Notion tiene un límite de 2,000 chars por bloque de texto
CHUNK_SIZE  = 1800
# Máximo de bloques por lote en la API de Notion
BATCH_SIZE  = 90


# ── Extracción de texto ───────────────────────────────────────────────────────

def extraer_texto(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF usando PyMuPDF."""
    doc = fitz.open(pdf_path)
    partes = []
    for i, pagina in enumerate(doc):
        texto = pagina.get_text("text").strip()
        if texto:
            partes.append(f"[Página {i+1}]\n{texto}")
    doc.close()
    return "\n\n".join(partes)


def chunked(text: str, size: int) -> list[str]:
    """Divide el texto en fragmentos de max `size` caracteres sin cortar palabras."""
    words = text.split()
    chunks, current = [], []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > size and current:
            chunks.append(" ".join(current))
            current, current_len = [], 0
        current.append(word)
        current_len += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


# ── Creación en Notion ────────────────────────────────────────────────────────

def _bloques_de_texto(chunks: list[str]) -> list[dict]:
    """Convierte fragmentos de texto en bloques de párrafo para Notion."""
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]},
        }
        for c in chunks
    ]


def crear_pagina_con_pdf(titulo: str, texto: str) -> dict:
    """Crea una página en Notion con el texto del PDF dividido en bloques."""
    chunks = chunked(texto, CHUNK_SIZE)
    print(f"  📄 {len(texto):,} chars → {len(chunks)} bloques")

    # Crear la página vacía primero
    pagina = notion.pages.create(
        parent={"type": "page_id", "page_id": PARENT_ID},
        properties={"title": [{"type": "text", "text": {"content": titulo}}]},
        children=[{
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": f"📚 Documento cargado automáticamente. {len(chunks)} fragmentos de texto."}}],
                "icon": {"type": "emoji", "emoji": "📄"},
            },
        }],
    )
    page_id = pagina["id"]

    # Agregar bloques en lotes de BATCH_SIZE
    for i in range(0, len(chunks), BATCH_SIZE):
        lote = chunks[i:i + BATCH_SIZE]
        notion.blocks.children.append(
            block_id=page_id,
            children=_bloques_de_texto(lote),
        )
        print(f"  ✓ Lote {i // BATCH_SIZE + 1}/{-(-len(chunks) // BATCH_SIZE)} subido")
        time.sleep(0.4)  # Respetar rate limit de Notion

    return {"id": page_id, "titulo": titulo, "bloques": len(chunks), "url": pagina.get("url", "")}


# ── CLI ───────────────────────────────────────────────────────────────────────

def procesar_pdf(path: str, preview: bool = False) -> None:
    p = Path(path)
    if not p.exists():
        print(f"  ❌ No encontrado: {path}")
        return
    if p.suffix.lower() != ".pdf":
        print(f"  ⚠️  No es PDF: {path}")
        return

    titulo = p.stem.replace("_", " ").replace("-", " ").title()
    print(f"\n{'─'*55}")
    print(f"  📖 {p.name}")
    print(f"  Título en Notion: {titulo}")

    print("  Extrayendo texto…")
    texto = extraer_texto(str(p))
    if not texto.strip():
        print("  ⚠️  El PDF no tiene texto extraíble (puede ser imagen escaneada).")
        return

    print(f"  {len(texto):,} caracteres extraídos")

    if preview:
        print("\n  Vista previa (primeros 500 chars):")
        print(textwrap.indent(texto[:500], "  │ "))
        print("  [--preview activo, no se sube a Notion]")
        return

    print("  Subiendo a Notion…")
    resultado = crear_pagina_con_pdf(titulo, texto)
    print(f"  ✅ Página creada: {resultado['url']}")


def main():
    parser = argparse.ArgumentParser(description="Sube PDFs a Notion como páginas de conocimiento")
    parser.add_argument("ruta", help="Ruta a un PDF o carpeta con PDFs")
    parser.add_argument("--preview", action="store_true", help="Solo mostrar vista previa, no subir")
    args = parser.parse_args()

    if not PARENT_ID:
        sys.exit("❌ NOTION_PARENT_PAGE_ID no está configurado en .env")
    if not os.getenv("NOTION_TOKEN"):
        sys.exit("❌ NOTION_TOKEN no está configurado en .env")

    ruta = Path(args.ruta)

    if ruta.is_dir():
        pdfs = sorted(ruta.glob("*.pdf"))
        if not pdfs:
            print(f"No se encontraron PDFs en: {ruta}")
            return
        print(f"Encontrados {len(pdfs)} PDFs en {ruta}")
        for pdf in pdfs:
            procesar_pdf(str(pdf), preview=args.preview)
    else:
        procesar_pdf(str(ruta), preview=args.preview)

    print("\n\n=== Carga completada ===")


if __name__ == "__main__":
    main()
