# Reporte de Avance — Fase 2 / Fase 3 Semana 6
## Arquitectura Completa e Integración de Interfaces de Usuario

**Universidad del Valle de México**
**Proyecto:** Athena — Asistente Financiero Personal con IA
**Equipo:** Juan Pablo, Oscar, Gabriel, Mariel, Alexis
**Periodo cubierto:** Semanas 4–6 | 4 de mayo – 24 de mayo de 2026
**Entregable:** Reporte de Avance — Arquitectura y UI

---

## 1. Resumen Ejecutivo

Durante las semanas 4 a 6 el proyecto Athena experimentó su mayor expansión en complejidad arquitectónica. A partir del agente funcional en Python construido en Fase 1, se añadieron tres capas nuevas:

1. **Capa de API REST** (`app_api.py` — FastAPI): exposición del agente como servicio HTTP con Docker
2. **Interfaz web** (`app.py` — Streamlit): frontend de demostración con panel de configuración
3. **Aplicación móvil** (Apex — React Native/Expo): frontend principal con autenticación Firebase, persistencia en Firestore y experiencia financiera completa

La arquitectura escaló de un script Python en terminal a un sistema de tres capas distribuidas, con dos frontends independientes apuntando al mismo backend.

---

## 2. Arquitectura del Sistema en Fase 2

### 2.1 Visión general

```
┌─────────────────────────┐     ┌──────────────────────┐
│   APEX (React Native)   │     │  Streamlit (app.py)  │
│   iOS · Android · Expo  │     │  Interfaz web demo   │
└────────────┬────────────┘     └──────────┬───────────┘
             │ POST /chat                  │ ejecutar_agente() directo
             ▼                             ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI  —  app_api.py  :8000              │
│           Docker · CORS abierto (dev)                  │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│              agent.py — Agentic Loop                   │
│   Groq llama-3.3-70b-versatile / llama-3.1-8b-instant  │
│   MAX_TURNS=10 · tool dispatch · fallback regex        │
└──────────┬─────────────────────────┬───────────────────┘
           │                         │
           ▼                         ▼
    ┌──────────────┐       ┌─────────────────────┐
    │  Groq Cloud  │       │    notion_tools.py   │
    │   LLM API    │       │    8 herramientas    │
    └──────────────┘       └─────────┬───────────┘
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │  Notion Workspace   │
                           │  API + Knowledge Base│
                           └─────────────────────┘

          ┌──────────────────────────────────┐
          │         Firebase (Google Cloud)  │
          │  Authentication + Firestore DB   │
          │  (athena_users — base no-default)│
          └──────────────────────────────────┘
                        ↕ SDK
                     Apex App
```

### 2.2 Separación de responsabilidades

| Capa | Archivo / Servicio | Responsabilidad |
|------|--------------------|-----------------|
| Frontend móvil | `apex_app/` | UX, autenticación, visualización financiera |
| Frontend web | `athena/app.py` | Demo académico con configuración de agente |
| API REST | `athena/app_api.py` | Puente HTTP entre Apex y el agente |
| Agente | `athena/agent.py` | Loop LLM + tool dispatch |
| Herramientas | `athena/notion_tools.py` | CRUD sobre Notion |
| Auth | Firebase Authentication | Gestión de identidad (UID + JWT) |
| Persistencia | Firebase Firestore | Perfil financiero, transacciones, chats |
| LLM | Groq Cloud API | Inferencia del modelo de lenguaje |
| Conocimiento | Notion Workspace | Base de conocimiento + tablas de datos |

---

## 3. Semana 4: Interfaz Streamlit (`app.py`)

### 3.1 Diseño del panel de configuración

La interfaz Streamlit se diseñó como demo académico y herramienta de prueba para el equipo. El sidebar incluye:

**Modo de respuesta:**
- *Asesor financiero (conciso)*: respuestas directas, máximo 80 palabras
- *Educativo (detallado)*: el prompt se prefija con "Explícame detalladamente: ..."
- *Solo datos*: el prompt se prefija con "Responde solo con datos y números: ..."

**Control de historial:** slider de 2 a 16 turnos de memoria. Determina cuántos mensajes previos se incluyen en el contexto enviado al agente en cada llamada.

**Contexto financiero de demostración:** toggle que inyecta datos ficticios de prueba en el campo `contexto_usuario`:
```
Ingresos del mes: $16,500 MXN
Gastos del mes: $9,300 MXN
Score crediticio: 681 puntos (Bueno)
Utilización de crédito: 45% (alto — ideal ≤30%)
Antigüedad crediticia: 3 años
```
Cuando este toggle está activo, el agente usa `llama-3.3-70b-versatile` con los datos en el system prompt y personaliza cada respuesta con los números reales del usuario.

