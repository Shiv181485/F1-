# Installation (Windows)

1. Install Python 3.11 or newer.
2. Extract the repository and open PowerShell in the project folder.
3. Create and activate an environment:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
4. Copy `.env.example` to `.env` and configure credentials if applicable.
5. Start the web app with `streamlit run streamlit_app.py`.
6. For desktop mode, additionally run `pip install -r requirements-desktop.txt` and `python main.py`.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass`.
