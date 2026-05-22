"""
update_auth_users.py — Sincroniza el email y displayName en Firebase Auth
para que coincidan con lo que ya tienes en Firestore.

Cómo correr (en la Mac, NO en Docker):
    cd /Users/quedojp/dev/school/athena
    python update_auth_users.py
"""

import requests

API_KEY  = "AIzaSyBeMgxm8RWVSYwf2Qz_AKTKHJqKB6D8ERI"
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
PASSWORD = "Athena2026!"

# (email_viejo, email_nuevo, displayName_nuevo)
UPDATES = [
    ("pedro.test.athena@gmail.com", "alexis.athena@gmail.com",  "Alexis Nava"),
    ("ana.test.athena@gmail.com",   "mariel.athena@gmail.com",  "Mariel Perez"),
    ("carlos.test.athena@gmail.com","gabriel.athena@gmail.com", "Gabriel Guerrero"),
    ("maria.test.athena@gmail.com", "oscar.athena@gmail.com",   "Oscar Dominguez"),
]


def sign_in(email: str, password: str) -> str:
    r = requests.post(
        f"{AUTH_URL}:signInWithPassword?key={API_KEY}",
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=15,
    )
    if not r.ok:
        raise requests.HTTPError(f"sign_in {r.status_code}: {r.text}", response=r)
    return r.json()["idToken"]


def update_user(id_token: str, new_email: str, display_name: str):
    r = requests.post(
        f"{AUTH_URL}:update?key={API_KEY}",
        json={
            "idToken":     id_token,
            "email":       new_email,
            "displayName": display_name,
            "returnSecureToken": True,
        },
        timeout=15,
    )
    if not r.ok:
        raise requests.HTTPError(f"update {r.status_code}: {r.text}", response=r)
    return r.json()


def main():
    for old_email, new_email, name in UPDATES:
        print(f"\n→ {old_email}")
        try:
            token = sign_in(old_email, PASSWORD)
            result = update_user(token, new_email, name)
            print(f"  ✅  {result.get('email')}  |  {result.get('displayName')}")
        except requests.HTTPError as e:
            print(f"  ❌  {e}")
        except Exception as e:
            print(f"  ❌  {e}")

    print("\nListo.")


if __name__ == "__main__":
    main()