### 3.2 Sistema de burbujas de chat

Se implementó un sistema de chat visualmente diferenciado con CSS inyectado:

- **Mensajes del usuario:** burbuja morada (`#6C47FF`), alineada a la derecha
- **Mensajes de Athena:** burbuja lila claro (`#F3F0FF`), alineada a la izquierda
- **Estado de sesión:** `st.session_state.messages` (display) y `st.session_state.historial` (enviado al agente) se mantienen separados para poder truncar el historial enviado sin afectar la visualización

El formulario de entrada usa `clear_on_submit=True` para limpiar el campo tras enviar, y `st.rerun()` para actualizar la vista inmediatamente.

### 3.3 Conexión directa con el agente

A diferencia de la app móvil (que pasa por FastAPI), Streamlit llama directamente a `ejecutar_agente()` desde `agent.py`:

```python
resultado = ejecutar_agente(
    mensaje_usuario=prompt,
    historial=st.session_state.historial[-max_historial:],
    contexto_usuario=ctx_demo if usar_ctx else "",
)
```

Esto simplifica el setup para demos: solo se necesita `streamlit run app.py`, sin servidor Docker.

---

## 4. Semana 5: API REST y Dockerización (`app_api.py`)

### 4.1 Servidor FastAPI

Se implementó `app_api.py` como capa de servicio HTTP que expone el agente al mundo exterior (principalmente a la app móvil Apex):

**Endpoint `POST /chat`:**
```json
Request:  { "mensaje": "...", "historial": [...], "contexto_usuario": "..." }
Response: { "respuesta": "...", "historial": [...] }
```

**Modelo Pydantic `ChatRequest`:**
```python
class ChatRequest(BaseModel):
    mensaje: str
    historial: list = Field(default_factory=list)   # evita mutable default
    contexto_usuario: str = Field(default="")
```

El uso de `Field(default_factory=list)` es crítico: un `list = []` como default en Pydantic crearía una única lista compartida entre todas las peticiones, haciendo que el historial de conversación de un usuario "filtrara" al siguiente (bug de estado mutable).

**Endpoint `GET /health`:** retorna `{"status": "ok"}`. Usado por `setup.sh` para verificar que el servidor está listo antes de mostrar el QR de la app.

**Validación de variables de entorno al inicio:**
```python
_missing = [v for v in ["GROQ_API_KEY", "NOTION_TOKEN", "NOTION_PARENT_PAGE_ID"]
            if not os.getenv(v)]
if _missing:
    sys.exit(f"Variables faltantes: {', '.join(_missing)}")
```
El servidor falla con mensaje claro si falta alguna credencial, en lugar de arrancar y fallar de forma críptica en el primer request.

### 4.2 Docker

Se contenerizó el servidor para estandarizar el entorno entre los 5 integrantes del equipo:

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Flujo de despliegue:**
```bash
docker compose build athena   # reconstruye imagen con código nuevo
docker compose up -d athena   # levanta en background
curl http://localhost:8000/health  # verifica
```

> **Lección aprendida:** `docker restart` **no** reconstruye la imagen — solo reinicia el contenedor existente. Para que los cambios en el código sean visibles, es obligatorio ejecutar `docker compose build` seguido de `docker compose up`.

### 4.3 Script de setup (`setup.sh`)

Para facilitar la configuración en diferentes redes (casa, universidad, hotspot), se creó `setup.sh` que:
1. Detecta la IP local del host con `hostname -I` / `ipconfig getifaddr en0`
2. Copia `.env.example` a `.env` si no existe
3. **Siempre** actualiza `EXPO_PUBLIC_API_URL` en `apex_app/.env` con la IP actual

```bash
sed -i.bak "s|^EXPO_PUBLIC_API_URL=.*|EXPO_PUBLIC_API_URL=http://$HOST_IP:8000|" apex_app/.env
```

La versión anterior del script solo creaba el archivo si no existía, lo que hacía que la URL quedara con la IP de casa al llevar la laptop a la universidad.

---

## 5. Semana 6: Aplicación Móvil Apex (React Native / Expo)

### 5.1 Stack tecnológico

