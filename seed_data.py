"""
seed_data.py — Pobla la base de datos Firestore con movimientos y perfil
crediticio para el usuario de prueba y 4 usuarios adicionales.

Uso:
    # Poblar solo al usuario actual (pide email/password):
    python seed_data.py

    # Crear + poblar los 4 usuarios de prueba adicionales:
    python seed_data.py --create-test-users
"""

import sys
import json
import time
import getpass
import argparse
import requests
from datetime import datetime, timezone

# ── Configuración Firebase ────────────────────────────────────────────────────
API_KEY    = "AIzaSyBeMgxm8RWVSYwf2Qz_AKTKHJqKB6D8ERI"
PROJECT_ID = "athena-f695a"
DB_ID      = "athena-users"
BASE_FS    = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DB_ID}/documents"
AUTH_URL   = f"https://identitytoolkit.googleapis.com/v1/accounts"


# ── Firebase Auth helpers ─────────────────────────────────────────────────────

def sign_in(email: str, password: str) -> tuple[str, str]:
    r = requests.post(
        f"{AUTH_URL}:signInWithPassword?key={API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
    )
    r.raise_for_status()
    d = r.json()
    return d["idToken"], d["localId"]


def sign_up(email: str, password: str, display_name: str) -> tuple[str, str]:
    r = requests.post(
        f"{AUTH_URL}:signUp?key={API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
    )
    r.raise_for_status()
    d = r.json()
    id_token, uid = d["idToken"], d["localId"]
    # Set display name
    requests.post(
        f"{AUTH_URL}:update?key={API_KEY}",
        json={"idToken": id_token, "displayName": display_name},
    )
    return id_token, uid


# ── Firestore REST helpers ────────────────────────────────────────────────────

def _fv(value):
    """Convert a Python value to a Firestore field value dict."""
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, datetime):
        return {"timestampValue": value.strftime("%Y-%m-%dT%H:%M:%SZ")}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {k: _fv(v) for k, v in value.items()}}}
    if isinstance(value, list):
        return {"arrayValue": {"values": [_fv(i) for i in value]}}
    return {"nullValue": None}


def _fields(data: dict) -> dict:
    return {"fields": {k: _fv(v) for k, v in data.items()}}


def create_doc(collection_path: str, data: dict, id_token: str) -> str:
    """POST — auto-generated document ID. Returns the new doc name."""
    r = requests.post(
        f"{BASE_FS}/{collection_path}",
        json=_fields(data),
        headers={"Authorization": f"Bearer {id_token}"},
    )
    r.raise_for_status()
    return r.json()["name"]


def patch_doc(doc_path: str, data: dict, id_token: str):
    """PATCH with full field mask — creates or replaces specific fields."""
    mask = "&".join(f"updateMask.fieldPaths={k}" for k in data.keys())
    r = requests.patch(
        f"{BASE_FS}/{doc_path}?{mask}",
        json=_fields(data),
        headers={"Authorization": f"Bearer {id_token}"},
    )
    r.raise_for_status()
    return r.json()


# ── Transaction helpers ───────────────────────────────────────────────────────

def dt(year, month, day, hour=10):
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


def tx(type_, amount, desc, category, emoji, date):
    return {
        "type":        type_,
        "amount":      float(amount),
        "description": desc,
        "category":    category,
        "emoji":       emoji,
        "date":        date,
    }


def seed_transactions(uid: str, id_token: str, transactions: list, credit_profile: dict):
    col = f"athena_users/{uid}/transactions"
    print(f"  💾 Escribiendo {len(transactions)} transacciones…")
    for t in transactions:
        create_doc(col, t, id_token)
        time.sleep(0.15)

    # Credit profile goes inside the user document
    print("  💾 Escribiendo perfil crediticio…")
    patch_doc(f"athena_users/{uid}", {"creditProfile": credit_profile}, id_token)

    # Also write/update the user doc display name so it appears in the app
    print("  ✅ Listo.\n")


# ── Perfiles de prueba ────────────────────────────────────────────────────────

