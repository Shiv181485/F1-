"""Jolpica Ergast-compatible client with limit/offset pagination."""
from urllib.parse import urljoin
from services.http import HttpClient

class JolpicaClient:
    def __init__(self, base_url="https://api.jolpi.ca/ergast/f1", user_agent="F1RaceReplay/2.0", timeout=20):
        self.base_url = base_url.rstrip("/") + "/"
        self.http = HttpClient(user_agent, timeout)

    def get(self, path="", params=None):
        route = path.strip("/") + ".json"
        return self.http.get_json(urljoin(self.base_url, route), params=params or {})

    def paginated(self, path, page_size=100, extra_params=None):
        offset, rows = 0, []
        while True:
            params = {"limit": min(page_size, 100), "offset": offset}
            params.update(extra_params or {})
            payload = self.get(path, params)
            mr = payload.get("MRData", {})
            # Jolpica uses endpoint-specific table names.
            table = next((v for k, v in mr.items() if k.endswith("Table") and isinstance(v, dict)), {})
            key = next((k for k, v in table.items() if isinstance(v, list)), None)
            page = table.get(key, []) if key else []
            rows.extend(page)
            total = int(mr.get("total", len(rows)))
            offset += len(page)
            if not page or offset >= total:
                break
        return rows

    def season_schedule(self, year):
        return self.paginated(f"{year}")

    def driver_standings(self, year):
        return self.get(f"{year}/driverStandings")

    def constructor_standings(self, year):
        return self.get(f"{year}/constructorStandings")

    def race_results(self, year):
        return self.paginated(f"{year}/results")

    def qualifying(self, year):
        return self.paginated(f"{year}/qualifying")

    def sprint_results(self, year):
        return self.paginated(f"{year}/sprint")

    def test_connection(self):
        data = self.get("current/last/results", {"limit": 1})
        return {"ok": True, "message": "Jolpica API reachable."}
