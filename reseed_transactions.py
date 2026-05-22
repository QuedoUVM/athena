"""
reseed_transactions.py — Re-escribe las transacciones de los 4 usuarios de prueba
usando sus nuevos emails. No toca la cuenta de Juan Pablo.

Cómo correr (en la Mac, NO en Docker):
    python3 reseed_transactions.py
"""
import sys, time, json, requests
from datetime import datetime, timezone

API_KEY    = "AIzaSyBeMgxm8RWVSYwf2Qz_AKTKHJqKB6D8ERI"
PROJECT_ID = "athena-f695a"
DB_ID      = "athena-users"
BASE_FS    = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DB_ID}/documents"
AUTH_URL   = f"https://identitytoolkit.googleapis.com/v1/accounts"

# ── helpers ───────────────────────────────────────────────────────────────────

def dt(y, m, d, h=10):
    return datetime(y, m, d, h, 0, 0, tzinfo=timezone.utc)

def tx(type_, amount, desc, category, emoji, date):
    return {"type": type_, "amount": float(amount), "description": desc,
            "category": category, "emoji": emoji, "date": date}

def _fv(v):
    if isinstance(v, bool):   return {"booleanValue": v}
    if isinstance(v, int):    return {"integerValue": str(v)}
    if isinstance(v, float):  return {"doubleValue": v}
    if isinstance(v, str):    return {"stringValue": v}
    if isinstance(v, datetime): return {"timestampValue": v.strftime("%Y-%m-%dT%H:%M:%SZ")}
    if isinstance(v, dict):   return {"mapValue": {"fields": {k: _fv(vv) for k, vv in v.items()}}}
    if isinstance(v, list):   return {"arrayValue": {"values": [_fv(i) for i in v]}}
    return {"nullValue": None}

def _fields(data): return {"fields": {k: _fv(v) for k, v in data.items()}}

def sign_in(email, password):
    r = requests.post(f"{AUTH_URL}:signInWithPassword?key={API_KEY}",
                      json={"email": email, "password": password, "returnSecureToken": True}, timeout=15)
    if not r.ok: raise Exception(f"sign_in: {r.text}")
    d = r.json(); return d["idToken"], d["localId"]

