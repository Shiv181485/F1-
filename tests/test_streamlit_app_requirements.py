from pathlib import Path

import streamlit_app
from database.repository import F1Repository


REQUIRED_PAGES = [
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


def test_required_pages_are_defined():
    pages = streamlit_app.get_page_names()
    assert pages == REQUIRED_PAGES


def test_repository_avoids_duplicate_rows(tmp_path):
    db_path = tmp_path / "f1_data.sqlite3"
    repo = F1Repository(path=db_path)

    repo.save_dataset("openf1", "sessions", [{"id": 1}], season=2024, status="LIVE")
    repo.save_dataset("openf1", "sessions", [{"id": 1}], season=2024, status="LIVE")

    assert repo.counts()["datasets"] == 1

    repo.save_dataset("openf1", "sessions", [{"id": 2}], season=2024, status="HISTORICAL")
    assert repo.counts()["datasets"] == 2


def test_database_defaults_to_sqlite_backend():
    repo = F1Repository(path=Path("data/f1_data.sqlite3"))
    assert repo.backend == "sqlite"
