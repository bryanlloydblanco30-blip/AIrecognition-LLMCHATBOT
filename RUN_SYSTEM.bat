@echo off
REM ╔══════════════════════════════════════════════════════════════════════╗
REM ║         Group-6 FinalCognate — Windows Launcher                     ║
REM ║  Opens 3 separate terminal windows:                                  ║
REM ║    Window 1 → Classifier backend   http://localhost:8000             ║
REM ║    Window 2 → EcoBot chatbot       http://localhost:8001             ║
REM ║    Window 3 → Next.js frontend     http://localhost:3000             ║
REM ╚══════════════════════════════════════════════════════════════════════╝

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║         Group-6 FinalCognate — Windows Launcher                     ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

REM ── Get the folder where this batch file lives ─────────────────────────
SET "ROOT=%~dp0"
REM Remove trailing backslash
IF "%ROOT:~-1%"=="\" SET "ROOT=%ROOT:~0,-1%"

echo Project root: %ROOT%
echo.

REM ── Load .env variables ───────────────────────────────────────────────
IF EXIST "%ROOT%\.env" (
  echo Loading .env ...
  FOR /F "eol=# usebackq tokens=1,* delims==" %%A IN ("%ROOT%\.env") DO (
    IF NOT "%%A"=="" SET "%%A=%%B"
  )
)

REM ── 1. Classifier backend (port 8000) ─────────────────────────────────
echo Starting Classifier backend on port 8000 ...
START "Classifier Backend :8000" cmd /k "cd /d %ROOT%\backend\trash-uibackend && call %ROOT%\.venv\Scripts\activate.bat && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

REM ── 2. EcoBot chatbot backend (port 8001) ─────────────────────────────
echo Starting EcoBot chatbot backend on port 8001 ...
START "EcoBot Chatbot :8001" cmd /k "cd /d %ROOT%\backend\llmchatbotbackend && call %ROOT%\.venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

REM ── 3. Next.js frontend (port 3000) ───────────────────────────────────
echo Starting Trash-UI frontend on port 3000 ...
START "Trash-UI Frontend :3000" cmd /k "cd /d %ROOT%\frontend\trash-ui && npm run dev"

REM ── 4. llmchatbot  (port 3001) ───────────────────────────────────
echo Starting llmchatbot on port 3001 ...
START "llmchatbot  Frontend :3001" cmd /k "cd /d %ROOT%\frontend\llmchatbot && npm run dev"

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   All services launched in separate windows.
echo.
echo   Dashboard  →  http://localhost:3000
echo   Scan       →  http://localhost:3000/scan
echo   Chat       →  http://localhost:3001/chat
echo   Classifier API  →  http://localhost:8000/docs
echo   EcoBot API      →  http://localhost:8001/docs
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
pause
