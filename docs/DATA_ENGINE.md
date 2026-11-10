# F1 Data Engine

This extension preserves the existing Arcade replay and PySide6 desktop UI and adds an independent provider/data layer.

## Providers and real coverage

- **Jolpica**: historical calendar, race results, qualifying, sprint results and championship standings through Ergast-compatible endpoints. Uses `limit`/`offset` pagination and a custom User-Agent. No API key is needed.
- **OpenF1**: historical data from 2023 onward is available without authentication. Real-time access requires a subscription and OAuth2 credentials. The REST client refreshes its one-hour token early and retries once after an authorization failure.
- **FastF1**: loads historical sessions and telemetry using the project's existing cache. FastF1 supports schedule/results back to 1950, while detailed timing/telemetry is generally available from 2018 onward.

The official F1/FIA websites are not scraped. This implementation does not bypass access controls or claim an unofficial feed is official.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `config/.env.example` to `.env`.
3. Add OpenF1 credentials only if you have an active subscription. Never commit `.env`.
4. Run a sync from Python:

```python
from services.synchronization_service import SynchronizationService
sync = SynchronizationService()
print(sync.sync_jolpica_season(2026))
print(sync.sync_openf1_season(2026))
```

5. Database is created at `data/f1_data.sqlite3` by default.

## Operating modes

- `HISTORICAL`: completed-session/provider history.
- `CACHED`: a previously stored payload is being shown.
- `LIVE`: only use after a live authenticated stream is actually connected and receiving timestamped messages.
- `OFFLINE`: no network provider available.
- `SIMULATION`: generated data, if a simulation feature is explicitly enabled.

The initial extension provides authenticated OpenF1 REST access and provider-ready live credentials. MQTT/WebSocket live ingestion is intentionally not labelled complete until the broker client is installed, connected and validated against a subscribed session. Do not mark REST polling or cached records as LIVE.

## Limitations

The database stores raw provider payloads with provider, dataset, season, retrieval timestamp and source URL. It is designed as a safe incremental foundation; it does not claim to have downloaded every season or every historical telemetry sample merely by installing the application. Historical backfill should be run season-by-season and respects provider availability/rate limits.
