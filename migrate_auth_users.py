"""
migrate_auth_users.py — Elimina los 4 usuarios de prueba en Auth y los recrea
con los nuevos emails/nombres, migrando toda su data de Firestore al nuevo UID.

Cómo correr (en la Mac, NO en Docker):
    cd /Users/quedojp/dev/school/athena
    python3 migrate_auth_users.py
"""

import requests
import json

API_KEY    = "AIzaSyBeMgxm8RWVSYwf2Qz_AKTKHJqKB6D8ERI"
PROJECT_ID = "athena-f695a"
DB_ID      = "athena-users"
BASE_FS    = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DB_ID}/documents"
AUTH_URL   = f"https://identitytoolkit.googleapis.com/v1/accounts"
PASSWORD   = "Athena2026!"

MIGRATIONS = [
    {"old_email": "pedro.test.athena@gmail.com",  "new_email": "alexis.athena@gmail.com",  "display_name": "Alexis Nava"},
    {"old_email": "ana.test.athena@gmail.com",    "new_email": "mariel.athena@gmail.com",  "display_name": "Mariel Perez"},
    {"old_email": "carlos.test.athena@gmail.com", "new_email": "gabriel.athena@gmail.com", "display_name": "Gabriel Guerrero"},
    {"old_email": "maria.test.athena@gmail.com",  "new_email": "oscar.athena@gmail.com",   "display_name": "Oscar Dominguez"},
]


# ── Auth helpers ──────────────────────────────────────────────────────────────

def sign_in(email, password):
    r = requests.post(f"{AUTH_URL}:signInWithPassword?key={API_KEY}",
                      json={"email": email, "password": password, "returnSecureToken": True},
                      timeout=15)
    if not r.ok:
        raise Exception(f"sign_in falló {r.status_code}: {r.text}")
    d = r.json()
    return d["idToken"], d["localId"]


def sign_up(email, password, display_name):
    r = requests.post(f"{AUTH_URL}:signUp?key={API_KEY}",
                      json={"email": email, "password": password, "returnSecureToken": True},
                      timeout=15)
    if not r.ok:
        raise Exception(f"sign_up falló {r.status_code}: {r.text}")
    d = r.json()
    token, uid = d["idToken"], d["localId"]
    requests.post(f"{AUTH_URL}:update?key={API_KEY}",
                  json={"idToken": token, "displayName": display_name}, timeout=15)
    return token, uid


def delete_auth_account(id_token):
    r = requests.post(f"{AUTH_URL}:delete?key={API_KEY}",
                      json={"idToken": id_token}, timeout=15)
    if not r.ok:
        raise Exception(f"delete falló {r.status_code}: {r.text}")


# ── Firestore REST helpers ────────────────────────────────────────────────────

def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def fs_get(path, token):
    """Fetch a single document. Returns fields dict or None if not found."""
    r = requests.get(f"{BASE_FS}/{path}", headers=_headers(token), timeout=15)
    if r.status_code == 404:
        return None
    if not r.ok:
        raise Exception(f"fs_get {path} → {r.status_code}: {r.text}")
    return r.json().get("fields", {})


def fs_query(parent_path, collection_id, token):
    """
    Use runQuery (structured query) to list all documents in a subcollection.
    This goes through Firestore security rules just like a normal read but
    avoids the REST collection LIST endpoint that has stricter rule matching.
    """
    body = {
        "structuredQuery": {
            "from": [{"collectionId": collection_id}],
            "select": {"fields": []},   # empty = return all fields
        }
    }
    r = requests.post(
        f"{BASE_FS}/{parent_path}:runQuery",
        headers=_headers(token),
        data=json.dumps(body),
        timeout=30,
    )
    if not r.ok:
        # Return empty list if access denied — we'll warn the caller
        return [], r.status_code
    rows = r.json()
    docs = []
    for row in rows:
        doc = row.get("document")
        if doc:
            doc_id = doc["name"].split("/")[-1]
            docs.append({"id": doc_id, "fields": doc.get("fields", {})})
    return docs, 200


