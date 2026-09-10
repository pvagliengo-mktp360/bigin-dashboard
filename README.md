# Bigin Dashboard (Streamlit + Zoho Bigin API v2)

Dashboard de pipeline y de tiempo entre fases ("lead time"), conectado
directo a la API REST de Zoho Bigin.

## 1. Generar credenciales (Self Client)

1. Entrá a https://api-console.zoho.com y creá un **Self Client**.
2. En "Generate Code" pedí los scopes:
   - `ZohoBigin.modules.ALL`
   - `ZohoBigin.settings.ALL`
   (duración 10 minutos). Copiá el **grant token** apenas te lo dé.
3. Completá `ZOHO_CLIENT_ID` y `ZOHO_CLIENT_SECRET` en un archivo `.env`
   (copiá `.env.example` como base).
4. Corré:
   ```bash
   python generate_refresh_token.py <GRANT_TOKEN>
   ```
   Copiá el `refresh_token` que te devuelve a `ZOHO_REFRESH_TOKEN` en el `.env`.
5. Definí `ZOHO_DC` según tu data center (`com`, `eu`, `in`, `com.au`, `jp`, `sa`, `ca`).

## 2. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
```

## 3. Correr el dashboard

```bash
streamlit run app.py
```

## Notas importantes

- En Bigin API v2 el módulo **"Deals" se renombró a "Pipelines"** — el
  código ya usa el nombre correcto en las URLs.
- Los nombres de campo (`Stage`, `Amount`, `Deal_Name`, etc.) son los
  estándar, pero tu instancia puede tener layouts custom. Usá la pestaña
  **Debug / metadata** del dashboard para confirmarlos antes de asumir nada.
- `get_stage_history_bulk` hace **una llamada de API por cada Trato**.
  Con pipelines grandes, esto puede consumir muchos créditos de API por
  día — considerá cachear resultados o correrlo por lotes.
- La regla de negocio de tiempo entre fases está en `metrics.py`:
  - T1 = primera vez que el trato entró a la fase origen.
  - T2 = primera vez que entró a la fase destino (después de T1).
  - Si nunca llegó a la fase destino, se marca `"En progreso"` con el
    tiempo acumulado hasta el momento actual.

## Estructura

```
bigin_dashboard/
├── app.py                     # Dashboard Streamlit (UI)
├── zoho_auth.py                # Manejo de OAuth / access token
├── zoho_api.py                  # Cliente de la API de Bigin
├── metrics.py                    # Cálculo de tiempo entre fases
├── generate_refresh_token.py      # Script único para obtener el refresh token
├── requirements.txt
└── .env.example
```
