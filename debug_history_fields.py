"""Consulta los campos disponibles del módulo interno DealHistory
(el que respalda a Stage_History), para saber los nombres exactos."""
import json

import requests

from zoho_auth import get_access_token

url = "https://www.zohoapis.com/bigin/v2/settings/fields"
headers = {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}
params = {"module": "DealHistory"}

resp = requests.get(url, headers=headers, params=params)
print("STATUS:", resp.status_code)
try:
    data = resp.json()
    # Solo mostramos api_name y label de cada campo, para que sea más corto
    fields = data.get("fields", [])
    for f in fields:
        print(f.get("api_name"), "->", f.get("field_label"))
    if not fields:
        print(json.dumps(data, indent=2))
except ValueError:
    print(resp.text)
