# API setup

## OpenF1
Historical endpoints are generally accessible without authentication. Configure `OPENF1_API_KEY` in `.env` or Streamlit Cloud Secrets if your OpenF1 plan supplies a bearer token. Username/password fields are also supported for the existing live-stream authentication path. Never commit secrets.

## Jolpica
Jolpica is used for season schedules, race results, qualifying and championship standings. No credential is embedded in this project.

## Status labels
Provider data is live only when fetched from a currently active session endpoint. Historical championship/schedule endpoints are historical/reference data. Cached dashboard queries are cached provider responses, not live guarantees. A missing or failed provider response is displayed as an error/unavailable state.