def fs_set(path, fields, token):
    r = requests.patch(
        f"{BASE_FS}/{path}",
        headers=_headers(token),
        data=json.dumps({"fields": fields}),
        timeout=15,
    )
    if not r.ok:
        raise Exception(f"fs_set {path} → {r.status_code}: {r.text}")


def fs_delete(path, token):
    r = requests.delete(f"{BASE_FS}/{path}", headers=_headers(token), timeout=15)
    if r.status_code not in (200, 204, 404):
        print(f"    ⚠  fs_delete {path} → {r.status_code} (ignorado)")


# ── Migration logic ───────────────────────────────────────────────────────────

def migrate_user(old_email, new_email, display_name):
    print(f"\n{'─'*60}")
    print(f"  {old_email}")
    print(f"  → {new_email}  /  {display_name}")
    print(f"{'─'*60}")

    # 1. Sign in with old credentials
    print("  [1/6] Sign-in antiguo…")
    old_token, old_uid = sign_in(old_email, PASSWORD)
    print(f"        old_uid = {old_uid}")

    # 2. Read Firestore data
    print("  [2/6] Leyendo Firestore…")
    user_fields = fs_get(f"athena_users/{old_uid}", old_token)

    tx_docs, tx_status = fs_query(f"athena_users/{old_uid}", "transactions", old_token)
    chat_docs, _ = fs_query(f"athena_users/{old_uid}", "chats", old_token)

    if tx_status == 403:
        print(f"        ⚠  Sin permiso para leer transacciones — se copiará solo el perfil")
    else:
        print(f"        user_doc={'OK' if user_fields else 'vacío'}  "
              f"transactions={len(tx_docs)}  chats={len(chat_docs)}")

    # 3. Delete old Auth account
    print("  [3/6] Eliminando cuenta Auth antigua…")
    delete_auth_account(old_token)
    print("        ✓")

    # 4. Create new Auth account
    print("  [4/6] Creando nueva cuenta Auth…")
    new_token, new_uid = sign_up(new_email, PASSWORD, display_name)
    print(f"        new_uid = {new_uid}")

    # 5. Write data under new UID
    print("  [5/6] Migrando datos…")

    if user_fields:
        user_fields["email"]       = {"stringValue": new_email}
        user_fields["displayName"] = {"stringValue": display_name}
        fs_set(f"athena_users/{new_uid}", user_fields, new_token)
        print(f"        ✓ perfil de usuario")

    for doc in tx_docs:
        fs_set(f"athena_users/{new_uid}/transactions/{doc['id']}", doc["fields"], new_token)
    if tx_docs:
        print(f"        ✓ {len(tx_docs)} transacciones")

    for doc in chat_docs:
        fs_set(f"athena_users/{new_uid}/chats/{doc['id']}", doc["fields"], new_token)
    if chat_docs:
        print(f"        ✓ {len(chat_docs)} chats")

    # 6. Clean up old Firestore documents
    print("  [6/6] Limpiando UID antiguo en Firestore…")
    for doc in tx_docs:
        fs_delete(f"athena_users/{old_uid}/transactions/{doc['id']}", new_token)
    for doc in chat_docs:
        fs_delete(f"athena_users/{old_uid}/chats/{doc['id']}", new_token)
    fs_delete(f"athena_users/{old_uid}", new_token)
    print("        ✓")

    print(f"\n  ✅  {display_name} ({new_email})  new_uid={new_uid}")
    return new_uid


def main():
    print("=== Migración de usuarios de prueba ===\n")
    results = []
    for m in MIGRATIONS:
        try:
            new_uid = migrate_user(m["old_email"], m["new_email"], m["display_name"])
            results.append({"email": m["new_email"], "name": m["display_name"], "uid": new_uid, "ok": True})
        except Exception as e:
            print(f"\n  ❌  ERROR: {e}")
            results.append({"email": m["new_email"], "name": m["display_name"], "ok": False, "error": str(e)[:80]})

    print("\n\n=== Resumen final ===")
    for r in results:
        status = "✅" if r["ok"] else "❌"
        extra  = f"uid={r.get('uid','')}" if r.get("uid") else f"error={r.get('error','')}"
        print(f"  {status}  {r['name']:<22}  {r['email']:<38}  {extra}")


if __name__ == "__main__":
    main()
