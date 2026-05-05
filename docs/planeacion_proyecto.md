# Planeación del Proyecto — Agente IA Personalizado de Notion

**Universidad del Valle de México**
**Periodo:** 13 de abril – 1 de julio de 2026

---

## ¿Qué es?

Un agente de inteligencia artificial conversacional que permite al usuario interactuar con su workspace de Notion en lenguaje natural. En lugar de abrir la aplicación y navegar manualmente, el usuario escribe una instrucción en español ("¿Qué tareas tengo pendientes?", "Crea una página con las ideas del sprint") y el agente la ejecuta directamente.

---

## ¿Para qué sirve?

- **Consultar información** almacenada en Notion sin abrir la app.
- **Crear páginas** automáticamente con título y contenido desde el chat.
- **Actualizar contenido** de páginas existentes con una sola instrucción.
- **Buscar dentro del contenido** de cualquier página, no solo por título.

El valor principal es reducir la fricción entre el usuario y su base de conocimiento: en lugar de recordar en qué página está algo, simplemente se le pregunta al agente.

---

## ¿Por qué?

Las herramientas de productividad como Notion concentran mucha información valiosa, pero acceder a ella de forma rápida sigue requiriendo navegación manual. Los modelos de lenguaje grandes (LLMs) con capacidad de *tool use* permiten conectar lenguaje natural con APIs externas, convirtiendo cualquier servicio con API en una herramienta conversacional.

Este proyecto aplica ese patrón en un contexto real y acotado: un workspace personal de Notion, con herramientas CRUD concretas y un modelo que decide cuál invocar según el contexto.

---

## Hipótesis

> *Si conectamos un modelo de lenguaje con capacidad de function calling a la API de Notion, es posible construir un agente funcional que interprete instrucciones en lenguaje natural y ejecute operaciones reales (buscar, leer, crear, actualizar páginas) con una tasa de éxito alta para casos de uso cotidianos.*

---

## Arquitectura general

```
Usuario (texto)
    ↓
Interfaz Streamlit  (app.py)         ← Semana 4
    ↓
Agente IA / LLM    (agent.py)        ← Semana 2
    ↓  decide qué tool llamar
Herramientas Notion (notion_tools.py) ← Semana 1
    ↓
API de Notion (notion-client SDK)
    ↓
Workspace real de Notion
```

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.14 |
| LLM / Agente | Groq API — `llama-3.3-70b-versatile` |
| Notion API | `notion-client` (SDK oficial) |
| Interfaz | Streamlit (pendiente) |
| Variables de entorno | `python-dotenv` |

---

## Fases del cronograma

| Semana | Fase | Entregable |
|---|---|---|
| 1 (13–19 abr) | Fundamentos | Setup + `notion_tools.py` |
| 2 (20–26 abr) | Agente | `agent.py` + tool use + pruebas |
| 3 (27 abr–3 may) | Arquitectura | Diagrama + reporte escrito |
| 4 (4–10 may) | UI | `app.py` en Streamlit |
| 5 (11–17 may) | Demo | Workspace poblado + escenarios |
| 6–8 (may–jun) | Avanzado | Memoria, bases de datos, config |
| 9–10 (jun) | Entrega | Pruebas, documentación, presentación |
