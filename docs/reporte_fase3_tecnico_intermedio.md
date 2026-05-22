# Reporte Técnico Intermedio — Fase 3
## Athena: Expansión de Capacidades, Base de Conocimiento y Optimización del Agente

**Universidad del Valle de México**
**Proyecto:** Athena — Asistente Financiero Personal con IA
**Equipo:** Juan Pablo, Oscar, Gabriel, Mariel, Alexis
**Periodo cubierto:** Semanas 7–8 | 25 de mayo – 7 de junio de 2026
**Entregable:** Reporte Técnico Intermedio — Fase 3

---

## 1. Resumen de Fase 3

La Fase 3 consolidó Athena como un asistente financiero completo al resolver tres brechas identificadas durante las pruebas de la Fase 2:

1. **Capacidad de escritura en tablas de Notion:** el agente solo podía crear páginas de texto libre; no podía insertar filas en bases de datos estructuradas (tablas con columnas tipadas).
2. **Conocimiento financiero superficial:** la base de conocimiento en Notion contenía texto redactado manualmente. Se identificó la necesidad de documentos oficiales reales (leyes mexicanas, informes del Banco de México, guías de CONSAR) para que el agente diera respuestas más precisas y citables.
3. **Calidad de respuestas personalizadas:** el agente mencionaba herramientas internas, daba respuestas con formato rígido y no aprovechaba el contexto financiero del usuario de forma consistente.

---

## 2. Nuevas Herramientas de Notion (Semana 7)

### 2.1 Motivación

En la Fase 2, los usuarios podían pedirle a Athena que registrara un gasto, pero el agente solo era capaz de crear una página de texto libre ("Gasto: $500 en comida"). No podía insertar una fila en una tabla de Notion con columnas tipadas (Monto: número, Categoría: select, Fecha: date).

Para habilitar esto se necesitaban dos operaciones nuevas:
- Descubrir qué tablas existen y cuáles son sus columnas
- Insertar una fila con los tipos correctos según el esquema de cada columna

### 2.2 `listar_bases_de_datos() → list`

Usa la búsqueda de Notion filtrada por tipo `database` para encontrar todas las bases de datos del workspace:

```python
resp = notion.search(
    filter={"property": "object", "value": "database"},
    page_size=20,
)
```

Por cada base de datos retorna: `id`, `titulo`, `url`, `columnas` (hasta 10 nombres) y `total_columnas`.

**Por qué es necesaria antes de insertar:** la API de Notion requiere que cada propiedad de la nueva fila se estructure de acuerdo al tipo de columna. Sin conocer el esquema, es imposible construir el payload correcto. El agente llama primero a `listar_bases_de_datos`, identifica el `id` de la tabla correcta y sus columnas, y luego llama a `agregar_entrada_a_tabla`.

### 2.3 `agregar_entrada_a_tabla(database_id: str, propiedades: dict) → dict`

Esta función es la más compleja de las 8 herramientas. El flujo interno:

**Paso 1 — Introspección del esquema:**
```python
db_meta = notion.databases.retrieve(database_id=database_id)
esquema = db_meta.get("properties", {})
```
La API de Notion retorna el tipo de cada columna: `title`, `rich_text`, `number`, `select`, `multi_select`, `date`, `checkbox`, `url`, `email`, `phone_number`.

**Paso 2 — Mapeo de tipos Python → Notion:**

| Tipo Notion | Estructura requerida | Ejemplo |
|-------------|---------------------|---------|
| `title` | `{"title": [{"text": {"content": "..."}}]}` | Nombre del gasto |
| `number` | `{"number": 500.0}` | Monto |
| `select` | `{"select": {"name": "Comida"}}` | Categoría |
| `date` | `{"date": {"start": "2026-05-19"}}` | Fecha |
| `checkbox` | `{"checkbox": true}` | Pagado |
| `rich_text` | `{"rich_text": [{"text": {"content": "..."}}]}` | Descripción |

