"""OpenF1 REST client. Historical endpoints work without credentials; live data requires subscription."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
from services.http import HttpClient, ApiError

class OpenF1Client:
    def __init__(self, username="", password="", base_url="https://api.openf1.org/v1",
                 user_agent="F1RaceReplay/2.0", timeout=20, api_key=""):
        self.username, self.password = username, password
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"
        self.http = HttpClient(user_agent, timeout)
        self._token, self._token_expiry = None, None

    def authenticate(self, force=False):
        if not self.username or not self.password:
            raise ApiError("OpenF1 credentials are not configured.")
        if not force and self._token and self._token_expiry and datetime.now(timezone.utc) < self._token_expiry:
            return self._token
        response = self.http.request("POST", "https://api.openf1.org/token",
            data={"username": self.username, "password": self.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ApiError("OpenF1 authentication response did not contain access_token.")
        self._token = token
        # Provider tokens expire after one hour; refresh early.
        self._token_expiry = datetime.now(timezone.utc) + timedelta(minutes=55)
        return token

    def get(self, endpoint, params=None, live=False):
        headers = {}
        if live:
            headers["Authorization"] = f"Bearer {self.authenticate()}"
        url = urljoin(self.base_url, endpoint.lstrip("/") + ("" if endpoint.endswith("/") else ""))
        try:
            return self.http.get_json(url, params=params or {}, headers=headers)
        except ApiError as exc:
            # Refresh once on expired/invalid token.
            if live and not self.api_key and ("401" in str(exc) or "403" in str(exc)):
                headers["Authorization"] = f"Bearer {self.authenticate(force=True)}"
                return self.http.get_json(url, params=params or {}, headers=headers)
            raise

    def test_connection(self):
        rows = self.get("sessions", {"year": datetime.now().year})
        return {"ok": True, "message": f"OpenF1 REST reachable; {len(rows)} session records returned."}

    def sessions(self, year):
        return self.get("sessions", {"year": year})
