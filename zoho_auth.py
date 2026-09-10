"""
Manejo del access token de Zoho Bigin.

El access token dura ~1 hora; este módulo lo cachea en memoria y lo
refresca automáticamente contra el refresh token de larga duración.
"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
DC = os.getenv("ZOHO_DC", "com")  # com | eu | in | com.au | jp | sa | ca

ACCOUNTS_URL = f"https://accounts.zoho.{DC}/oauth/v2/token"

_token_cache = {"access_token": None, "expires_at": 0}


def get_access_token(force_refresh: bool = False) -> str:
    """Devuelve un access token válido, refrescándolo si venció o si
    force_refresh=True (por ejemplo, tras un 401)."""
    now = time.time()
    if (
        not force_refresh
        and _token_cache["access_token"]
        and now < _token_cache["expires_at"] - 60
    ):
        return _token_cache["access_token"]

    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        raise RuntimeError(
            "Faltan credenciales. Configurá ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET "
            "y ZOHO_REFRESH_TOKEN en tu archivo .env (ver .env.example)."
        )

    resp = requests.post(
        ACCOUNTS_URL,
        params={
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Error al refrescar el token de Zoho: {data}")

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return _token_cache["access_token"]