**Paso 3 — Creación de la fila:**
```python
notion.pages.create(
    parent={"database_id": database_id},
    properties=page_props,
)
```

**Búsqueda case-insensitive de columnas:** el usuario puede decir "monto" y la columna en Notion puede llamarse "Monto" o "MONTO". Se normaliza con `.lower()` antes de comparar:
```python
col_key = next((k for k in esquema if k.lower() == nombre_col.lower()), None)
```

**Ejemplo de uso:**
```
Usuario: "Registra un gasto de $350 en transporte del 19 de mayo"
Agente:
  1. listar_bases_de_datos() → encuentra tabla "Gastos" con id=xxx
  2. agregar_entrada_a_tabla(
       database_id="xxx",
       propiedades={"Nombre": "Transporte", "Monto": 350, 
                    "Categoría": "Transporte", "Fecha": "2026-05-19"}
     )
  3. Responde: "Registré el gasto de $350 en Transporte para hoy."
```

### 2.4 Integración en `agent.py`

Ambas herramientas se agregaron a la lista `TOOLS` con sus definiciones JSON Schema y al diccionario `HERRAMIENTAS`. El total de herramientas disponibles para el agente es ahora **8**:

| # | Herramienta | Operación |
|---|-------------|-----------|
| 1 | `buscar_paginas` | Búsqueda dual en workspace |
| 2 | `leer_pagina` | Lectura completa de página |
| 3 | `crear_pagina` | Nueva página de texto |
| 4 | `agregar_a_pagina` | Append de contenido sin borrar |
| 5 | `actualizar_pagina` | Reemplazar contenido |
| 6 | `eliminar_pagina` | Archivar página |
| 7 | `listar_bases_de_datos` | Descubrir tablas y columnas |
| 8 | `agregar_entrada_a_tabla` | Insertar fila en tabla tipada |

---

## 3. Base de Conocimiento PDF (Semana 7)

### 3.1 Problema: Notion no expone texto de archivos PDF adjuntos

La API de Notion, cuando se adjunta un PDF a una página, solo retorna la URL del archivo (almacenado en los servidores de Notion). No expone el contenido textual del documento. Un agente que intente "leer" un PDF adjunto solo recibirá el URL, no el texto.

La solución correcta es extraer el texto del PDF antes de subirlo y almacenarlo en Notion como texto plano en bloques de párrafo.

### 3.2 Pipeline `upload_pdfs_to_notion.py`

Se desarrolló un script standalone que automatiza el proceso completo:

```
PDF en disco
    │  PyMuPDF (fitz)
    ▼
Texto extraído con marcadores de página [Página N]
    │  chunked() — divide sin cortar palabras
    ▼
Fragmentos de máx 1,800 caracteres (límite Notion: 2,000)
    │  notion.pages.create() + notion.blocks.children.append()
    ▼
Página en Notion con callout + N bloques de párrafo
```

**`extraer_texto(pdf_path)`:** usa `fitz.open()` de PyMuPDF para extraer texto por página, prefijando cada sección con `[Página N]`. Solo incluye páginas con contenido no vacío.

**`chunked(text, size=1800)`:** divide el texto completo en fragmentos respetando límites de palabras (no corta a mitad de palabra). La API de Notion acepta bloques de hasta 2,000 caracteres; se usa 1,800 para dejar margen.

**Subida en lotes:** la API de Notion acepta máximo 100 bloques por llamada `blocks.children.append`. El script envía lotes de 90 con `time.sleep(0.4)` entre cada uno para respetar el rate limit de ~3 req/s.

**CLI:**
```bash
# Subir un PDF
python3 upload_pdfs_to_notion.py documento.pdf

# Subir todos los PDFs de una carpeta
python3 upload_pdfs_to_notion.py pdfs/

# Vista previa sin subir
python3 upload_pdfs_to_notion.py documento.pdf --preview
```

### 3.3 Documentos cargados a la base de conocimiento

Se subieron 7 documentos oficiales a Notion, totalizando decenas de miles de caracteres de conocimiento financiero verificado:

