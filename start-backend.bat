@echo off
echo ==============================================
echo   AI Tu Van Bat Dong San - Khoi dong Backend
echo ==============================================

cd /d "%~dp0backend"

IF NOT EXIST ".venv" (
  echo Tao virtual environment...
  python -m venv .venv
)

echo Kich hoat virtual environment...
call .venv\Scripts\activate.bat

echo Cai dat dependencies...
pip install -r requirements.txt -q

echo.
echo Backend dang chay tai http://127.0.0.1:8765
echo Nhan Ctrl+C de dung.
echo.

python main.py
