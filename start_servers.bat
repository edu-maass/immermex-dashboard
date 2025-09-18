@echo off
echo ========================================
echo    INICIANDO IMMERMEX DASHBOARD
echo ========================================
echo.

echo Iniciando servidores...
echo.

REM Iniciar backend en una nueva ventana
start "Immermex Backend" cmd /k "cd backend && python run.py"

REM Esperar un poco para que el backend inicie
timeout /t 3 /nobreak >nul

REM Iniciar frontend en una nueva ventana
start "Immermex Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo    SERVIDORES INICIADOS
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