| Documento | Fuente | Relevancia |
|-----------|--------|------------|
| Ley para Regular Instituciones de Tecnología Financiera (Ley Fintech) | DOF | Regulación de apps y servicios FinTech en México |
| Ley del Mercado de Valores (LMV) | CNBV | Marco legal para inversiones bursátiles |
| Ley de Protección al Usuario de Servicios Financieros (CONDUSEF) | CONDUSEF | Derechos del usuario financiero |
| Informe Anual Banco de México | Banxico | Inflación, tasas de interés, CETES |
| Guía de Inversiones BIVA / BMV | BMV | Funcionamiento de la bolsa mexicana |
| Manual del Buró de Crédito | Buró de Crédito | Cómo funciona el score crediticio |
| Guía AFORE — CONSAR | CONSAR | Sistema de pensiones y retiro en México |

Estos documentos son accesibles por el agente mediante `buscar_paginas` cuando el usuario hace preguntas sobre regulaciones, tasas, inversiones o derechos financieros.

### 3.4 Verificación de integridad

Para confirmar que los documentos se subieron correctamente (y no como páginas vacías), se verificó que cada página en Notion contiene bloques de texto con contenido real. La API de Notion no puede leer PDF adjuntos, pero sí puede leer el texto extraído almacenado como párrafos, lo cual es lo que `leer_pagina()` retorna al agente.

---

## 4. Optimización de Respuestas del Agente (Semana 8)

### 4.1 Problemas identificados en pruebas con usuarios

Durante las pruebas de la Semana 7 con los 5 integrantes del equipo se identificaron tres problemas de calidad en las respuestas:

**Problema 1 — Menciones a herramientas internas:**
El agente incluía frases como "según mi búsqueda en Notion..." o "la herramienta `buscar_paginas` encontró..." en sus respuestas al usuario. El usuario no debe saber que existe Notion ni cómo funciona el sistema internamente.

**Problema 2 — Respuestas genéricas a pesar del contexto:**
Cuando el usuario enviaba su score crediticio de 681 puntos y preguntaba cómo mejorarlo, el agente daba consejos genéricos de México en lugar de citar el número real del usuario y sus factores específicos.

**Problema 3 — Formato rígido y repetitivo:**
Un system prompt anterior tenía una sección `FORMATO OBLIGATORIO:` que hacía que el agente iniciara cada respuesta con el score y terminara siempre con "Esta semana:". Las 3 preguntas de un usuario daban respuestas estructuralmente idénticas.

**Problema 4 — Tercera persona interna:**
El agente decía "¿Te refieres a tu historial de pagos?" cuando debía decir "¿Me refiero a tu historial de pagos?" — confundía al interlocutor con el hablante.

### 4.2 Soluciones implementadas en `agent.py`

**Dos system prompts independientes:**

```python
SYSTEM_PROMPT = """Eres Athena, asistente financiero personal para usuarios mexicanos.
Responde en español, de forma directa y en máximo 100 palabras.
No menciones herramientas, sistemas ni bases de datos internas.
Usa tu conocimiento sobre finanzas personales MX (CETES, AFORE, Buró de Crédito, etc.).
Cierra con 1-2 acciones concretas."""

SYSTEM_PROMPT_PERSONAL = """Eres Athena, asistente financiero personal mexicano.
Los datos financieros del usuario están en este system prompt — úsalos para personalizar CADA respuesta.

ESTILO:
- Máximo 80 palabras. Responde solo lo que se preguntó.
- Cita los números reales del usuario cuando sean relevantes (score, %, MXN, años).
- Varía el tono: a veces directo, a veces motivador, nunca robótico ni repetitivo.
- Cierra con una acción concreta solo cuando aporta valor a ESA pregunta.
- Habla siempre en primera persona ("me refiero a...", nunca "te refieres a...").
- Prohibido mencionar Notion, herramientas internas, búsquedas ni bases de datos."""
```

