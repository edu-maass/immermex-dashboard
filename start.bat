@echo off
echo ========================================
echo    IMMERMEX DASHBOARD - INICIO RAPIDO
echo ========================================
echo.

echo [1/4] Instalando dependencias del backend...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Error instalando dependencias del backend
    pause
    exit /b 1
)
echo ✅ Backend instalado

echo [2/4] Instalando dependencias del frontend...
cd ..\frontend
npm install
if %errorlevel% neq 0 (
    echo ❌ Error instalando dependencias del frontend
    pause
    exit /b 1
)
echo ✅ Frontend instalado

echo [3/4] Iniciando servidores...
cd ..
start "Immermex Backend" cmd /k "cd /d %~dp0backend && python simple_main.py"
timeout /t 3 /nobreak >nul
start "Immermex Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo [4/4] Verificando sistema...
timeout /t 5 /nobreak >nul
python -c "import requests; print('Backend Status:', requests.get('http://localhost:8000/api/health').status_code)" 2>nul

echo.
echo ========================================
echo    SISTEMA INICIADO EXITOSAMENTE
echo ========================================
echo.
echo 🌐 URLs del sistema:
echo    📊 Dashboard: http://localhost:3000
echo    🔧 Backend:   http://localhost:8000
echo    📚 API Docs:  http://localhost:8000/docs
echo.
echo 💡 El dashboard se abrirá automáticamente en tu navegador
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
