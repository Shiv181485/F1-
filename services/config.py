"""Central configuration for the F1 data services. Secrets are read from env or Streamlit secrets."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class ServiceConfig:
    openf1_username: str = os.getenv("OPENF1_USERNAME", "")
    openf1_password: str = os.getenv("OPENF1_PASSWORD", "")
    openf1_api_key: str = os.getenv("OPENF1_API_KEY", "")
    openf1_base_url: str = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
    jolpica_base_url: str = os.getenv("JOLPICA_BASE_URL", "https://api.jolpi.ca/ergast/f1")
    database_url: str = os.getenv("F1_DATABASE_URL", "")
    database_path: str = os.getenv("F1_DATABASE_PATH", "data/f1_data.sqlite3")
    request_timeout: int = int(os.getenv("F1_REQUEST_TIMEOUT", "20"))
    user_agent: str = os.getenv("F1_USER_AGENT", "F1RaceReplay/2.0 FastF1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
