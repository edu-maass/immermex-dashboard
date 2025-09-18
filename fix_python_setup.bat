@echo off
echo ========================================
echo    SOLUCIONANDO PROBLEMAS DE PYTHON
echo ========================================
echo.

echo [1/6] Verificando Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python no encontrado en PATH. Buscando alternativas...
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Python no encontrado. Instala Python desde https://python.org
        echo Asegurate de marcar "Add Python to PATH" durante la instalacion
        pause
        exit /b 1
    ) else (
        echo Usando 'py' en lugar de 'python'
        set PYTHON_CMD=py
    )
) else (
    echo Python encontrado
    set PYTHON_CMD=python
)

echo [2/6] Verificando pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip no encontrado. Instalando pip...
    %PYTHON_CMD% -m ensurepip --upgrade
)

echo [3/6] Actualizando pip...
%PYTHON_CMD% -m pip install --upgrade pip

echo [4/6] Instalando dependencias del backend...
cd backend
%PYTHON_CMD% -m pip install fastapi uvicorn pandas openpyxl sqlalchemy python-multipart python-dotenv pydantic

echo [5/6] Verificando instalacion...
%PYTHON_CMD% -c "import fastapi, pandas, sqlalchemy; print('Dependencias instaladas correctamente')"
if %errorlevel% neq 0 (
    echo ERROR: Fallo verificando dependencias
    pause
    exit /b 1
)

echo [6/6] Inicializando base de datos...
%PYTHON_CMD% -c "from database import init_db; init_db(); print('Base de datos inicializada')"
if %errorlevel% neq 0 (
    echo ERROR: Fallo inicializando base de datos
    pause
    exit /b 1
)

echo.
echo ========================================
echo    PYTHON CONFIGURADO CORRECTAMENTE
echo ========================================
echo.
echo Para ejecutar el backend:
echo   cd backend
echo   %PYTHON_CMD% run.py
echo.
echo Para ejecutar el frontend:
echo   cd frontend
echo   npm run dev
echo.
pause
