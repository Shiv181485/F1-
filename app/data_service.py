"""Shared web data access; returns provider data or explicit errors, never synthetic live values."""
import os
import streamlit as st
from services.api_manager import ApiManager
from services.config import ServiceConfig

@st.cache_resource
def api_manager():
    cfg = ServiceConfig()
    # Streamlit secrets override environment variables without displaying credentials.
    try:
        key = st.secrets.get("OPENF1_API_KEY", cfg.openf1_api_key)
        user = st.secrets.get("OPENF1_USERNAME", cfg.openf1_username)
        password = st.secrets.get("OPENF1_PASSWORD", cfg.openf1_password)
        cfg = ServiceConfig(openf1_username=user, openf1_password=password,
            openf1_api_key=key, openf1_base_url=cfg.openf1_base_url,
            jolpica_base_url=cfg.jolpica_base_url, database_path=cfg.database_path,
            request_timeout=cfg.request_timeout, user_agent=cfg.user_agent,
            openai_api_key=cfg.openai_api_key)
    except Exception:
        pass
    return ApiManager(cfg)

@st.cache_data(ttl=300, show_spinner=False)
def openf1_rows(endpoint, params_tuple=()):
    return api_manager().openf1.get(endpoint, dict(params_tuple))

@st.cache_data(ttl=3600, show_spinner=False)
def jolpica_json(path, params_tuple=()):
    return api_manager().jolpica.get(path, dict(params_tuple))

def season_schedule(year):
    return api_manager().jolpica.season_schedule(year)

def driver_standings(year):
    return jolpica_json(f"{year}/driverStandings")

def constructor_standings(year):
    return jolpica_json(f"{year}/constructorStandings")
