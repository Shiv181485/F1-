"""Optional OpenF1 MQTT live stream. LIVE status begins only after broker connection."""
import json
import threading
from datetime import datetime, timezone

class OpenF1LiveStream:
    BROKER = "mqtt.openf1.org"
    PORT = 8883
    DEFAULT_TOPICS = ("v1/sessions", "v1/position", "v1/laps", "v1/car_data",
                      "v1/location", "v1/pit", "v1/stints", "v1/weather",
                      "v1/race_control", "v1/intervals")

    def __init__(self, username, password, on_message=None, on_status=None, topics=None):
        self.username, self.password = username, password
        self.on_message = on_message or (lambda topic, payload: None)
        self.on_status = on_status or (lambda status, detail: None)
        self.topics = topics or self.DEFAULT_TOPICS
        self.client = None
        self.connected = threading.Event()

    def start(self):
        if not self.username or not self.password:
            raise RuntimeError("OpenF1 live credentials are not configured.")
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError("Install paho-mqtt to enable OpenF1 live streaming.") from exc

        # paho-mqtt 2.x callback API; use a compatibility fallback for 1.x.
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except (AttributeError, TypeError):
            self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.tls_set()
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

        def connected(client, userdata, flags, reason_code, properties=None):
            code = getattr(reason_code, "value", reason_code)
            if int(code) == 0:
                self.connected.set()
                self.on_status("LIVE", "Authenticated OpenF1 MQTT connection established.")
                for topic in self.topics:
                    client.subscribe(topic)
            else:
                self.on_status("OFFLINE", f"MQTT connection rejected: {reason_code}")

        def disconnected(client, userdata, disconnect_flags=None, reason_code=None, properties=None):
            self.connected.clear()
            self.on_status("OFFLINE", f"OpenF1 MQTT disconnected: {reason_code}")

        def message(client, userdata, msg):
            received_at = datetime.now(timezone.utc).isoformat()
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {"raw": msg.payload.decode("utf-8", errors="replace")}
            self.on_message(msg.topic, {"received_at": received_at, "data": payload,
                                        "mode": "LIVE"})

        self.client.on_connect = connected
        self.client.on_disconnect = disconnected
        self.client.on_message = message
        self.client.connect_async(self.BROKER, self.PORT, keepalive=60)
        self.client.loop_start()
        return self

    def stop(self):
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
        self.connected.clear()
        self.on_status("OFFLINE", "Live stream stopped.")
