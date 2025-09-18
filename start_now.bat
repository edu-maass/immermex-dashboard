@echo off
echo ========================================
echo    INICIANDO IMMERMEX DASHBOARD
echo ========================================
echo.

echo Iniciando backend...
start "Backend" cmd /k "cd /d %~dp0backend && python simple_main.py"

echo Esperando 3 segundos...
timeout /t 3 /nobreak >nul

echo Iniciando frontend...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo    SERVIDORES INICIADOS
echo ========================================
echo.
echo Dashboard: http://localhost:3000
echo Backend:   http://localhost:8000
echo.
echo Espera unos segundos y luego abre:
echo http://localhost:3000
echo.
pause
