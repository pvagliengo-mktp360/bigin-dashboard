"""
Prueba rápida y con progreso visible del cálculo de tiempo entre fases,
sin pasar por Streamlit. Usa solo los primeros N tratos para ir rápido.
"""
from zoho_api import get_all_pipeline_records, get_stage_history
from metrics import lead_time_between_stages

N_TRATOS_DE_PRUEBA = 5  # cambiá este número si querés probar con más

STAGE_ORIGEN = "Etapa inicial"
STAGE_DESTINO = "Activo"

print("1. Trayendo tratos...")
fields = ["Deal_Name", "Stage"]
deals_df = get_all_pipeline_records(fields)
print(f"   Total de tratos traídos: {len(deals_df)}")

muestra = deals_df.head(N_TRATOS_DE_PRUEBA)
print(f"2. Probando con los primeros {len(muestra)} tratos...\n")

for _, deal in muestra.iterrows():
    rid = deal["id"]
    nombre = deal.get("Deal_Name", rid)
    print(f"--- Trato: {nombre} (id={rid}) ---")
    try:
        historial = get_stage_history(rid)
        print(f"    Eventos en Stage_History: {len(historial)}")
        if historial:
            print(f"    Ejemplo de evento crudo: {historial[0]}")
        resultado = lead_time_between_stages(historial, STAGE_ORIGEN, STAGE_DESTINO)
        print(f"    Resultado: {resultado}")
    except Exception as e:
        print(f"    ERROR: {e}")
    print()

print("Listo.")
