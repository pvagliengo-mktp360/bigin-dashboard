"""
Cliente delgado para la API v2 de Zoho Bigin.

Nota clave: en Bigin API v2, el módulo que antes se llamaba "Deals" se
renombró a "Pipelines" (aplica a URLs, scopes y respuestas).
"""
import os
import time

import pandas as pd
import requests

from zoho_auth import get_access_token

DC = os.getenv("ZOHO_DC", "com")
BASE_URL = f"https://www.zohoapis.{DC}/bigin/v2"

MODULE = "Pipelines"  # antes "Deals"


def _headers():
    return {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}


def _get(path, params=None):
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    if resp.status_code == 401:
        # token vencido -> refrescar una vez y reintentar
        get_access_token(force_refresh=True)
        resp = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_related_lists(module: str = MODULE):
    """Related lists disponibles para el módulo. Útil para confirmar el
    api_name exacto de 'Stage History' en tu instancia (pestaña Debug)."""
    return _get("/settings/related_lists", params={"module": module})


def get_fields_metadata(module: str = MODULE):
    """Nombres reales de los campos (por si tu pipeline usa etiquetas
    distintas a Stage/Amount/Deal_Name)."""
    return _get("/settings/fields", params={"module": module})


def get_pipeline_records(fields, page: int = 1, per_page: int = 200):
    params = {"fields": ",".join(fields), "page": page, "per_page": per_page}
    return _get(f"/{MODULE}", params=params)


def get_all_pipeline_records(fields, max_pages: int = 25) -> pd.DataFrame:
    """Trae todos los registros paginando. `fields` es obligatorio en v2."""
    all_records = []
    page = 1
    while page <= max_pages:
        data = get_pipeline_records(fields, page=page)
        records = data.get("data", [])
        if not records:
            break
        all_records.extend(records)
        if not data.get("info", {}).get("more_records"):
            break
        page += 1
        time.sleep(0.2)  # cuidar el rate limit
    return pd.DataFrame(all_records)


STAGE_HISTORY_FIELDS = [
    "Stage",
    "Modified_Time",
    "Moved_To__s",
    "Stage_Duration_Calendar_Days",
]


def get_stage_history(record_id: str, related_list_api_name: str = "Stage_History"):
    params = {"fields": ",".join(STAGE_HISTORY_FIELDS)}
    data = _get(f"/{MODULE}/{record_id}/{related_list_api_name}", params=params)
    return data.get("data", [])


def get_stage_history_bulk(record_ids, related_list_api_name: str = "Stage_History"):
    """Trae el historial de etapas de una lista de registros.
    Hace 1 llamada por registro: para pipelines grandes, revisá tu límite
    diario de créditos de API antes de correrlo sobre todo el dataset."""
    history = {}
    for rid in record_ids:
        try:
            history[rid] = get_stage_history(rid, related_list_api_name)
        except requests.HTTPError:
            history[rid] = []
        time.sleep(0.15)
    return history
