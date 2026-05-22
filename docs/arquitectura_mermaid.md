# Arquitectura del Sistema — Athena + Apex


```mermaid
flowchart TB
    subgraph FRONTENDS["Frontends"]
        direction LR
        subgraph APEX["Apex — React Native / Expo"]
            A_SCREENS["Dashboard · Finance · Credit · Invest · Chat · Profile"]
            A_SDK["Firebase Auth SDK + Firestore SDK"]
        end
        subgraph STREAMLIT["Streamlit UI — app.py"]
            S_UI["Sidebar config · Chat bubbles · Demo context"]
        end
    end

    subgraph BACKEND["Backend (Docker)"]
        subgraph FASTAPI["FastAPI — app_api.py  :8000"]
            F_CHAT["POST /chat"]
            F_HEALTH["GET /health"]
        end
        subgraph AGENT["agent.py — Agentic Loop (MAX_TURNS=10)"]
            AG_PERSONAL["ctx=True → llama-3.3-70b-versatile\n(sin tools, contexto en system prompt)"]
            AG_NOTION["ctx=False → llama-3.1-8b-instant\n(con 8 tools de Notion)"]
            AG_FALLBACK["Fallback: _parsear_tool_call regex"]
        end
        subgraph TOOLS["notion_tools.py — 8 herramientas CRUD"]
            T1["buscar_paginas"]
            T2["leer_pagina"]
            T3["crear_pagina"]
            T4["actualizar_pagina"]
            T5["agregar_a_pagina"]
            T6["eliminar_pagina"]
            T7["listar_bases_de_datos"]
            T8["agregar_entrada_a_tabla"]
            CACHE["_CONTENT_CACHE (TTL 10 min)"]
        end
    end

    subgraph EXTERNAL["Servicios Externos"]
        subgraph FIREBASE["Firebase (Google Cloud)"]
            FB_AUTH["Authentication — UID · JWT"]
            FB_FS["Firestore — athena_users DB\n(transactions · chats · score)"]
        end
        subgraph GROQ["Groq Cloud API (LPU)"]
            G1["llama-3.3-70b-versatile"]
            G2["llama-3.1-8b-instant"]
        end
        subgraph NOTION_WS["Notion Workspace"]
            N_KB["18 páginas de conocimiento\n7 docs PDF (texto extraído)"]
            N_DB["Tablas: gastos · ingresos"]
        end
    end

    subgraph PDF_PIPELINE["Pipeline PDF (offline)"]
        PDF["upload_pdfs_to_notion.py\nPyMuPDF → chunks → Notion pages"]
    end

    %% Connections
    APEX -->|"POST /chat (JSON)"| FASTAPI
    FASTAPI -->|"respuesta + historial"| APEX
    STREAMLIT -->|"ejecutar_agente() directo"| AGENT
    APEX <-->|"Auth / Firestore SDK"| FIREBASE

    FASTAPI --> AGENT
    AGENT -->|"LLM call"| GROQ
    GROQ -->|"completion"| AGENT
    AGENT -->|"tool calls (ctx=False)"| TOOLS
    TOOLS -->|"results"| AGENT
    TOOLS <-->|"CRUD API"| NOTION_WS

    FB_FS -->|"contexto_usuario\n(score, ingresos, gastos)"| FASTAPI

    PDF -->|"crea páginas"| NOTION_WS

    %% Styles
    classDef mobile    fill:#6C47FF,stroke:#6C47FF,color:#fff
    classDef stream    fill:#FF6B6B,stroke:#FF6B6B,color:#fff
    classDef firebase  fill:#FF9100,stroke:#FF9100,color:#fff
    classDef api       fill:#00B4D8,stroke:#00B4D8,color:#000
    classDef agent     fill:#00F5A0,stroke:#00F5A0,color:#000
    classDef notion    fill:#555,stroke:#aaa,color:#fff
    classDef groq      fill:#00F5A0,stroke:#00F5A0,color:#000

    class APEX,A_SCREENS,A_SDK mobile
    class STREAMLIT,S_UI stream
    class FIREBASE,FB_AUTH,FB_FS firebase
    class FASTAPI,F_CHAT,F_HEALTH api
    class AGENT,AG_PERSONAL,AG_NOTION,AG_FALLBACK agent
    class TOOLS,T1,T2,T3,T4,T5,T6,T7,T8,CACHE notion
    class GROQ,G1,G2 groq
    class NOTION_WS,N_KB,N_DB notion
```

## Estado de entregables — Fase 1 → Fase 3

| Fase | Sem | Entregable | Estado |
|------|-----|-----------|--------|
| **Fase 1** | 1 | Diseño de arquitectura del sistema | ✅ Completo (este diagrama) |
| **Fase 1** | 2 | Configuración del entorno (Firebase, Notion, Groq, Docker) | ✅ Completo |
| **Fase 1** | 3 | Primer reporte escrito | ⚠️ Pendiente (documento Word/PDF) |
| **Fase 2** | 4 | Streamlit UI — `app.py` | ✅ Completo |
| **Fase 2** | 5 | FastAPI backend — `app_api.py` | ✅ Completo |
| **Fase 2** | 6 | React Native app — Apex | ✅ Completo |
| **Fase 3** | 6 | Reporte de avance (arquitectura + UI) | ⚠️ Pendiente (documento) |
| **Fase 3** | 7 | Nuevas herramientas Notion: `listar_bases_de_datos` + `agregar_entrada_a_tabla` | ✅ Completo |
| **Fase 3** | 7 | Base de conocimiento PDF → Notion (7 documentos) | ✅ Completo |
| **Fase 3** | 8 | Panel configuración Streamlit (modo, idioma, historial) | ✅ Completo |
| **Fase 3** | 8 | Reporte técnico intermedio | ⚠️ Pendiente (documento) |
```