def create_doc(col_path, data, token):
    r = requests.post(f"{BASE_FS}/{col_path}", json=_fields(data),
                      headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if not r.ok: raise Exception(f"create_doc: {r.status_code} {r.text[:120]}")

def patch_doc(doc_path, data, token):
    mask = "&".join(f"updateMask.fieldPaths={k}" for k in data.keys())
    r = requests.patch(f"{BASE_FS}/{doc_path}?{mask}", json=_fields(data),
                       headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if not r.ok: raise Exception(f"patch_doc: {r.status_code} {r.text[:120]}")

def list_tx_ids(uid, token):
    """List existing transaction doc IDs so we can avoid duplicates."""
    r = requests.get(f"{BASE_FS}/athena_users/{uid}/transactions?pageSize=100",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if not r.ok: return []
    return [d["name"].split("/")[-1] for d in r.json().get("documents", [])]

def delete_doc(path, token):
    requests.delete(f"{BASE_FS}/{path}",
                    headers={"Authorization": f"Bearer {token}"}, timeout=15)

# ── Datos de transacciones ────────────────────────────────────────────────────

def transactions_oscar():   # ex-maría  — marketing 28 años, utilización 65%
    return [
        tx("income",  18000,"Nómina mayo",       "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("expense",  5500,"Renta CDMX",        "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  3200,"Comida/restaurantes","🍔 Comida",          "🍔", dt(2026,5,10,13)),
        tx("expense",  2400,"Ropa y accesorios",  "👕 Ropa",            "👕", dt(2026,5,8,15)),
        tx("expense",  1800,"Entretenimiento",    "🎬 Entretenimiento", "🎬", dt(2026,5,12,20)),
        tx("expense",  1200,"Servicios",          "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   900,"Transporte/Uber",    "🚗 Transporte",      "🚗", dt(2026,5,7,18)),
        tx("expense",   600,"Gym + bienestar",    "💊 Salud",           "💊", dt(2026,5,3,10)),
        tx("income",  18000,"Nómina abril",       "💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("expense",  5500,"Renta abril",        "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  3500,"Restaurantes",       "🍔 Comida",          "🍔", dt(2026,4,15,13)),
        tx("expense",  3100,"Ropa shopping",      "👕 Ropa",            "👕", dt(2026,4,20,15)),
        tx("expense",  2000,"Viaje fin de semana","🎬 Entretenimiento", "🎬", dt(2026,4,22,10)),
        tx("expense",  1200,"Servicios",          "📱 Servicios",       "📱", dt(2026,4,5,9)),
    ]

def credit_oscar():
    return {"paymentHistory":95.0,"utilization":65.0,"creditAge":4.0,"creditTypes":1.0,"newApplications":2.0}

def transactions_gabriel():  # ex-carlos — ingeniero 35 años, score 735
    return [
        tx("income",  28000,"Nómina mayo",       "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("expense",  9500,"Hipoteca mayo",      "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  4200,"Súper familiar",     "🍔 Comida",          "🍔", dt(2026,5,5,11)),
        tx("expense",  2500,"Colegiatura hijos",  "📚 Educación",       "📚", dt(2026,5,3,9)),
        tx("expense",  1800,"Servicios casa",     "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",  1200,"Gasolina auto",      "🚗 Transporte",      "🚗", dt(2026,5,7,8)),
        tx("expense",   800,"Seguros",            "💊 Salud",           "💊", dt(2026,5,2,10)),
        tx("expense",   600,"Entretenimiento",    "🎬 Entretenimiento", "🎬", dt(2026,5,15,18)),
        tx("income",  28000,"Nómina abril",       "💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("income",   5000,"Bono trimestral",    "🎁 Regalo",          "🎁", dt(2026,4,5,10)),
        tx("expense",  9500,"Hipoteca abril",     "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  4000,"Súper familiar",     "🍔 Comida",          "🍔", dt(2026,4,10,11)),
        tx("expense",  2500,"Colegiatura",        "📚 Educación",       "📚", dt(2026,4,3,9)),
        tx("expense",  2000,"Vacaciones cortas",  "🎬 Entretenimiento", "🎬", dt(2026,4,20,10)),
        tx("expense",  1800,"Servicios",          "📱 Servicios",       "📱", dt(2026,4,5,9)),
    ]

def credit_gabriel():
    return {"paymentHistory":95.0,"utilization":28.0,"creditAge":7.0,"creditTypes":2.0,"newApplications":0.0}

def transactions_mariel():  # ex-ana — freelancer 31 años, score 785
    return [
        tx("income",  22000,"Proyecto cliente A", "🎯 Freelance",       "🎯", dt(2026,5,2,10)),
        tx("income",   8000,"Proyecto cliente B", "🎯 Freelance",       "🎯", dt(2026,5,9,10)),
        tx("expense",  4000,"Renta mayo",         "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  2200,"Comida saludable",   "🍔 Comida",          "🍔", dt(2026,5,10,12)),
        tx("expense",  1500,"CETES reinversión",  "📈 Inversiones",     "📈", dt(2026,5,5,9)),
        tx("expense",   800,"Transporte",         "🚗 Transporte",      "🚗", dt(2026,5,7,8)),
        tx("expense",   600,"Servicios",          "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   400,"Gym",                "💊 Salud",           "💊", dt(2026,5,3,7)),
        tx("income",  15000,"Proyecto cliente C", "🎯 Freelance",       "🎯", dt(2026,4,5,10)),
        tx("income",  10000,"Proyecto cliente D", "🎯 Freelance",       "🎯", dt(2026,4,20,10)),
        tx("expense",  4000,"Renta abril",        "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  2000,"Comida",             "🍔 Comida",          "🍔", dt(2026,4,15,12)),
        tx("expense",  3000,"Aportación AFORE",   "📈 Inversiones",     "📈", dt(2026,4,3,9)),
        tx("expense",   600,"Servicios",          "📱 Servicios",       "📱", dt(2026,4,5,9)),
        tx("expense",   800,"Transporte",         "🚗 Transporte",      "🚗", dt(2026,4,10,8)),
    ]

def credit_mariel():
    return {"paymentHistory":98.0,"utilization":15.0,"creditAge":5.0,"creditTypes":3.0,"newApplications":0.0}

def transactions_alexis():  # ex-pedro — recién graduado 23 años, balance negativo
    return [
        tx("income",   9500,"Primer empleo mayo", "💼 Nómina",          "💼", dt(2026,5,1,9)),
        tx("expense",  3200,"Renta compartida",   "🏠 Hogar",           "🏠", dt(2026,5,1,10)),
        tx("expense",  2500,"Salidas/antros",     "🎬 Entretenimiento", "🎬", dt(2026,5,10,22)),
        tx("expense",  1500,"Comida",             "🍔 Comida",          "🍔", dt(2026,5,7,13)),
        tx("expense",   800,"Transporte",         "🚗 Transporte",      "🚗", dt(2026,5,5,8)),
        tx("expense",   700,"Servicios",          "📱 Servicios",       "📱", dt(2026,5,5,9)),
        tx("expense",   600,"Ropa",               "👕 Ropa",            "👕", dt(2026,5,9,15)),
        tx("expense",   500,"Gym",                "💊 Salud",           "💊", dt(2026,5,3,7)),
        tx("income",   9500,"Primer empleo abril","💼 Nómina",          "💼", dt(2026,4,1,9)),
        tx("expense",  3200,"Renta abril",        "🏠 Hogar",           "🏠", dt(2026,4,1,10)),
        tx("expense",  3000,"Viaje con amigos",   "🎬 Entretenimiento", "🎬", dt(2026,4,20,10)),
        tx("expense",  1800,"Comida",             "🍔 Comida",          "🍔", dt(2026,4,15,13)),
        tx("expense",   900,"Transporte",         "🚗 Transporte",      "🚗", dt(2026,4,10,8)),
        tx("expense",   700,"Servicios",          "📱 Servicios",       "📱", dt(2026,4,5,9)),
        tx("expense",   600,"Deuda tarjeta",      "💳 Deudas",          "💳", dt(2026,4,10,10)),
    ]

def credit_alexis():
    return {"paymentHistory":65.0,"utilization":80.0,"creditAge":1.0,"creditTypes":1.0,"newApplications":4.0}

# ── Usuarios a re-seedear ─────────────────────────────────────────────────────

USERS = [
    {"email": "oscar.athena@gmail.com",   "name": "Oscar Dominguez",   "txs": transactions_oscar,   "cp": credit_oscar},
    {"email": "gabriel.athena@gmail.com", "name": "Gabriel Guerrero",  "txs": transactions_gabriel, "cp": credit_gabriel},
    {"email": "mariel.athena@gmail.com",  "name": "Mariel Perez",      "txs": transactions_mariel,  "cp": credit_mariel},
    {"email": "alexis.athena@gmail.com",  "name": "Alexis Nava",       "txs": transactions_alexis,  "cp": credit_alexis},
]

# ── Main ──────────────────────────────────────────────────────────────────────

def seed_user(u):
    print(f"\n{'─'*55}")
    print(f"  {u['name']}  ({u['email']})")
    print(f"{'─'*55}")

    token, uid = sign_in(u["email"], "Athena2026!")
    print(f"  UID: {uid}")

    # Borrar transacciones vacías que dejó la migración anterior
    old_ids = list_tx_ids(uid, token)
    if old_ids:
        print(f"  🗑  Borrando {len(old_ids)} docs vacíos anteriores…")
        for doc_id in old_ids:
            delete_doc(f"athena_users/{uid}/transactions/{doc_id}", token)
            time.sleep(0.05)

    # Escribir transacciones frescas
    txs = u["txs"]()
    print(f"  💾 Escribiendo {len(txs)} transacciones…")
    for t in txs:
        create_doc(f"athena_users/{uid}/transactions", t, token)
        time.sleep(0.12)

    # Perfil crediticio
    cp = u["cp"]()
    patch_doc(f"athena_users/{uid}", {"creditProfile": cp}, token)
    print(f"  ✅ Listo")


def main():
    print("=== Re-seed de transacciones ===")
    ok, fail = 0, 0
    for u in USERS:
        try:
            seed_user(u)
            ok += 1
        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
            fail += 1
    print(f"\n\n{'='*55}")
    print(f"  Resultado: {ok} ✅  {fail} ❌")

if __name__ == "__main__":
    main()
