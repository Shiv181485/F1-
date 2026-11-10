"""Provider registry and health checks. Each provider can fail independently."""
from services.openf1_client import OpenF1Client
from services.jolpica_client import JolpicaClient
from services.fastf1_client import FastF1Client
from services.config import ServiceConfig

class ApiManager:
    def __init__(self, config=None):
        self.config = config or ServiceConfig()
        self.openf1 = OpenF1Client(self.config.openf1_username, self.config.openf1_password,
            self.config.openf1_base_url, self.config.user_agent, self.config.request_timeout, self.config.openf1_api_key)
        self.jolpica = JolpicaClient(self.config.jolpica_base_url, self.config.user_agent,
            self.config.request_timeout)
        self.fastf1 = FastF1Client()

    def create_live_stream(self, on_message=None, on_status=None):
        from services.live_stream_manager import OpenF1LiveStream
        return OpenF1LiveStream(self.config.openf1_username, self.config.openf1_password,
                                on_message=on_message, on_status=on_status)

    def test_all(self):
        checks = {}
        for name, provider in (("OpenF1", self.openf1), ("Jolpica", self.jolpica), ("FastF1", self.fastf1)):
            try:
                checks[name] = provider.test_connection()
            except Exception as exc:
                checks[name] = {"ok": False, "message": str(exc)}
        return checks
