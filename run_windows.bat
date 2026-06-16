@echo off
echo =========================================
echo Starting KESCO Billing Analysis Dashboard
echo =========================================

echo Starting Python Backend...
start "KESCO Backend" cmd /c "cd backend && pip install -r ../requirements.txt && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Starting React Frontend...
start "KESCO Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo Application is booting up!
echo The React frontend will open in your browser shortly (usually http://localhost:5173).
pause
