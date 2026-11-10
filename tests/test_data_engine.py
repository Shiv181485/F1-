import json
from database.repository import F1Repository
from services.openf1_client import OpenF1Client
from services.jolpica_client import JolpicaClient

def test_openf1_historical_does_not_require_credentials():
    client = OpenF1Client()
    assert client.username == ""
    assert client.password == ""

def test_jolpica_pagination_parses_race_table(monkeypatch):
    client = JolpicaClient()
    payloads = [
        {"MRData": {"total": "2", "RaceTable": {"Races": [{"round": "1"}]}}},
        {"MRData": {"total": "2", "RaceTable": {"Races": [{"round": "2"}]}}},
    ]
    monkeypatch.setattr(client, "get", lambda path, params: payloads[0 if params["offset"] == 0 else 1])
    assert [r["round"] for r in client.paginated("2025")] == ["1", "2"]

def test_repository_upserts_and_counts(tmp_path):
    repo = F1Repository(tmp_path / "test.sqlite3")
    repo.save_dataset("Jolpica", "schedule", [{"round": 1}], season=2025,
                      source_url="https://api.jolpi.ca", status="HISTORICAL")
    repo.save_dataset("Jolpica", "schedule", [{"round": 1}], season=2025,
                      source_url="https://api.jolpi.ca", status="HISTORICAL")
    assert repo.counts()["datasets"] == 1
