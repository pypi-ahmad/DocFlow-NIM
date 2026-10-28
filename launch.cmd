@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-offline.ps1"
if errorlevel 1 (
    echo Local model startup failed. See the error above.
    pause
    exit /b 1
)
uv run streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8472
