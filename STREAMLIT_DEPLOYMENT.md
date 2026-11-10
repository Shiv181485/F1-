# Streamlit Community Cloud deployment

1. Create a GitHub repository and upload the project source (exclude `.env`, secrets, local `data/*.sqlite*`, `.venv`, and caches).
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**, select the repository and branch.
4. Set the main file path to `streamlit_app.py`.
5. In **Advanced settings → Secrets**, add only the credentials required by your OpenF1 plan, for example:
```toml
OPENF1_API_KEY = "your_api_key_here"
```
6. Deploy. The app installs dependencies from `requirements.txt`.
7. Verify Overview, championship, calendar, API settings, and System Health pages. Use an active OpenF1 session key to test live timing/telemetry.
8. Check provider health messages and Streamlit logs for deployment issues.

Start locally with `streamlit run streamlit_app.py`.

**Persistence warning:** Streamlit Community Cloud local filesystem is not a durable database. This build's SQLite repository is suitable for local use and ephemeral cache only. Configure an external managed PostgreSQL service before relying on persistent cloud writes. This release documents that requirement but does not yet include a PostgreSQL adapter; do not treat SQLite on Cloud as permanent storage.

A successful GitHub push is not proof of a successful deployment. Verify the deployed URL manually; no cloud deployment was performed by this package build.
