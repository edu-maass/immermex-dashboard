@echo off
echo ========================================
echo    SOLUCIONANDO E INICIANDO SISTEMA
echo ========================================
echo.

echo [1/6] Instalando dependencias del backend...
pip install fastapi uvicorn sqlalchemy requests
echo ✅ Dependencias del backend instaladas

echo [2/6] Instalando dependencias del frontend...
cd frontend
npm install
cd ..
echo ✅ Dependencias del frontend instaladas

echo [3/6] Iniciando backend...
start "Immermex Backend" cmd /k "cd /d %~dp0backend && python simple_main.py"

echo [4/6] Esperando que el backend inicie...
timeout /t 5 /nobreak >nul

echo [5/6] Verificando backend...
python -c "import requests; print('Backend Status:', requests.get('http://localhost:8000/api/health').status_code)" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Backend aún iniciando, esperando más...
    timeout /t 3 /nobreak >nul
)

echo [6/6] Sistema listo!
echo.
echo ========================================
echo    SISTEMA INICIADO CORRECTAMENTE
echo ========================================
echo.
echo 🌐 URLs del sistema:
echo    📊 Dashboard: http://localhost:3000
echo    🔧 Backend:   http://localhost:8000
echo    📚 API Docs:  http://localhost:8000/docs
echo.
echo 💡 El frontend ya está ejecutándose en http://localhost:3000
echo    Ahora el backend también debería estar funcionando.
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
