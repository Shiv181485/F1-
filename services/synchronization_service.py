"""Conservative season synchronization: schedule, results and standings, with source metadata."""
from datetime import datetime, timezone
from services.api_manager import ApiManager
from database.repository import F1Repository

class SynchronizationService:
    def __init__(self, api_manager=None, repository=None):
        self.apis = api_manager or ApiManager()
        self.repo = repository or F1Repository(self.apis.config.database_path)

    def sync_jolpica_season(self, year):
        jobs = [
            ("schedule", lambda: self.apis.jolpica.season_schedule(year)),
            ("results", lambda: self.apis.jolpica.race_results(year)),
            ("qualifying", lambda: self.apis.jolpica.qualifying(year)),
            ("sprint", lambda: self.apis.jolpica.sprint_results(year)),
            ("driver_standings", lambda: self.apis.jolpica.driver_standings(year)),
            ("constructor_standings", lambda: self.apis.jolpica.constructor_standings(year)),
        ]
        outcome = {}
        for dataset, fetch in jobs:
            try:
                data = fetch()
                count = self.repo.save_dataset("Jolpica", dataset, data, season=year,
                    status="HISTORICAL", source_url=self.apis.config.jolpica_base_url)
                self.repo.log_sync("Jolpica", "SUCCESS", count, dataset)
                outcome[dataset] = {"ok": True, "records": count}
            except Exception as exc:
                self.repo.log_sync("Jolpica", "ERROR", 0, f"{dataset}: {exc}")
                outcome[dataset] = {"ok": False, "error": str(exc)}
        return outcome

    def sync_openf1_season(self, year):
        try:
            rows = self.apis.openf1.sessions(year)
            count = self.repo.save_dataset("OpenF1", "sessions", rows, season=year,
                status="HISTORICAL", source_url=self.apis.config.openf1_base_url)
            self.repo.log_sync("OpenF1", "SUCCESS", count, f"sessions {year}")
            return {"ok": True, "records": count}
        except Exception as exc:
            self.repo.log_sync("OpenF1", "ERROR", 0, str(exc))
            return {"ok": False, "error": str(exc)}
