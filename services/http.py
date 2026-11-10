"""Shared HTTP client with timeouts, retry/backoff and a descriptive User-Agent."""
import time
import requests

class ApiError(RuntimeError):
    pass

class HttpClient:
    def __init__(self, user_agent="F1RaceReplay/2.0", timeout=20, retries=3):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        self.timeout, self.retries = timeout, retries

    def request(self, method, url, **kwargs):
        last = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                if response.status_code == 429 or response.status_code >= 500:
                    wait = min(2 ** attempt, 12)
                    time.sleep(wait)
                    last = ApiError(f"HTTP {response.status_code} from {url}")
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last = ApiError(f"Request failed for {url}: {exc}")
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 12))
        raise last or ApiError(f"Request failed: {url}")

    def get_json(self, url, **kwargs):
        try:
            return self.request("GET", url, **kwargs).json()
        except ValueError as exc:
            raise ApiError(f"Invalid JSON from {url}") from exc
