@echo off
echo ========================================
echo    INICIANDO IMMERMEX DASHBOARD
echo ========================================
echo.

echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado
    echo Instala Python desde https://python.org
    pause
    exit /b 1
)
echo Python encontrado

echo [2/4] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no encontrado
    echo Instala Node.js desde https://nodejs.org
    pause
    exit /b 1
)
echo Node.js encontrado

echo [3/4] Instalando dependencias...
cd backend
pip install fastapi uvicorn >nul 2>&1
cd ..\frontend
npm install >nul 2>&1
cd ..

echo [4/4] Iniciando servidores...

REM Iniciar backend
start "Immermex Backend" cmd /k "cd /d %~dp0backend && python simple_main.py"

REM Esperar 3 segundos
timeout /t 3 /nobreak >nul

REM Iniciar frontend
start "Immermex Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo    SERVIDORES INICIADOS
echo ========================================
echo.
echo Dashboard: http://localhost:3000
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Espera unos segundos para que los servidores inicien...
echo.
pause
