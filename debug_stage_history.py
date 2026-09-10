"""Script de diagnóstico: muestra el error/respuesta exacta que da Zoho
al consultar Stage_History de un registro puntual."""
import requests
from zoho_auth import get_access_token

RECORD_ID = "7024981000001319229"  # Chuky

url = f"https://www.zohoapis.com/bigin/v2/Pipelines/{RECORD_ID}/Stage_History"
headers = {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}
params = {"fields": "field_label,new_value,old_value,modified_time,modified_by"}

resp = requests.get(url, headers=headers, params=params)
print("STATUS:", resp.status_code)
print("BODY:", resp.text)
