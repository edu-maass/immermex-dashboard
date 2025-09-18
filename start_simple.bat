@echo off
echo ========================================
echo    INICIANDO IMMERMEX DASHBOARD
echo    (Version Simplificada)
echo ========================================
echo.

echo [1/3] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado
    echo Instala Python desde https://python.org
    pause
    exit /b 1
)

echo [2/3] Instalando FastAPI...
pip install fastapi uvicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar FastAPI
    pause
    exit /b 1
)

echo [3/3] Iniciando servidores...
echo.

REM Iniciar backend simplificado
start "Immermex Backend" cmd /k "cd backend && python simple_main.py"

REM Esperar un poco
timeout /t 3 /nobreak >nul

REM Iniciar frontend
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
echo Presiona cualquier tecla para cerrar...
pause >nul
