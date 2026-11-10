"""F1 Race Replay — production Streamlit control center."""
from __future__ import annotations

import json
from datetime import datetime
from io import StringIO
from typing import Any, Callable

import pandas as pd
import plotly.express as px
import streamlit as st

from app.data_service import api_manager, jolpica_json, openf1_rows, season_schedule
from database.repository import F1Repository
from services.synchronization_service import SynchronizationService

PAGE_NAMES = [
    "Overview Dashboard",
    "Live Timing",
    "Driver Comparison",
    "Driver Championship",
    "Constructor Championship",
    "Race Calendar",
    "Advanced Telemetry",
    "Circuit Explorer",
    "Pit Stop Analysis",
    "Tyre Strategy",
    "Historical Race Analysis",
    "API Settings",
    "System Health",
]

st.set_page_config(
    page_title="F1 Data Control Center",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: Inter, sans-serif; }
    .stApp { background: #090b10; color: #f4f5f7; }
    [data-testid="stSidebar"] { background: #11151d; border-right: 1px solid #292e38; }
    h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.4px; }
    h1 { font-size: 3rem !important; font-weight: 800 !important; }
    .kicker { color: #f04444; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; font-size: 0.75rem; }
    .status-pill { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
    .status-live { background: rgba(30, 215, 96, 0.16); color: #3be57d; }
    .status-historical { background: rgba(255, 190, 92, 0.12); color: #ffc970; }
    .status-cached { background: rgba(90, 165, 255, 0.14); color: #7bb8ff; }
    .status-demo { background: rgba(219, 105, 255, 0.14); color: #ec9cff; }
    .metric-card { background: #141923; border: 1px solid #292f3a; border-radius: 12px; padding: 1rem; }
    .f1-panel { background: linear-gradient(135deg, rgba(30,34,43,0.96), rgba(16,18,25,0.95)); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1rem 1.1rem; box-shadow: 0 12px 30px rgba(0,0,0,0.25); }
    .hero-shell { background: linear-gradient(135deg, rgba(15,18,27,0.95), rgba(21,24,33,0.88)); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 1rem; box-shadow: 0 18px 40px rgba(0,0,0,0.35); }
    .hero-title { font-size: clamp(2.2rem, 5vw, 4.5rem); font-weight: 800; letter-spacing: 0.06em; line-height: 0.9; }
    .hero-subtitle { color: #c4c9d1; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; }
    .hero-image img { border-radius: 18px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 20px 40px rgba(225,6,0,0.25); }
    .hero-car { height: 120px; border-radius: 18px; background: linear-gradient(135deg, rgba(225,6,0,0.28), rgba(255,255,255,0.04), rgba(15,18,24,0.85)); border: 1px solid rgba(255,255,255,0.08); position: relative; overflow: hidden; }
    .hero-car::before { content: ""; position: absolute; inset: 20px 12px 22px 12px; border-radius: 18px; border: 2px solid rgba(255,255,255,0.08); background: linear-gradient(90deg, rgba(255,255,255,0.06), rgba(225,6,0,0.28), rgba(255,255,255,0.06)); }
    .hero-car::after { content: ""; position: absolute; left: 18%; right: 18%; bottom: 22px; height: 6px; border-radius: 999px; background: linear-gradient(90deg, #e10600, #fda4af, #e10600); box-shadow: 0 0 18px rgba(225,6,0,0.7); }
    div[data-testid="stMetric"] { background: #141923; border: 1px solid #292f3a; padding: 0.8rem; border-radius: 10px; }
    .stButton > button { border-radius: 8px; border: 1px solid #e10600; background: #e10600; color: white; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_page_names() -> list[str]:
    return list(PAGE_NAMES)


def branded_heading(title: str, subtitle: str) -> None:
    st.markdown('<div class="kicker">F1 Race Replay • Data Control Center</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def load_repository() -> F1Repository:
    return F1Repository()


def render_status_badge(label: str, ok: bool, state: str = "live") -> None:
    colors = {
        "live": "status-live",
        "historical": "status-historical",
        "cached": "status-cached",
        "demo": "status-demo",
    }
    cls = colors.get(state, "status-historical")
    st.markdown(f'<span class="status-pill {cls}">{label}: {"online" if ok else "offline"}</span>', unsafe_allow_html=True)


def safe_fetch(label: str, fn: Callable[[], Any], *, fail_message: str | None = None):
    try:
        with st.spinner(f"Loading {label}…"):
            return fn()
    except Exception as exc:
        st.warning(f"{fail_message or label} unavailable: {exc}")
        return None


def dataframe_or_message(rows: list[dict] | list | pd.DataFrame, *, empty_message: str = "No records returned for this selection.") -> None:
    if rows is None:
        return
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    if frame.empty:
        st.info(empty_message)
        return
    st.dataframe(frame, width="stretch", hide_index=True)


@st.cache_data(ttl=300)
def get_session_rows(year: int) -> list[dict]:
    rows = openf1_rows("sessions", (("year", int(year)),))
    return rows or []


@st.cache_data(ttl=300)
def get_default_session_key(year: int) -> int:
    sessions = get_session_rows(year)
    keys = []
    for row in sessions:
        value = row.get("session_key")
        if value is None:
            continue
        try:
            keys.append(int(value))
        except (TypeError, ValueError):
            continue
    return max(keys) if keys else 1


def render_latest_dataset_cards(repo: F1Repository, *, limit: int = 3) -> None:
    rows = repo.latest_datasets(limit=limit)
    if not rows:
        st.info("No cached datasets yet. The app will populate this list as provider data is fetched or synced.")
        return

    cards = st.columns(min(len(rows), 3))
    for index, row in enumerate(rows[:3]):
        with cards[index]:
            st.markdown(
                f"""
                <div class="f1-panel">
                  <div class="kicker">{row.get('provider', 'Provider')}</div>
                  <h4>{row.get('dataset', 'dataset')}</h4>
                  <p>Season: {row.get('season', '-')}</p>
                  <p>Status: {row.get('status', 'UNKNOWN')}</p>
                  <p>Stored: {row.get('retrieved_at', '')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _json_payload_to_rows(payload: Any) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return []
        if isinstance(decoded, list):
            return [item for item in decoded if isinstance(item, dict)]
        if isinstance(decoded, dict):
            return [decoded]
        return []
    if isinstance(payload, dict):
        return [payload]
    return []


def get_local_dataset_rows() -> list[dict]:
    repo = load_repository()
    rows: list[dict] = []
    with repo.connect() as db:
        query = "SELECT provider, dataset, season, status, retrieved_at, source_url, payload FROM datasets ORDER BY retrieved_at DESC"
        for provider, dataset, season, status, retrieved_at, source_url, payload in db.execute(query).fetchall():
            data = json.loads(payload) if isinstance(payload, str) else payload
            records = 0
            if isinstance(data, list):
                records = len(data)
            elif isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, list):
                        records = len(value)
                        break
            rows.append({
                "provider": provider,
                "dataset": dataset,
                "season": season,
                "category": dataset,
                "status": status,
                "records": records,
                "storage": repo.backend.upper(),
                "last_updated": retrieved_at,
                "source_url": source_url or "N/A",
                "payload": data,
            })
    return rows


def render_local_dataset_management(year: int) -> None:
    st.subheader("Local Datasets")
    repo = load_repository()
    dataset_rows = get_local_dataset_rows()
    if not dataset_rows:
        st.info("No synchronization history available yet. Local datasets will appear here once data is fetched or synced.")
        return

    search = st.text_input("Search datasets", placeholder="Filter by dataset name or provider")
    category_filter = st.selectbox("Category", ["All"] + sorted({row["category"] for row in dataset_rows}))
    season_filter = st.selectbox("Season", ["All"] + sorted({row["season"] for row in dataset_rows if row.get("season") not in (None, -1)}, reverse=True))

    filtered = dataset_rows
    if search:
        filtered = [row for row in filtered if search.lower() in (row["dataset"].lower() + row["provider"].lower())]
    if category_filter != "All":
        filtered = [row for row in filtered if row["category"] == category_filter]
    if season_filter != "All":
        filtered = [row for row in filtered if str(row.get("season")) == str(season_filter)]

    if not filtered:
        st.warning("No datasets match the selected filters.")
        return

    table = pd.DataFrame(filtered)[["dataset", "provider", "season", "records", "status", "storage", "last_updated"]]
    st.dataframe(table, use_container_width=True, hide_index=True)

    selected_name = st.selectbox("Dataset preview", options=[row["dataset"] for row in filtered], index=0)
    selected = next((row for row in filtered if row["dataset"] == selected_name), filtered[0])
    payload = selected.get("payload") or []
    sample_rows = _json_payload_to_rows(payload)[:5]

    with st.expander("Dataset details", expanded=True):
        st.write(f"Provider: {selected['provider']}")
        st.write(f"Season: {selected['season']}")
        st.write(f"Storage: {selected['storage']}")
        st.write(f"Last updated: {selected['last_updated']}")
        st.write(f"Records: {selected['records']}")
        if sample_rows:
            st.dataframe(pd.DataFrame(sample_rows).head(), use_container_width=True, hide_index=True)
        else:
            st.info("This dataset is available but it does not contain sample rows to preview.")

        csv_buffer = StringIO()
        pd.DataFrame(sample_rows).to_csv(csv_buffer, index=False)
        st.download_button("Export CSV", csv_buffer.getvalue(), file_name=f"{selected['dataset']}.csv", mime="text/csv")

        json_buffer = StringIO()
        json_buffer.write(json.dumps(payload if isinstance(payload, (list, dict)) else sample_rows, indent=2))
        st.download_button("Export JSON", json_buffer.getvalue(), file_name=f"{selected['dataset']}.json", mime="application/json")

        if st.button(f"Refresh {selected['dataset']}", key=f"refresh_{selected['dataset']}"):
            try:
                service = SynchronizationService(repo=repo)
                season_year = int(selected.get("season") or year)
                if selected["provider"].lower() == "openf1":
                    result = service.sync_openf1_season(season_year)
                else:
                    result = service.sync_jolpica_season(season_year)
                st.success(f"Refresh finished: {result}")
            except Exception as exc:
                st.error(f"Refresh failed: {exc}")


def get_sync_logs() -> list[dict]:
    repo = load_repository()
    with repo.connect() as db:
        rows = db.execute(
            "SELECT provider, started_at, finished_at, status, records, message FROM sync_logs ORDER BY started_at DESC"
        ).fetchall()
    return [
        {
            "provider": row[0],
            "started_at": row[1],
            "finished_at": row[2],
            "status": row[3],
            "records": row[4],
            "message": row[5],
        }
        for row in rows
    ]


def render_sync_logs(year: int) -> None:
    st.subheader("Sync Logs")
    logs = get_sync_logs()
    if not logs:
        st.info("No synchronization history available yet.")
        return

    source_filter = st.selectbox("Source", ["All"] + sorted({row["provider"] for row in logs}))
    status_filter = st.selectbox("Status", ["All"] + sorted({row["status"] for row in logs}))
    search = st.text_input("Search logs", placeholder="Filter by message or source")

    filtered = logs
    if source_filter != "All":
        filtered = [row for row in filtered if row["provider"] == source_filter]
    if status_filter != "All":
        filtered = [row for row in filtered if row["status"] == status_filter]
    if search:
        filtered = [row for row in filtered if search.lower() in (str(row["message"]).lower() + row["provider"].lower())]

    if not filtered:
        st.warning("No sync logs match the selected filters.")
        return

    table = pd.DataFrame(filtered)
    table["status"] = table["status"].fillna("UNKNOWN")
    st.dataframe(table, use_container_width=True, hide_index=True)

    if st.button("Retry latest sync"):
        latest = filtered[0]
        try:
            service = SynchronizationService(repo=load_repository())
            if latest["provider"].lower() == "openf1":
                result = service.sync_openf1_season(int(year))
            else:
                result = service.sync_jolpica_season(int(year))
            st.success(f"Retry completed: {result}")
        except Exception as exc:
            st.error(f"Retry failed: {exc}")


def render_hero_banner(year: int) -> None:
    hero_image = "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80"
    provider_status = get_provider_status()
    live_count = sum(1 for result in provider_status.values() if result.get("ok"))
    total_providers = max(len(provider_status), 1)
    live_pct = int((live_count / total_providers) * 100)

    left, right = st.columns([1.2, 1.0], gap="large")
    with left:
        st.markdown('<div class="kicker">Formula One • Race Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">FORMULA 1<br>DATA CONTROL CENTER</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">REAL-TIME MOTORSPORT INTELLIGENCE</div>', unsafe_allow_html=True)
        st.markdown("<div class='f1-panel'>Season: <strong>{}</strong> &nbsp; • &nbsp; Status: <strong>{}% provider health</strong></div>".format(year, live_pct), unsafe_allow_html=True)
        st.markdown("<div class='f1-panel'>Selected GP: <strong>{}</strong> &nbsp; • &nbsp; Session: <strong>{}</strong></div>".format("Current Weekend", "Live / Cached"), unsafe_allow_html=True)
    with right:
        st.image(hero_image, caption="Cinematic F1 car action", use_container_width=True, output_format="auto")


@st.cache_data(ttl=600)
def get_driver_standings_for_year(year: int) -> list[dict]:
    body = jolpica_json(f"{year}/driverStandings")
    if not body:
        return []
    table = body.get("MRData", {}).get("StandingsTable", {})
    lists = table.get("StandingsLists", [])
    if not lists:
        return []
    drivers = lists[0].get("DriverStandings", [])
    rows = []
    for item in drivers:
        driver = item.get("Driver", {})
        constructors = item.get("Constructors", [])
        rows.append({
            "Position": item.get("position"),
            "Driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
            "Code": driver.get("code"),
            "Team": ", ".join(c.get("name", "") for c in constructors),
            "Points": item.get("points"),
            "Wins": item.get("wins"),
        })
    return rows


@st.cache_data(ttl=600)
def get_constructor_standings_for_year(year: int) -> list[dict]:
    body = jolpica_json(f"{year}/constructorStandings")
    if not body:
        return []
    table = body.get("MRData", {}).get("StandingsTable", {})
    lists = table.get("StandingsLists", [])
    if not lists:
        return []
    constructors = lists[0].get("ConstructorStandings", [])
    rows = []
    for item in constructors:
        team = item.get("Constructor", {})
        rows.append({
            "Position": item.get("position"),
            "Constructor": team.get("name"),
            "Points": item.get("points"),
            "Wins": item.get("wins"),
        })
    return rows


@st.cache_data(ttl=600)
def get_calendar_rows(year: int) -> list[dict]:
    rows = season_schedule(int(year))
    results = []
    for item in rows or []:
        circuit = item.get("Circuit", {})
        location = circuit.get("Location", {})
        results.append({
            "Round": item.get("round"),
            "Grand Prix": item.get("raceName"),
            "Circuit": circuit.get("circuitName"),
            "Country": location.get("country"),
            "Date": item.get("date"),
            "Time": item.get("time"),
        })
    return results


@st.cache_data(ttl=300)
def get_provider_status() -> dict[str, dict[str, Any]]:
    return api_manager().test_all()


def render_provider_overview() -> None:
    checks = get_provider_status()
    for name in ("OpenF1", "Jolpica", "FastF1"):
        result = checks.get(name, {})
        ok = bool(result.get("ok"))
        st.markdown(
            f'<div class="metric-card"><strong>{name}</strong><br>{result.get("message", "No response")}</div>',
            unsafe_allow_html=True,
        )
        render_status_badge(name, ok, "live" if ok else "historical")


def render_overview_dashboard(year: int) -> None:
    branded_heading("Overview Dashboard", "Live connectivity, historical data, and championship context for the selected season.")
    repo = load_repository()
    data_counts = repo.counts()
    dataset_rows = get_local_dataset_rows()
    sync_rows = get_sync_logs()
    provider_status = get_provider_status()

    render_hero_banner(year)

    st.markdown("### Race overview")
    overview_cols = st.columns(4)
    overview_cols[0].metric("Season", year)
    overview_cols[1].metric("Latest GP", "Current weekend")
    overview_cols[2].metric("Session status", "Live / Cached")
    overview_cols[3].metric("Data sync", sync_rows[0]["started_at"] if sync_rows else "Not started")

    st.markdown("### Key performance indicators")
    season_count = len({row.get("season") for row in dataset_rows if row.get("season") not in (None, -1)})
    runs = len(get_session_rows(year))
    total_drivers = sum(row["records"] for row in dataset_rows if row["dataset"].lower() in {"drivers", "driver_standings"})
    total_constructors = sum(row["records"] for row in dataset_rows if row["dataset"].lower() in {"constructors", "constructor_standings"})
    total_telemetry = sum(row["records"] for row in dataset_rows if row["dataset"].lower() in {"telemetry", "car_data", "laps"})
    total_local_datasets = len(dataset_rows)

    kpi = st.columns(6)
    kpi[0].metric("Seasons", season_count or 0, delta="Database")
    kpi[1].metric("Race sessions", runs or 0, delta="OpenF1")
    kpi[2].metric("Drivers", total_drivers or 0, delta="Local")
    kpi[3].metric("Constructors", total_constructors or 0, delta="Local")
    kpi[4].metric("Telemetry", total_telemetry or 0, delta="Records")
    kpi[5].metric("Local datasets", total_local_datasets or 0, delta="Storage")

    st.markdown("### Quick access dashboard")
    nav_actions = [
        ("Live Timing", "Live race telemetry and timing windows.", "⏱️"),
        ("Driver Comparison", "Compare lap performance and key indicators.", "🏎️"),
        ("Driver Championship", "View championship standings and points.", "🏆"),
        ("Constructor Championship", "Constructor battle and team points.", "🏁"),
        ("Race Calendar", "Season calendar and fixture planning.", "📅"),
        ("Advanced Telemetry", "Detailed telemetry stream data.", "📊"),
        ("Circuit Explorer", "Circuit and track position analysis.", "🗺️"),
        ("Pit Stop Analysis", "Pit stop and tyre stint review.", "🛠️"),
        ("Historical Race Analysis", "Historical race and qualifying records.", "📚"),
    ]
    cards = st.columns(3)
    for idx, (name, description, icon) in enumerate(nav_actions):
        with cards[idx % 3]:
            st.markdown(f"""
            <div class="f1-panel">
              <div class="kicker">{icon} {name}</div>
              <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open", key=f"nav_{name}"):
                st.session_state["selected_page"] = name
                st.rerun()

    st.markdown("### F1 racing gallery")
    gallery = [
        "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80",
    ]
    gcols = st.columns(3)
    for idx, src in enumerate(gallery):
        with gcols[idx]:
            st.image(src, use_container_width=True, caption=["Racing car", "Driver action", "Circuit view"][idx])

    st.markdown("### Local Datasets")
    render_local_dataset_management(year)

    st.markdown("### Sync Logs")
    render_sync_logs(year)

    st.markdown("### System health")
    render_provider_overview()
    status_cols = st.columns(3)
    status_cols[0].metric("Database backend", repo.backend.upper())
    status_cols[1].metric("Local datasets", data_counts.get("datasets", 0))
    status_cols[2].metric("Sync logs", data_counts.get("sync_logs", 0))

    st.subheader("Latest cached datasets")
    render_latest_dataset_cards(repo)

    st.subheader("Championship snapshot")
    driver_rows = get_driver_standings_for_year(year)
    if driver_rows:
        driver_df = pd.DataFrame(driver_rows)
        st.dataframe(driver_df.head(10), width="stretch", hide_index=True)
        fig = px.bar(driver_df.head(10), x="Driver", y="Points", color="Driver", title=f"{year} Driver Championship")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Driver standings are not yet available from the published provider data.")

    st.subheader("Most recent sessions")
    sessions = get_session_rows(year)
    if sessions:
        session_df = pd.DataFrame(sessions)
        latest = session_df.sort_values(by=["session_key"], ascending=False).head(12)
        st.dataframe(latest, width="stretch", hide_index=True)
    else:
        st.info("No OpenF1 sessions are available for this season yet. Use a different season or check the provider connection.")


def render_live_timing(year: int) -> None:
    branded_heading("Live Timing", "Use OpenF1 session keys to inspect live-position, lap, interval, and stopping data.")
    default_session = get_default_session_key(year)
    session_key = st.number_input("OpenF1 session key", min_value=1, value=default_session, step=1)
    if session_key == 1 and default_session != 1:
        st.info(f"The default session key 1 is not valid for this season. Showing the most recent available session: {default_session}.")
    st.caption("OpenF1 live endpoints may require account access; the app shows status-only data when a session is unavailable.")
    if st.button("Refresh live timing"):
        for title, endpoint in [("Positions", "position"), ("Intervals", "intervals"), ("Laps", "laps"), ("Pit stops", "pit")]:
            st.subheader(title)
            rows = safe_fetch(title, lambda e=endpoint: openf1_rows(e, (("session_key", int(session_key),),)), fail_message=title)
            if rows is None or not rows:
                st.info(f"No {title.lower()} were returned for session {session_key}. Try a newer session key from the recent sessions table.")
            else:
                dataframe_or_message(rows[-30:][::-1], empty_message=f"No {title.lower()} were returned for session {session_key}.")


def render_driver_comparison(year: int) -> None:
    branded_heading("Driver Comparison", "Compare lap timings and telemetry traces for selected drivers in a session.")
    default_session = get_default_session_key(year)
    session_key = st.number_input("Session key", min_value=1, value=default_session, step=1)
    drivers = safe_fetch("driver list", lambda: openf1_rows("drivers", (("session_key", int(session_key)),)))
    if not drivers:
        st.info(f"No drivers are available for session {session_key}. Try a valid session key from the latest session list.")
        return

    driver_lookup = {f"{d.get('name_acronym', '')} — {d.get('full_name', '')}": d.get("driver_number") for d in drivers}
    selected = st.multiselect("Drivers", list(driver_lookup.keys()), default=list(driver_lookup.keys())[:2])
    if not selected:
        st.info("Choose at least one driver to compare.")
        return

    numbers = [driver_lookup[name] for name in selected]
    laps = safe_fetch("lap data", lambda: openf1_rows("laps", (("session_key", int(session_key)),)))
    if laps is None:
        return
    selected_laps = [row for row in laps if row.get("driver_number") in numbers]
    dataframe_or_message(selected_laps, empty_message="No lap records were returned for the selected drivers.")

    if selected_laps:
        lap_df = pd.DataFrame(selected_laps)
        if {"lap_number", "lap_duration", "driver_number"}.issubset(lap_df.columns):
            fig = px.line(
                lap_df,
                x="lap_number",
                y="lap_duration",
                color="driver_number",
                markers=True,
                title="Lap time comparison",
            )
            st.plotly_chart(fig, use_container_width=True)


def render_championship(year: int, *, kind: str) -> None:
    label = "Driver" if kind == "driver" else "Constructor"
    branded_heading(f"{label} Championship", f"Official standings published for the {year} championship.")
    rows = get_driver_standings_for_year(year) if kind == "driver" else get_constructor_standings_for_year(year)
    dataframe_or_message(rows, empty_message=f"No {label.lower()} standings are available for {year}.")


def render_race_calendar(year: int) -> None:
    branded_heading("Race Calendar", f"Grand Prix schedule for the {year} season.")
    rows = get_calendar_rows(year)
    dataframe_or_message(rows, empty_message=f"No race calendar entries were published for {year}.")


def render_advanced_telemetry(year: int) -> None:
    branded_heading("Advanced Telemetry", "Speed, throttle, braking, RPM and gear traces for a selected driver and session.")
    default_session = get_default_session_key(year)
    session_key = st.number_input("Session key", min_value=1, value=default_session, step=1)
    driver_number = st.number_input("Driver number", min_value=1, max_value=99, value=1, step=1)
    rows = safe_fetch(
        "car telemetry",
        lambda: openf1_rows("car_data", (("session_key", int(session_key)), ("driver_number", int(driver_number)))),
        fail_message="Telemetry",
    )
    if not rows:
        st.info(f"No telemetry was returned for session {session_key} and driver {driver_number}. Try a newer valid session ID from this season.")
        return

    df = pd.DataFrame(rows)
    metric_columns = [column for column in ["speed", "throttle", "brake", "rpm", "n_gear"] if column in df.columns]
    if metric_columns:
        fig = px.line(df, x="date" if "date" in df.columns else df.index, y=metric_columns, title="Telemetry trace")
        st.plotly_chart(fig, use_container_width=True)
    dataframe_or_message(df.tail(100), empty_message="No telemetry rows available to display.")


def render_circuit_explorer(year: int) -> None:
    branded_heading("Circuit Explorer", "Track position samples and circuit traces when the provider exposes location data.")
    default_session = get_default_session_key(year)
    session_key = st.number_input("Session key", min_value=1, value=default_session, step=1)
    driver_number = st.number_input("Driver number", min_value=1, max_value=99, value=1, step=1)
    rows = safe_fetch(
        "location data",
        lambda: openf1_rows("location", (("session_key", int(session_key)), ("driver_number", int(driver_number)))),
        fail_message="Circuit location",
    )
    if not rows:
        st.info(f"No location samples are available for session {session_key} and driver {driver_number}. Choose a valid session from the current season.")
        return
    df = pd.DataFrame(rows)
    if {"x", "y"}.issubset(df.columns):
        fig = px.scatter(df, x="x", y="y", title="Track position samples")
        fig.update_yaxes(scaleanchor="x", scaleratio=1)
        st.plotly_chart(fig, use_container_width=True)
    dataframe_or_message(df.tail(50), empty_message="No location data was returned.")


def render_pit_stop_analysis(year: int) -> None:
    branded_heading("Pit Stop Analysis", "Pit stop and tyre stint datasets from OpenF1 are displayed here without inventing timing conclusions.")
    default_session = get_default_session_key(year)
    session_key = st.number_input("Session key", min_value=1, value=default_session, step=1)
    for title, endpoint in [("Pit stops", "pit"), ("Tyre stints", "stints")]:
        st.subheader(title)
        rows = safe_fetch(title.lower(), lambda e=endpoint: openf1_rows(e, (("session_key", int(session_key)),)), fail_message=title)
        if rows is None or not rows:
            st.info(f"No {title.lower()} were returned for session {session_key}. Use a valid session key from the most recent season entries.")
        else:
            dataframe_or_message(rows, empty_message=f"No {title.lower()} were returned for session {session_key}.")


def render_tyre_strategy(year: int) -> None:
    branded_heading("Tyre Strategy", "Tyre stint and pit-window information is shown when provider data is available.")
    st.info("Strategy conclusions require lap-by-lap and stint data. This page reflects what the API actually returned and labels any inferred findings as such.")
    render_pit_stop_analysis(year)


def render_historical_analysis(year: int) -> None:
    branded_heading("Historical Race Analysis", "Review race, qualifying and sprint data from the Jolpica Ergast-compatible endpoints.")
    round_number = st.number_input("Round", min_value=1, max_value=30, value=1, step=1)
    for title, path in [
        ("Race results", f"{year}/{int(round_number)}/results"),
        ("Qualifying", f"{year}/{int(round_number)}/qualifying"),
        ("Sprint", f"{year}/{int(round_number)}/sprint"),
    ]:
        st.subheader(title)
        body = safe_fetch(title.lower(), lambda p=path: jolpica_json(p), fail_message=title)
        if not body:
            st.info(f"No {title.lower()} data is available for round {round_number}.")
            continue
        mr = body.get("MRData", {})
        table = next((value for key, value in mr.items() if key.endswith("Table") and isinstance(value, dict)), {})
        rows = next((value for value in table.values() if isinstance(value, list)), [])
        dataframe_or_message(rows, empty_message=f"No {title.lower()} rows were returned.")


def render_api_settings(year: int) -> None:
    branded_heading("API Settings", "Read credentials from environment variables or the Streamlit cloud secrets manager.")
    st.code(
        "OPENF1_API_KEY = \"your_api_key_here\"\nOPENF1_USERNAME = \"\"\nOPENF1_PASSWORD = \"\"\nF1_DATABASE_URL = \"postgresql://user:pass@host/dbname\"",
        language="toml",
    )
    st.caption("The app never hard-codes API keys. Configure them in local environment variables or the Streamlit secrets file.")
    st.subheader("Verified providers")
    render_provider_overview()


def render_system_health(year: int) -> None:
    branded_heading("System Health", "Repository state and infrastructure health for local SQLite and optional PostgreSQL setups.")
    repo = load_repository()
    counts = repo.counts()
    columns = st.columns(3)
    columns[0].metric("Database backend", repo.backend.upper())
    columns[1].metric("Datasets", counts.get("datasets", 0))
    columns[2].metric("Sync log entries", counts.get("sync_logs", 0))

    st.subheader("Latest cached datasets")
    render_latest_dataset_cards(repo, limit=3)

    rendered = st.columns(2)
    rendered[0].subheader("Provider status")
    render_provider_overview()
    rendered[1].subheader("Recent repository records")
    rows = repo.latest_datasets(5)
    if rows:
        cleaned = []
        for row in rows:
            payload = row.get("payload", {})
            if isinstance(payload, str):
                payload_size = len(payload)
            else:
                payload_size = len(str(payload))
            cleaned.append({
                "Provider": row.get("provider"),
                "Dataset": row.get("dataset"),
                "Season": row.get("season"),
                "Status": row.get("status"),
                "Retrieved": row.get("retrieved_at"),
                "Payload size": payload_size,
            })
        dataframe_or_message(cleaned, empty_message="No repository records are available yet.")
    else:
        st.info("No cached records are available yet. Use the live data pages to fetch provider records and populate this section.")


PAGE_RENDERERS = {
    "Overview Dashboard": lambda year: render_overview_dashboard(year),
    "Live Timing": lambda year: render_live_timing(year),
    "Driver Comparison": lambda year: render_driver_comparison(year),
    "Driver Championship": lambda year: render_championship(year, kind="driver"),
    "Constructor Championship": lambda year: render_championship(year, kind="constructor"),
    "Race Calendar": lambda year: render_race_calendar(year),
    "Advanced Telemetry": lambda year: render_advanced_telemetry(year),
    "Circuit Explorer": lambda year: render_circuit_explorer(year),
    "Pit Stop Analysis": lambda year: render_pit_stop_analysis(year),
    "Tyre Strategy": lambda year: render_tyre_strategy(year),
    "Historical Race Analysis": lambda year: render_historical_analysis(year),
    "API Settings": lambda year: render_api_settings(year),
    "System Health": lambda year: render_system_health(year),
}


def main() -> None:
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "Overview Dashboard"

    st.sidebar.markdown('<div class="kicker">Formula One • Race Intelligence</div>', unsafe_allow_html=True)
    st.sidebar.title("F1 Control Center")
    page_names = get_page_names()
    selected_page = st.sidebar.radio(
        "Navigation",
        page_names,
        index=page_names.index(st.session_state["selected_page"]) if st.session_state["selected_page"] in page_names else 0,
        label_visibility="collapsed",
    )
    st.session_state["selected_page"] = selected_page
    year = st.sidebar.number_input("Season", min_value=1950, max_value=2100, value=datetime.now().year, step=1)
    st.sidebar.caption("Data sources: OpenF1, Jolpica and FastF1. Historical data is cached; live endpoints are tested before use.")
    render = PAGE_RENDERERS.get(selected_page)
    if render is not None:
        render(year)


if __name__ == "__main__":
    main()