**Inyección de contexto solo en el system prompt:**
El contexto financiero del usuario se inyecta una sola vez en el `system_content`, no en cada mensaje del usuario. Esto evita que el historial de conversación se infle con el contexto repetido en cada turno:

```python
system_content = SYSTEM_PROMPT_PERSONAL + f"\n\n--- DATOS DEL USUARIO ---\n{ctx}"

messages = [
    {"role": "system", "content": system_content},
    *historial,                          # turnos previos sin contexto
    {"role": "user", "content": mensaje_usuario},  # solo el mensaje nuevo
]
```

**Resultado medible:** en las pruebas posteriores, el agente citaba correctamente el score 681, el 45% de utilización y los $16,500 MXN de ingresos en sus respuestas, sin mencionar Notion ni usar formatos repetitivos.

### 4.3 Modelo seleccionado por ruta

| Condición | Modelo | Razón |
|-----------|--------|-------|
| `contexto_usuario` presente | `llama-3.3-70b-versatile` | Razonamiento financiero de calidad; sigue instrucciones de estilo del 70B |
| Sin contexto (búsqueda Notion) | `llama-3.1-8b-instant` | Suficiente para decidir qué tool llamar; más rápido y menor costo |

---

## 5. Mejoras en `notion_tools.py` (Semana 8)

### 5.1 Cache en memoria

Para reducir la latencia en conversaciones multi-turno (donde el usuario hace varias preguntas sobre el mismo documento), se implementó un cache in-process:

```python
_CONTENT_CACHE: dict = {}   # { page_id: (contenido, timestamp) }
_CACHE_TTL = 600            # 10 minutos

def _leer_contenido_cached(page_id: str) -> str:
    now = time.time()
    entry = _CONTENT_CACHE.get(page_id)
    if entry and now - entry[1] < _CACHE_TTL:
        return entry[0]
    content = _leer_contenido(page_id)
    _CONTENT_CACHE[page_id] = (content, now)
    return content
```

Las operaciones de escritura (`agregar_a_pagina`, `actualizar_pagina`, `eliminar_pagina`) llaman a `_invalidar_cache(page_id)` para asegurarse de que la siguiente lectura obtenga el contenido actualizado.

### 5.2 Logging estructurado

Se agregó logging con `logging.getLogger("athena.notion")` en todas las funciones públicas:

```python
log.info("buscar_paginas: query=%r", query)
log.info("buscar_paginas: %d resultados", len(paginas))
log.error("Error en búsqueda Notion: %s", e)
```

Esto permite monitorear en tiempo real qué herramientas llama el agente durante el demo, útil para demostrar el razonamiento del sistema a la audiencia.

### 5.3 Try/except en todas las llamadas a la API

Todas las llamadas a la API de Notion están envueltas en `try/except Exception as e` que retorna un dict `{"error": "..."}` en lugar de propagar la excepción. El agente recibe el error como resultado de la tool call, puede informar al usuario de forma amigable y continúa funcionando.

---

## 6. Resultados Finales de Fase 3

### 6.1 Métricas del sistema completo

| Métrica | Valor |
|---------|-------|
| Herramientas Notion disponibles | 8 |
| Documentos PDF en base de conocimiento | 7 |
| Páginas de conocimiento en Notion | ~25 (18 redactadas + 7 PDFs) |
| Modelos LLM en uso | 2 (70B y 8B según contexto) |
| Usuarios de prueba configurados | 5 |
| Endpoints de API | 2 (`/chat`, `/health`) |
| Frontends | 2 (React Native + Streamlit) |
| Tiempo de respuesta promedio (con contexto) | 2–4 segundos |
| Tiempo de respuesta promedio (con Notion) | 4–8 segundos |

### 6.2 Tabla de entregables completos

