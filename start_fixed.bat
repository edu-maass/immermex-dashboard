@echo off
echo ========================================
echo    INICIANDO IMMERMEX DASHBOARD
echo ========================================
echo.

echo [1/5] Instalando dependencias del backend...
pip install fastapi uvicorn requests pandas sqlalchemy
echo ✅ Dependencias del backend instaladas

echo [2/5] Instalando dependencias del frontend...
cd frontend
npm install @tailwindcss/postcss
echo ✅ Dependencias del frontend instaladas

echo [3/5] Iniciando backend...
cd ..
start "Immermex Backend" cmd /k "cd /d %~dp0backend && python simple_main.py"

echo [4/5] Esperando que el backend inicie...
timeout /t 5 /nobreak >nul

echo [5/5] Verificando sistema...
python -c "import requests; print('Backend Status:', requests.get('http://localhost:8000/api/health').status_code)" 2>nul

echo.
echo ========================================
echo    SISTEMA INICIADO
echo ========================================
echo.
echo 🌐 URLs del sistema:
echo    📊 Dashboard: http://localhost:3001 (o 3000)
echo    🔧 Backend:   http://localhost:8000
echo    📚 API Docs:  http://localhost:8000/docs
echo.
echo 💡 El frontend ya está ejecutándose.
echo    Ahora el backend también debería estar funcionando.
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