| Componente | Tecnología |
|------------|------------|
| Framework | React Native + Expo SDK |
| Autenticación | Firebase Authentication (email/password + Google Sign-In) |
| Base de datos | Firebase Firestore (base de datos `athena_users`, no-default) |
| Navegación | React Navigation (Stack + Bottom Tabs) |
| Icons | `@expo/vector-icons` (Ionicons) |
| Configuración | `expo-constants` + `.env` (`EXPO_PUBLIC_*`) |

### 5.2 Pantallas implementadas

**`LoginScreen.js` — Autenticación**
- Formulario con email y contraseña
- Botón de Google Sign-In (OAuth 2.0 vía Expo Auth Session)
- Validación de campos antes del submit
- Manejo de errores de Firebase con mensajes en español

**`DashboardScreen.js` — Resumen financiero**
- Tarjeta de balance mensual (ingresos − gastos)
- Lista de últimas transacciones del mes actual
- Indicador de score crediticio con semáforo visual (rojo/amarillo/verde)
- Pull-to-refresh para actualizar datos desde Firestore

**`FinanceScreen.js` — Gestión de gastos e ingresos**
- Lista de transacciones filtrable por mes/categoría
- Formulario para registrar nuevo movimiento (monto, categoría, fecha, descripción)
- Categorías predefinidas: Hogar, Comida, Transporte, Entretenimiento, Salud, Ingreso, Otros

**`CreditScreen.js` — Score crediticio**
- Gauge visual del score (300–850)
- Desglose de los 5 factores del score: historial de pagos, utilización, antigüedad, tipos de crédito, consultas recientes
- Recomendaciones personalizadas según los valores actuales del usuario

**`InvestScreen.js` — Inversiones y ahorro**
- Información educativa sobre CETES, AFORE, S&P 500
- Calculadora de rendimiento proyectado (tasa, plazo, capital inicial)
- No conectado a datos reales en esta fase; listo para integración futura

**`ChatScreen.js` — Conversación con Athena**
- Burbujas de chat usuario/agente con scroll automático al último mensaje
- Indicador de "escribiendo..." (tres puntos animados)
- Timeout de 15 segundos en el fetch, con mensaje de error claro
- Contexto del usuario (`contexto_usuario`) construido dinámicamente desde Firestore y enviado en cada petición al agente

**`ChatHistoryScreen.js` — Historial de conversaciones**
- Lista de chats anteriores ordenados por fecha
- Botón de eliminación visible (ícono de basurero) con confirmación por alerta/dialog
- Persistencia en subcolección `chats` de Firestore

**`ProfileScreen.js` — Perfil del usuario**
- Foto de perfil (Google o avatar por defecto)
- Datos del usuario: nombre, email, fecha de registro
- Botón de cierre de sesión con limpieza de estado (mensajes y historial del chat)

### 5.3 Integración Firebase

**Authentication:**
```javascript
// authService.js
export const loginUser = (email, password) =>
    signInWithEmailAndPassword(auth, email, password);

export const loginWithGoogle = async () => {
    const { type, params } = await promptAsync();
    if (type === 'success') {
        const credential = GoogleAuthProvider.credential(null, params.access_token);
        return signInWithCredential(auth, credential);
    }
};
```

**Firestore — Base de datos no-default:**
El proyecto usa la base de datos `athena_users` en lugar de la base `(default)`, lo que requiere pasarla explícitamente en la inicialización:
```javascript
const db = getFirestore(app, 'athena_users');
```
Esta decisión se tomó para aislar los datos de Athena de otros posibles proyectos en el mismo workspace de Firebase.

**Estructura de datos en Firestore:**
```
athena_users (database)
  └── users (collection)
        └── {uid} (document)
              ├── email, displayName, photoURL
              ├── createdAt, updatedAt
              ├── scoreCredito: { score, historialPagos, utilizacion, antigüedad, ... }
              └── subcollections:
                    ├── transactions: { monto, categoria, fecha, descripcion, tipo }
                    └── chats: { titulo, preview, fecha, messages[] }
```

### 5.4 Contexto financiero hacia Athena

Cuando el usuario abre el chat, la app construye el `contexto_usuario` dinámicamente desde Firestore:

```javascript
const ctx = [
  `Ingresos del mes: $${ingresosDelMes} MXN`,
  `Gastos del mes: $${gastosDelMes} MXN`,
  `Balance: $${balance} MXN`,
  `Top gastos: ${topCategorias}`,
  `Score crediticio: ${score} puntos`,
  `Utilización: ${utilizacion}%`,
  `Historial de pagos: ${historialPagos}%`,
].join('\n');
```

Este string se envía como `contexto_usuario` en el body de `POST /chat`. El agente lo recibe, lo inyecta en el system prompt de `llama-3.3-70b-versatile`, y personaliza cada respuesta con los datos reales del usuario.

