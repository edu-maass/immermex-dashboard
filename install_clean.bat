@echo off
echo ========================================
echo    INSTALACION LIMPIA - IMMERMEX DASHBOARD
echo ========================================
echo.

echo [1/8] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado
    echo Instala Python desde https://python.org
    pause
    exit /b 1
)
echo ✅ Python encontrado

echo [2/8] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no encontrado
    echo Instala Node.js desde https://nodejs.org
    pause
    exit /b 1
)
echo ✅ Node.js encontrado

echo [3/8] Instalando dependencias del backend...
cd backend
pip install fastapi uvicorn requests
if %errorlevel% neq 0 (
    echo ERROR: Fallo instalando dependencias Python
    pause
    exit /b 1
)
echo ✅ Dependencias del backend instaladas

echo [4/8] Instalando dependencias del frontend...
cd ..\frontend
npm install
if %errorlevel% neq 0 (
    echo ERROR: Fallo instalando dependencias Node.js
    pause
    exit /b 1
)
echo ✅ Dependencias del frontend instaladas

echo [5/8] Verificando archivos del proyecto...
cd ..
if not exist "backend\simple_main.py" (
    echo ERROR: Archivo simple_main.py no encontrado
    pause
    exit /b 1
)
echo ✅ Archivos del proyecto verificados

echo [6/8] Iniciando backend...
start "Immermex Backend" cmd /k "cd /d %~dp0backend && python simple_main.py"

echo [7/8] Esperando que el backend inicie...
timeout /t 5 /nobreak >nul

echo [8/8] Iniciando frontend...
start "Immermex Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo    INSTALACION COMPLETADA
echo ========================================
echo.
echo 🌐 URLs del sistema:
echo    📊 Dashboard: http://localhost:3000
echo    🔧 Backend:   http://localhost:8000
echo    📚 API Docs:  http://localhost:8000/docs
echo.
echo ⏳ Espera unos segundos para que los servidores inicien...
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
