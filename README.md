# F1 Race Replay Data Control Center

<p align="center">
  <img src="https://img.shields.io/badge/Formula%201-Analytics%20Control%20Center-red?style=for-the-badge" alt="F1 Analytics Control Center" />
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge" alt="Streamlit Dashboard" />
  <img src="https://img.shields.io/badge/SQLite-Local%20Data%20Store-5A5A5A?style=for-the-badge" alt="SQLite" />
</p>

<p align="center">
  <img src="https://images.unsplash.com/photo-1549365814-3f1f4a2f0d8a?auto=format&fit=crop&w=1400&q=80" alt="F1 car on track" width="100%" />
</p>

A premium Formula 1 telemetry and race intelligence platform built for live timing, lap analysis, strategy review, and replay workflows. This project combines a data-rich Streamlit control center with a desktop-grade racing interface, giving you a complete operational picture of sessions, drivers, tyres, and performance trends.

## Why this project stands out

- Real-time and historical race data workflows for F1 analysis
- High-contrast, race-control inspired dashboard UX
- Driver, constructor, circuit, and telemetry insights in one place
- Local SQLite storage with sync-ready dataset management
- Replay, strategy, and pit-wall style views for deeper racing analysis

## Dashboard preview

<p align="center">
  <img src="resources/preview.png" alt="F1 control center homepage preview" width="100%" />
</p>

## Key features

### Race intelligence dashboard
- Session overview cards and KPI summaries
- Live timing style status blocks
- Local dataset health and sync tracking
- Grid, lap, tyre, and performance summaries

### Telemetry and strategy analysis
- Circuit explorer and telemetry views
- Tyre-degradation strategy insights
- Driver comparison and historical race review
- Pit wall style operational analysis

### Data layer
- OpenF1 and Jolpica source integration
- SQLite repository with idempotent dataset tracking
- Cached local records for performance and continuity
- Export-friendly data handling for downstream analysis

## Screenshots

<div align="center">
  <table>
    <tr>
      <td width="50%">
        <img src="resources/insights-menu.png" alt="Insights view" width="100%" />
      </td>
      <td width="50%">
        <img src="resources/pit-wall-window-template.png" alt="Pit wall template" width="100%" />
      </td>
    </tr>
    <tr>
      <td width="50%">
        <img src="resources/gui-menu.png" alt="GUI menu" width="100%" />
      </td>
      <td width="50%">
        <img src="resources/telemetry-logger.png" alt="Telemetry logger" width="100%" />
      </td>
    </tr>
  </table>
</div>

## Analytics and graph views

The platform is designed to present race data in a way that feels like a Formula 1 operations room: charts, distribution views, tyre wear, timing deltas, and race strategy overlays are all surfaced in a performance-focused layout.

<p align="center">
  <img src="resources/preview.png" alt="Race charts and dashboard graphs" width="100%" />
</p>

## Quick start

### Web app
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Desktop app
```powershell
pip install -r requirements-desktop.txt
python main.py
```

## Project architecture

```text
F1-Race-Replay-Data-Control-Center/
├── app/                  # shared data access and service layers
├── database/             # SQLite repository and persistence logic
├── services/             # provider and sync orchestration services
├── src/                  # replay, telemetry, GUI, and strategy modules
├── tests/                # project validation suite
├── resources/            # screenshots and product imagery
├── streamlit_app.py      # main dashboard entry point
├── main.py               # desktop app entry point
├── requirements.txt
├── requirements-desktop.txt
├── README.md
├── STREAMLIT_DEPLOYMENT.md
├── INSTALLATION.md
└── API_SETUP.md
```

## Data sources and reliability

This project is built around provider-backed F1 data, using OpenF1 and Jolpica sources when available. Where provider data is missing or a session is unavailable, the app gracefully surfaces the status instead of inventing data.

- Local SQLite persistence for cached and retrieved data
- Provider-aware dataset handling for sessions and race information
- Safe fallback messaging for unavailable or incomplete source data

## Deployment notes

See the project docs for environment configuration and deployment guidance:

- [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)
- [INSTALLATION.md](INSTALLATION.md)
- [API_SETUP.md](API_SETUP.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)

## Built for the paddock, the pit lane, and the strategy room

This project is designed to feel like a modern racing control center: fast, technical, polished, and built around the signals that matter during a Grand Prix weekend.

<p align="center">
  <img src="https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1400&q=80" alt="F1 car close-up" width="100%" />
</p>

---

<p align="center">
  <strong>F1 Race Replay Data Control Center</strong><br />
  Race data, telemetry intelligence, and strategy clarity in one control-surface.
</p>


