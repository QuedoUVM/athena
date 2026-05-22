"""
app.py — Interfaz Streamlit para Athena (Fase 2 · Sem 4 + Fase 3 · Sem 8)

Cómo correr:
    streamlit run app.py
"""

import streamlit as st
from agent import ejecutar_agente

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Athena · Asistente Financiero",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS mínimo ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .user-bubble   { background:#6C47FF; color:#fff; padding:10px 14px; border-radius:16px 16px 4px 16px; margin:4px 0; display:inline-block; max-width:75%; float:right; clear:both; }
    .agent-bubble  { background:#F3F0FF; color:#1a1a2e; padding:10px 14px; border-radius:16px 16px 16px 4px; margin:4px 0; display:inline-block; max-width:75%; float:left;  clear:both; }
    .bubble-wrap   { overflow:hidden; margin-bottom:4px; }
    .stTextInput>div>div>input { border-radius:20px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar — panel de configuración del agente ───────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank-building.png", width=60)
    st.title("Athena")
    st.caption("Asistente financiero personal · IA")
    st.divider()

    st.subheader("⚙️ Configuración del agente")

    modo = st.selectbox(
        "Modo de respuesta",
        ["Asesor financiero (conciso)", "Educativo (detallado)", "Solo datos"],
        help="Ajusta el estilo de las respuestas de Athena",
    )

    idioma = st.selectbox("Idioma", ["Español (México)", "English"])

    max_historial = st.slider(
        "Turnos de memoria",
        min_value=2, max_value=16, value=8, step=2,
        help="Cuántos mensajes anteriores recuerda Athena en la conversación",
    )

    st.divider()
    st.subheader("📊 Contexto financiero (demo)")
    usar_ctx = st.toggle("Inyectar datos de prueba", value=True)
    if usar_ctx:
        st.caption("Athena recibirá datos financieros de ejemplo para personalizar sus respuestas.")
        ctx_demo = (
            "=== CONTEXTO FINANCIERO (demo Streamlit) ===\n"
            "Ingresos del mes: $16,500 MXN\n"
            "Gastos del mes: $9,300 MXN\n"
            "Balance: $7,200 MXN (positivo ✓)\n"
            "Top gastos: Hogar ($3,500), Comida ($2,600), Transporte ($1,150)\n"
            "\n=== SCORE CREDITICIO ESTIMADO: 681 puntos (Bueno) ===\n"
            "Historial de pagos: 90%\n"
            "Utilización de crédito: 45% ⚠️ alto (ideal ≤30%)\n"
            "Antigüedad crediticia: 3 años\n"
            "Tipos de crédito: 2 ✓\n"
            "Solicitudes en 12 meses: 1 ✓"
        )
    else:
        ctx_demo = ""

    st.divider()
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages  = []
        st.session_state.historial = []
        st.rerun()

    st.caption("v1.0.0 · Demo académico · UVM")


# ── Session state ─────────────────────────────────────────────────────────────
if "messages"  not in st.session_state: st.session_state.messages  = []
if "historial" not in st.session_state: st.session_state.historial = []


# ── Cabecera ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🏛️ Athena — Asistente Financiero")
    st.caption("Powered by Groq · Llama 3 · Notion · Firebase")
with col2:
    st.metric("Mensajes en sesión", len(st.session_state.messages))

st.divider()


# ── Historial del chat ────────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown(
            "**👋 Hola, soy Athena.** Tu asistente financiero personal. "
            "Puedo ayudarte con presupuestos, inversiones, score crediticio, "
            "CETES, AFORE y mucho más. ¿En qué te ayudo hoy?"
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="bubble-wrap"><span class="user-bubble">🧑 {msg["content"]}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bubble-wrap"><span class="agent-bubble">🏛️ {msg["content"]}</span></div>', unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
st.divider()
with st.form("chat_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "Mensaje",
            placeholder="Escríbele a Athena…",
            label_visibility="collapsed",
        )
    with col_btn:
        enviado = st.form_submit_button("Enviar ➤", use_container_width=True)

if enviado and user_input.strip():
    prompt = user_input.strip()

    # Ajustar prompt según modo
    if modo == "Educativo (detallado)":
        prompt = f"Explícame detalladamente: {prompt}"
    elif modo == "Solo datos":
        prompt = f"Responde solo con datos y números, sin explicaciones: {prompt}"

    # Guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Athena está pensando…"):
        try:
            resultado = ejecutar_agente(
                mensaje_usuario=prompt,
                historial=st.session_state.historial[-max_historial:],
                contexto_usuario=ctx_demo if usar_ctx else "",
            )
            respuesta = resultado["respuesta"]
            st.session_state.historial = resultado["historial"][-max_historial:]
        except Exception as e:
            respuesta = f"⚠️ Error al conectar con el agente: {e}"

    st.session_state.messages.append({"role": "assistant", "content": respuesta})
    st.rerun()