def transactions_juan_pablo():
    """Usuario actual: joven profesionista, gasto controlado pero utilización alta en crédito."""
    return [
        # Mayo 2026
        tx("income",  14500, "Nómina mayo",       "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("income",   2000, "Proyecto freelance", "🎯 Freelance",       "🎯", dt(2026,5,8,11)),
        tx("expense",  3500, "Renta mayo",         "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  1400, "Súper semanal",      "🍔 Comida",          "🍔", dt(2026,5,3,12)),
        tx("expense",   850, "Gasolina",           "🚗 Transporte",      "🚗", dt(2026,5,5,8)),
        tx("expense",   700, "Telcel",             "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   500, "Internet TELMEX",    "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   350, "Netflix + Spotify",  "🎬 Entretenimiento", "🎬", dt(2026,5,6,10)),
        tx("expense",  1200, "Súper semanal",      "🍔 Comida",          "🍔", dt(2026,5,10,12)),
        tx("expense",   600, "Ropa Liverpool",     "👕 Ropa",            "👕", dt(2026,5,11,15)),
        tx("expense",   400, "Farmacia",           "💊 Salud",           "💊", dt(2026,5,10,11)),
        tx("expense",   300, "Uber",               "🚗 Transporte",      "🚗", dt(2026,5,12,20)),

        # Abril 2026
        tx("income",  14500, "Nómina abril",       "💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("expense",  3500, "Renta abril",        "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  2400, "Comida mes",         "🍔 Comida",          "🍔", dt(2026,4,15,12)),
        tx("expense",  1500, "Transporte abril",   "🚗 Transporte",      "🚗", dt(2026,4,20,8)),
        tx("expense",  1200, "Servicios",          "📱 Servicios",       "📱", dt(2026,4,5,9)),
        tx("expense",  1800, "Salida con amigos",  "🎬 Entretenimiento", "🎬", dt(2026,4,22,20)),
        tx("expense",   800, "Ropa",               "👕 Ropa",            "👕", dt(2026,4,18,15)),

        # Marzo 2026
        tx("income",  14500, "Nómina marzo",       "💼 Nómina",          "💼", dt(2026,3,1,9)),
        tx("expense",  3500, "Renta marzo",        "🏠 Hogar",           "🏠", dt(2026,3,1,10)),
        tx("expense",  2000, "Comida",             "🍔 Comida",          "🍔", dt(2026,3,15,12)),
        tx("expense",  1200, "Transporte",         "🚗 Transporte",      "🚗", dt(2026,3,20,8)),
        tx("expense",  1200, "Servicios",          "📱 Servicios",       "📱", dt(2026,3,5,9)),
        tx("expense",  1200, "Pago mínimo tarjeta","💳 Deudas",          "💳", dt(2026,3,10,10)),
    ]


def credit_profile_juan():
    # Score estimado: ~682 (Bueno, pero utilización alta es el talón de Aquiles)
    return {
        "paymentHistory":  90.0,
        "utilization":     45.0,   # ⚠️ HIGH — main improvement target
        "creditAge":        3.0,
        "creditTypes":      2.0,
        "newApplications":  1.0,
    }


# ── 4 usuarios de prueba ──────────────────────────────────────────────────────

TEST_USERS = [
    {
        "email":       "maria.test.athena@gmail.com",
        "password":    "Athena2026!",
        "displayName": "María González",
        "persona":     "Profesionista 28 años — gana bien pero casi no ahorra",
    },
    {
        "email":       "carlos.test.athena@gmail.com",
        "password":    "Athena2026!",
        "displayName": "Carlos Ramírez",
        "persona":     "Ingeniero 35 años — disciplinado, buen ahorro mensual",
    },
    {
        "email":       "ana.test.athena@gmail.com",
        "password":    "Athena2026!",
        "displayName": "Ana López",
        "persona":     "Freelancer 31 años — excelente score, ya invierte",
    },
    {
        "email":       "pedro.test.athena@gmail.com",
        "password":    "Athena2026!",
        "displayName": "Pedro Hernández",
        "persona":     "Recién graduado 23 años — gastos > ingresos, score muy malo",
    },
]


def transactions_maria():
    """María: marketing, $18k/mes, $16.5k gastos. Score 650 — utilización 65%."""
    return [
        tx("income",  18000, "Nómina mayo",       "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("expense",  5500, "Renta CDMX",        "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  3200, "Comida/restaurantes","🍔 Comida",          "🍔", dt(2026,5,10,13)),
        tx("expense",  2400, "Ropa y accesorios",  "👕 Ropa",            "👕", dt(2026,5,8,15)),
        tx("expense",  1800, "Entretenimiento",    "🎬 Entretenimiento", "🎬", dt(2026,5,12,20)),
        tx("expense",  1200, "Servicios",          "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   900, "Transporte/Uber",    "🚗 Transporte",      "🚗", dt(2026,5,7,18)),
        tx("expense",   600, "Gym + bienestar",    "💊 Salud",           "💊", dt(2026,5,3,10)),
        tx("income",  18000, "Nómina abril",       "💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("expense",  5500, "Renta abril",        "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  3500, "Restaurantes",       "🍔 Comida",          "🍔", dt(2026,4,15,13)),
        tx("expense",  3100, "Ropa shopping",      "👕 Ropa",            "👕", dt(2026,4,20,15)),
        tx("expense",  2000, "Viaje fin de semana","🎬 Entretenimiento", "🎬", dt(2026,4,22,10)),
        tx("expense",  1200, "Servicios",          "📱 Servicios",       "📱", dt(2026,4,5,9)),
    ]


def credit_maria():
    # Score ~645 (Malo) — muy alta utilización, buen historial de pagos
    return {"paymentHistory": 95.0, "utilization": 65.0, "creditAge": 4.0, "creditTypes": 1.0, "newApplications": 2.0}


def transactions_carlos():
    """Carlos: ingeniero con familia, $28k/mes, $21k gastos. Score 735 — disciplinado."""
    return [
        tx("income",  28000, "Nómina mayo",        "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("expense",  9500, "Hipoteca mayo",       "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  4200, "Súper familiar",      "🍔 Comida",          "🍔", dt(2026,5,5,11)),
        tx("expense",  2500, "Colegiatura hijos",   "📚 Educación",       "📚", dt(2026,5,3,9)),
        tx("expense",  1800, "Servicios casa",      "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",  1200, "Gasolina auto",       "🚗 Transporte",      "🚗", dt(2026,5,7,8)),
        tx("expense",   800, "Seguros",             "💊 Salud",           "💊", dt(2026,5,2,10)),
        tx("expense",   600, "Entretenimiento",     "🎬 Entretenimiento", "🎬", dt(2026,5,15,18)),
        tx("income",  28000, "Nómina abril",        "💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("income",   5000, "Bono trimestral",     "🎁 Regalo",          "🎁", dt(2026,4,5,10)),
        tx("expense",  9500, "Hipoteca abril",      "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  4000, "Súper familiar",      "🍔 Comida",          "🍔", dt(2026,4,10,11)),
        tx("expense",  2500, "Colegiatura",         "📚 Educación",       "📚", dt(2026,4,3,9)),
        tx("expense",  2000, "Vacaciones cortas",   "🎬 Entretenimiento", "🎬", dt(2026,4,20,10)),
        tx("expense",  1800, "Servicios",           "📱 Servicios",       "📱", dt(2026,4,5,9)),
    ]


def credit_carlos():
    # Score ~735 (Bueno) — bien en todo, podría diversificar créditos
    return {"paymentHistory": 95.0, "utilization": 28.0, "creditAge": 7.0, "creditTypes": 2.0, "newApplications": 0.0}


def transactions_ana():
    """Ana: freelancer, $15k-22k/mes variable, $10k gastos. Score 785 — excelente."""
    return [
        tx("income",  22000, "Proyecto cliente A",  "🎯 Freelance",       "🎯", dt(2026,5,2,10)),
        tx("income",   8000, "Proyecto cliente B",  "🎯 Freelance",       "🎯", dt(2026,5,9,10)),
        tx("expense",  4000, "Renta mayo",          "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  2200, "Comida saludable",    "🍔 Comida",          "🍔", dt(2026,5,10,12)),
        tx("expense",  1500, "CETES reinversión",   "📈 Inversiones",     "📈", dt(2026,5,5,9)),
        tx("expense",   800, "Transporte",          "🚗 Transporte",      "🚗", dt(2026,5,7,8)),
        tx("expense",   600, "Servicios",           "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   400, "Gym",                 "💊 Salud",           "💊", dt(2026,5,3,7)),
        tx("income",  15000, "Proyecto cliente C",  "🎯 Freelance",       "🎯", dt(2026,4,5,10)),
        tx("income",  10000, "Proyecto cliente D",  "🎯 Freelance",       "🎯", dt(2026,4,20,10)),
        tx("expense",  4000, "Renta abril",         "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  2000, "Comida",              "🍔 Comida",          "🍔", dt(2026,4,15,12)),
        tx("expense",  3000, "Aportación AFORE",    "📈 Inversiones",     "📈", dt(2026,4,3,9)),
        tx("expense",   600, "Servicios",           "📱 Servicios",       "📱", dt(2026,4,5,9)),
        tx("expense",   800, "Transporte",          "🚗 Transporte",      "🚗", dt(2026,4,10,8)),
    ]


def credit_ana():
    # Score ~785 (Muy bueno) — todo en orden, 3 tipos de crédito
    return {"paymentHistory": 98.0, "utilization": 15.0, "creditAge": 5.0, "creditTypes": 3.0, "newApplications": 0.0}


def transactions_pedro():
    """Pedro: recién graduado, $9.5k/mes, $10.2k gastos (negativo). Score 570 — mal."""
    return [
        tx("income",   9500, "Primer empleo mayo",  "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("expense",  3200, "Renta compartida",    "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  2500, "Salidas/antros",      "🎬 Entretenimiento", "🎬", dt(2026,5,10,22)),
        tx("expense",  1500, "Comida",              "🍔 Comida",          "🍔", dt(2026,5,7,13)),
        tx("expense",   900, "Ropa",                "👕 Ropa",            "👕", dt(2026,5,9,15)),
        tx("expense",   700, "Servicios",           "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   600, "Transporte",          "🚗 Transporte",      "🚗", dt(2026,5,6,8)),
        tx("expense",   800, "Deuda tarjeta",       "💳 Deudas",          "💳", dt(2026,5,11,10)),
        tx("income",   9500, "Sueldo abril",        "💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("expense",  3200, "Renta abril",         "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  3000, "Entretenimiento",     "🎬 Entretenimiento", "🎬", dt(2026,4,20,20)),
        tx("expense",  1800, "Comida",              "🍔 Comida",          "🍔", dt(2026,4,15,13)),
        tx("expense",  1200, "Ropa",                "👕 Ropa",            "👕", dt(2026,4,18,15)),
        tx("expense",   800, "Deuda tarjeta",       "💳 Deudas",          "💳", dt(2026,4,10,10)),
        tx("expense",   500, "Servicios",           "📱 Servicios",       "📱", dt(2026,4,5,9)),
    ]


def credit_pedro():
    # Score ~558 (Muy malo) — alta utilización, pagos atrasados, poco historial
    return {"paymentHistory": 65.0, "utilization": 80.0, "creditAge": 1.0, "creditTypes": 1.0, "newApplications": 4.0}


# ── Asignación de datos por usuario ──────────────────────────────────────────

USER_DATA = {
    "maría": (transactions_maria,   credit_maria),
    "carlos": (transactions_carlos, credit_carlos),
    "ana":    (transactions_ana,    credit_ana),
    "pedro":  (transactions_pedro,  credit_pedro),
}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create-test-users", action="store_true",
                        help="Crea los 4 usuarios de prueba y los pobla con datos")
    parser.add_argument("--email",    default="", help="Email del usuario actual")
    parser.add_argument("--password", default="", help="Contraseña del usuario actual")
    args = parser.parse_args()

    if args.create_test_users:
        print("🧑‍🤝‍🧑 Creando 4 usuarios de prueba…\n")
        personas = {
            "maría":  (transactions_maria,   credit_maria),
            "carlos": (transactions_carlos,  credit_carlos),
            "ana":    (transactions_ana,     credit_ana),
            "pedro":  (transactions_pedro,   credit_pedro),
        }
        for i, user_def in enumerate(TEST_USERS):
            key = list(personas.keys())[i]
            tx_fn, cp_fn = personas[key]
            print(f"👤 {user_def['displayName']} — {user_def['persona']}")
            print(f"   Email: {user_def['email']}  |  Password: {user_def['password']}")
            try:
                id_token, uid = sign_up(
                    user_def["email"], user_def["password"], user_def["displayName"]
                )
                # Create base user document
                patch_doc(f"athena_users/{uid}", {
                    "displayName":     user_def["displayName"],
                    "email":           user_def["email"],
                    "createdAt":       datetime.now(timezone.utc),
                }, id_token)
                seed_transactions(uid, id_token, tx_fn(), cp_fn())
            except Exception as e:
                print(f"   ⚠️  Error: {e}\n")
                continue
        print("✅ Usuarios de prueba creados.\n")
        print("Credenciales para la app:")
        for u in TEST_USERS:
            print(f"  {u['email']}  /  {u['password']}")
        return

    # ── Seed usuario actual ───────────────────────────────────────────────────
    print("🌱 Seed de datos para tu usuario de prueba")
    print("=" * 45)
    email    = args.email    or input("Email: ").strip()
    password = args.password or getpass.getpass("Contraseña: ")

    print("\n🔐 Autenticando…")
    try:
        id_token, uid = sign_in(email, password)
    except Exception as e:
        print(f"❌ Error al autenticar: {e}")
        sys.exit(1)
    print(f"   UID: {uid}\n")

    print("💾 Sembrando transacciones y perfil crediticio…")
    seed_transactions(uid, id_token, transactions_juan_pablo(), credit_profile_juan())

    print("✅ Datos cargados en Firestore.")
    print("   Abre la app y ve a Inicio para ver tu resumen financiero.")
    print("   Luego pregúntale a Athena cómo mejorar tu score o tus finanzas.")


if __name__ == "__main__":
    main()
