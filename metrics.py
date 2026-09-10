"""
Implementa la regla de negocio del skill: tiempo transcurrido entre dos
fases de un Trato, usando el related list Stage_History.
"""
import pandas as pd


def _parse_stage_events(stage_history_records, stage_field="Stage", time_field="Modified_Time"):
    """Normaliza Stage_History a una lista [(etapa, timestamp), ...] ordenada."""
    events = []
    for rec in stage_history_records:
        stage = rec.get(stage_field) or rec.get("stage")
        ts_raw = rec.get(time_field) or rec.get("modified_time")
        if stage is None or ts_raw is None:
            continue
        try:
            ts = pd.to_datetime(ts_raw, utc=True)
        except (ValueError, TypeError):
            continue
        events.append((stage, ts))
    events.sort(key=lambda x: x[1])
    return events


def lead_time_between_stages(
    stage_history_records,
    stage_origen,
    stage_destino,
    stage_field="Stage",
    time_field="Modified_Time",
):
    """
    T1 = primer timestamp de entrada a stage_origen.
    T2 = primer timestamp de entrada a stage_destino, posterior a T1.
    delta = T2 - T1.
    Si el trato no llegó a stage_destino: estado 'En progreso' con el
    tiempo acumulado hasta el momento actual.
    """
    events = _parse_stage_events(stage_history_records, stage_field, time_field)

    t1 = next((ts for st, ts in events if st == stage_origen), None)
    if t1 is None:
        return {"estado": "sin_dato", "t1": None, "t2": None, "delta_dias": None, "delta_horas": None}

    t2 = next((ts for st, ts in events if st == stage_destino and ts >= t1), None)

    if t2 is not None:
        delta = t2 - t1
        return {
            "estado": "completado",
            "t1": t1,
            "t2": t2,
            "delta_dias": round(delta.total_seconds() / 86400, 2),
            "delta_horas": round(delta.total_seconds() / 3600, 2),
        }

    ahora = pd.Timestamp.now(tz="UTC")
    delta = ahora - t1
    return {
        "estado": "En progreso",
        "t1": t1,
        "t2": None,
        "delta_dias": round(delta.total_seconds() / 86400, 2),
        "delta_horas": round(delta.total_seconds() / 3600, 2),
    }


def build_lead_time_dataframe(
    deals_df, stage_history_by_id, stage_origen, stage_destino,
    id_field="id", name_field="Deal_Name",
):
    rows = []
    for _, deal in deals_df.iterrows():
        rid = deal[id_field]
        history = stage_history_by_id.get(rid, [])
        result = lead_time_between_stages(history, stage_origen, stage_destino)
        rows.append({
            "id": rid,
            "nombre": deal.get(name_field, rid),
            "estado": result["estado"],
            "entro_a_origen": result["t1"],
            "entro_a_destino": result["t2"],
            "dias": result["delta_dias"],
            "horas": result["delta_horas"],
        })
    return pd.DataFrame(rows)
