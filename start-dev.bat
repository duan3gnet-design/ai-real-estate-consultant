@echo off
echo ==============================================
echo   AI Tu Van Bat Dong San - Dev Mode
echo ==============================================

:: Khoi dong backend trong cua so moi
start "Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

:: Doi backend khoi dong
timeout /t 2 /nobreak >nul

:: Khoi dong Electron + Vite
cd /d "%~dp0"
set NODE_ENV=development
npm run dev
