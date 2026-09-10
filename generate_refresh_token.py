"""
Uso único: cambia un Grant Token (código que da la Zoho API Console,
válido solo por unos minutos) por un Refresh Token permanente.

    python generate_refresh_token.py <GRANT_TOKEN>

El resultado se imprime en pantalla. Copiá el valor de "refresh_token"
a tu archivo .env (ZOHO_REFRESH_TOKEN).
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
DC = os.getenv("ZOHO_DC", "com")
REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", "https://www.zoho.com")


def main():
    if len(sys.argv) != 2:
        print("Uso: python generate_refresh_token.py <GRANT_TOKEN>")
        sys.exit(1)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Falta ZOHO_CLIENT_ID / ZOHO_CLIENT_SECRET en tu .env")
        sys.exit(1)

    grant_token = sys.argv[1]
    url = f"https://accounts.zoho.{DC}/oauth/v2/token"

    resp = requests.post(
        url,
        params={
            "code": grant_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    data = resp.json()
    print(data)

    if "refresh_token" in data:
        print("\n✅ Copiá esto a tu .env como ZOHO_REFRESH_TOKEN:\n")
        print(data["refresh_token"])
    else:
        print("\n⚠️  No se recibió refresh_token. Revisá que el grant token")
        print("    no haya expirado (dura pocos minutos) y que el scope")
        print("    incluya 'access_type=offline' (la API Console lo hace sola).")


if __name__ == "__main__":
    main()
