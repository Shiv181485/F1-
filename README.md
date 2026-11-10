# F1 Race Replay — Data Control Center

A dual-interface Formula 1 analytics project: the existing Python/Arcade/PySide6 replay desktop app plus a Streamlit web dashboard sharing the existing provider clients and SQLite repository.

## Run the web app
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Run the desktop app
Install the desktop extras with `pip install -r requirements-desktop.txt`, then `python main.py`. The desktop interface requires a graphical Windows/Linux desktop and its original dependencies.

## Data integrity
SQLite records are upserted using a normalized composite key. Missing key values are represented by stable sentinels so SQLite's NULL uniqueness semantics cannot create duplicates. Local SQLite is not durable on Streamlit Community Cloud restarts.

## Data provenance
The web UI queries OpenF1 and Jolpica endpoints. Missing provider data is shown as unavailable; the application does not generate fictional live timing or standings. OpenF1 live access may require account credentials or a subscription. Historical Jolpica data is queried separately.

## Deployment
See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md), [API_SETUP.md](API_SETUP.md), [INSTALLATION.md](INSTALLATION.md), and [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## Known limitations
- Cloud PostgreSQL persistence is documented as an external deployment requirement; this package currently uses SQLite locally and does not yet ship a PostgreSQL repository adapter.
- OpenF1 live feed / live subscription entitlement cannot be verified without user credentials and an active session.
- Circuit corner labels and official track maps are not fabricated; Circuit Explorer plots provider location samples where available.
- Some desktop imports and GUI startup require PySide6, Arcade, FastF1 and a graphical environment.