### 5.5 Correcciones aplicadas durante integración

| Problema | Causa | Solución |
|----------|-------|----------|
| App congelada al enviar mensaje | Sin timeout en fetch | `AbortController` con 15s de timeout |
| Chat de usuario A visible para usuario B | Logout no limpiaba estado | Limpiar `messages` y `historial` en `onAuthStateChanged` cuando `user === null` |
| Login fallaba con contraseñas válidas | `.trim()` aplicado a password | Eliminar `.trim()` de contraseña (mantenerlo solo en email) |
| Cambio de red rompía conexión | `apex_app/.env` no se actualizaba | `setup.sh` siempre sobreescribe la URL |
| Doble envío con taps rápidos | `loading` no se chequeaba al inicio de `sendMessage` | Guardia `if (loading) return;` al inicio |
| IP hardcodeada en código fuente | Variable directamente en `App.js` | `config.js` con `EXPO_PUBLIC_API_URL` desde `.env` |

---

## 6. Optimización del Agente — Estrategia de Doble Modelo

Un hallazgo crítico de las semanas 5–6 fue que el comportamiento del agente dependía fuertemente del modelo usado y del cómo se estructuraba el contexto:

### Problema observado
Con `llama-3.1-8b-instant` y contexto financiero inyectado, el agente:
- Ignoraba los datos numéricos del usuario y daba consejos genéricos
- Mencionaba nombres internos de funciones (`buscar_paginas`, "mi búsqueda no encontró...")
- Daba respuestas con formato rígido y repetitivo

### Solución: estrategia de dos rutas

```python
if contexto_usuario:
    # Con datos personales: modelo grande, sin tools, contexto en system prompt
    model_to_use      = "llama-3.3-70b-versatile"
    tools_param       = None           # No busca en Notion (datos ya en contexto)
    system_content    = SYSTEM_PROMPT_PERSONAL + "\n\n--- DATOS ---\n" + ctx
else:
    # Sin datos: modelo rápido con acceso a Notion
    model_to_use      = "llama-3.1-8b-instant"
    tools_param       = TOOLS
    system_content    = SYSTEM_PROMPT
```

**Justificación:**
- Cuando el app envía el contexto financiero del usuario, el agente ya tiene toda la información necesaria en el system prompt. Activar tools solo introduciría latencia y riesgo de que el modelo mencione Notion.
- El modelo 8B es suficiente para decidir qué herramienta de Notion llamar (tarea estructurada). Para razonar sobre datos personales y dar consejos financieros de calidad se requiere el modelo 70B.

---

## 7. Estado del Proyecto al Cierre de Fase 2 / Semana 6

### 7.1 Componentes completados

| Componente | Archivo | Estado |
|------------|---------|--------|
| Herramientas Notion (4 CRUD) | `notion_tools.py` | ✅ |
| Agente con function calling | `agent.py` | ✅ |
| Interfaz Streamlit | `app.py` | ✅ |
| API REST FastAPI | `app_api.py` | ✅ |
| Docker | `Dockerfile` + `docker-compose.yml` | ✅ |
| App móvil React Native | `apex_app/` | ✅ |
| Firebase Auth | `authService.js` | ✅ |
| Firebase Firestore | `firebaseConfig.js` | ✅ |
| Seed de datos de prueba | `seed_data.py` | ✅ |
| Script de setup automático | `setup.sh` | ✅ |

### 7.2 Usuarios de prueba configurados

| Usuario | Email | Datos |
|---------|-------|-------|
| Juan Pablo | juanpagameplays2015@gmail.com | 15 transacciones, score 720 |
| Oscar | oscar.athena@gmail.com | 14 transacciones, score 650 |
| Gabriel | gabriel.athena@gmail.com | 15 transacciones, score 710 |
| Mariel | mariel.athena@gmail.com | 15 transacciones, score 680 |
| Alexis | alexis.athena@gmail.com | 15 transacciones, score 695 |

---

## 8. Pendientes para Fase 3

| Entregable | Semana |
|-----------|--------|
| Nuevas herramientas Notion: `listar_bases_de_datos`, `agregar_entrada_a_tabla` | Sem 7 |
| Base de conocimiento PDF: leyes, guías de inversión, documentos del Banco de México | Sem 7 |
| Panel de configuración Streamlit (mejoras) | Sem 8 |
| Diagrama de arquitectura final | Sem 8 |
| Reporte técnico intermedio | Sem 8 |
