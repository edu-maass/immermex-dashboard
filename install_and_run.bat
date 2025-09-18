@echo off
echo ========================================
echo    IMMERMEX DASHBOARD - INSTALACION
echo ========================================
echo.

echo [1/5] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado. Instala Python 3.8+ desde https://python.org
    pause
    exit /b 1
)

echo [2/5] Verificando Node.js...
node --version
if %errorlevel% neq 0 (
    echo ERROR: Node.js no encontrado. Instala Node.js desde https://nodejs.org
    pause
    exit /b 1
)

echo [3/5] Instalando dependencias del backend...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Fallo instalando dependencias Python
    pause
    exit /b 1
)

echo [4/5] Instalando dependencias del frontend...
cd ..\frontend
npm install
if %errorlevel% neq 0 (
    echo ERROR: Fallo instalando dependencias Node.js
    pause
    exit /b 1
)

echo [5/5] Inicializando base de datos...
cd ..\backend
python -c "from database import init_db; init_db(); print('Base de datos inicializada')"
if %errorlevel% neq 0 (
    echo ERROR: Fallo inicializando base de datos
    pause
    exit /b 1
)

echo.
echo ========================================
echo    INSTALACION COMPLETADA EXITOSAMENTE
echo ========================================
echo.
echo Para ejecutar el sistema:
echo   1. Ejecuta: start_servers.bat
echo   2. O ejecuta manualmente:
echo      - Backend: cd backend && python run.py
echo      - Frontend: cd frontend && npm run dev
echo.
echo URLs:
echo   - Frontend: http://localhost:3000
echo   - Backend:  http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
pause
