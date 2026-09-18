@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "FRONTEND_URL=http://127.0.0.1:5173"

echo Applying database migrations...
cd /d "%BACKEND_DIR%"
.\venv\Scripts\python.exe -m alembic upgrade head
if errorlevel 1 (
    echo Database migration failed. Backend will not start.
    pause
    exit /b 1
)

echo Starting DocuMind AI backend...
start "DocuMind AI Backend" cmd /k "cd /d "%BACKEND_DIR%" && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload"

echo Starting DocuMind AI frontend...
start "DocuMind AI Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev -- --host 127.0.0.1 --port 5173"

echo Waiting for the frontend to start...
timeout /t 5 /nobreak >nul

echo Opening DocuMind AI in your browser...
start "" "%FRONTEND_URL%"

endlocal
