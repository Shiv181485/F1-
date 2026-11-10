"""FastF1 adapter for historical timing/telemetry; no live claim is made here."""
from pathlib import Path

class FastF1Client:
    def __init__(self, cache_dir=".fastf1-cache"):
        self.cache_dir = str(Path(cache_dir))
        self._fastf1 = None

    def _module(self):
        if self._fastf1 is None:
            import fastf1
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
            fastf1.Cache.enable_cache(self.cache_dir)
            self._fastf1 = fastf1
        return self._fastf1

    def load_session(self, year, round_number, session_code="R", telemetry=True):
        ff1 = self._module()
        session = ff1.get_session(int(year), int(round_number), session_code)
        session.load(telemetry=telemetry, weather=True, messages=True)
        return session

    def test_connection(self):
        try:
            self._module()
            return {"ok": True, "message": "FastF1 installed and cache initialized."}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