| Fase | Sem | Entregable | Estado |
|------|-----|-----------|--------|
| Fase 1 | 1 | `notion_tools.py` — 4 herramientas CRUD | ✅ |
| Fase 1 | 2 | `agent.py` — Agentic loop con Groq | ✅ |
| Fase 1 | 3 | Diagrama de arquitectura + Reporte Fase 1 | ✅ |
| Fase 2 | 4 | `app.py` — Streamlit UI | ✅ |
| Fase 2 | 5 | `app_api.py` — FastAPI + Docker | ✅ |
| Fase 2 | 6 | Apex — React Native (6 pantallas) | ✅ |
| Fase 3 | 6 | Reporte de avance arquitectura + UI | ✅ |
| Fase 3 | 7 | `listar_bases_de_datos` + `agregar_entrada_a_tabla` | ✅ |
| Fase 3 | 7 | Pipeline PDF → Notion (7 documentos oficiales) | ✅ |
| Fase 3 | 8 | Optimización agente (doble modelo, prompts) | ✅ |
| Fase 3 | 8 | Cache de contenido + logging en notion_tools | ✅ |
| Fase 3 | 8 | Reporte técnico intermedio | ✅ (este documento) |

### 6.3 Casos de uso habilitados en Fase 3

| Caso de uso | Herramientas involucradas |
|-------------|--------------------------|
| "¿Qué dice la Ley Fintech sobre las SOFIPO?" | `buscar_paginas` → página PDF de la ley |
| "Registra un gasto de $300 en comida de hoy" | `listar_bases_de_datos` → `agregar_entrada_a_tabla` |
| "¿Cuál es mi score y cómo lo subo?" | Contexto del usuario en system prompt (sin tools) |
| "¿Qué es una AFORE y cuánto debería tener?" | `buscar_paginas` → Guía CONSAR |
| "Crea una página con mi plan de ahorro para diciembre" | `crear_pagina` |

---

## 7. Aprendizajes de Fase 3

### 7.1 Sobre el conocimiento del agente

El agente sin base de conocimiento PDF daba respuestas correctas pero genéricas. Con los 7 documentos oficiales cargados, puede citar artículos específicos de la Ley Fintech, tasas actuales de CETES del informe del Banco de México, y procedimientos exactos del Buró de Crédito. La calidad del conocimiento disponible es directamente proporcional a la calidad de las respuestas.

### 7.2 Sobre la personalización

La personalización financiera requiere el modelo más capaz disponible. El modelo de 8B es excelente para clasificar intenciones y llamar herramientas; es insuficiente para razonar sobre datos numéricos personales y generar consejos matizados. La estrategia de ruteo dinámico (8B para búsqueda, 70B para contexto personal) optimiza tanto costo como calidad.

### 7.3 Sobre la experiencia del usuario

Los usuarios de prueba notaron inmediatamente cuando el agente mencionaba herramientas internas: "¿Por qué me dice que buscó en Notion? Eso me rompe la ilusión de que es un asistente inteligente." La regla explícita "prohibido mencionar Notion o herramientas internas" en el system prompt resolvió esto completamente.

### 7.4 Sobre el diseño de APIs

La API de Notion tiene esquemas complejos y tipos de propiedad no documentados completamente. `agregar_entrada_a_tabla` requirió revisar la documentación oficial y hacer pruebas exhaustivas para cada tipo de columna. La introspección dinámica del esquema (`databases.retrieve`) fue la decisión correcta: hace la función robusta ante cualquier estructura de tabla, no solo las predefinidas.

---

## 8. Próximos Pasos (Semanas 9–10)

| Actividad | Descripción |
|-----------|-------------|
| Pruebas de integración con los 5 usuarios | Escenarios de demo documentados en `docs/demo_semana5.md` |
| Reporte técnico final | Documentación completa del sistema para entrega académica |
| Presentación / demo | Demostración en vivo con cada integrante usando su perfil |
| CORS en producción | Restringir `allow_origins` a la IP/dominio de la app antes de cualquier deploy público |
| Retry con backoff | Manejar rate limits de Groq y Notion en producción |
| Persistencia de historial | Guardar conversaciones en Firestore para recuperar sesiones anteriores |
