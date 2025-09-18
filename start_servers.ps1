# Script de PowerShell para iniciar Immermex Dashboard
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    INICIANDO IMMERMEX DASHBOARD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado. Instala Python desde https://python.org" -ForegroundColor Red
    Read-Host "Presiona Enter para continuar..."
    exit 1
}

# Verificar Node.js
Write-Host "Verificando Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js no encontrado. Instala Node.js desde https://nodejs.org" -ForegroundColor Red
    Read-Host "Presiona Enter para continuar..."
    exit 1
}

# Instalar dependencias del backend
Write-Host "Instalando dependencias del backend..." -ForegroundColor Yellow
Set-Location "backend"
try {
    pip install fastapi uvicorn
    Write-Host "✅ Dependencias del backend instaladas" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Error instalando dependencias del backend" -ForegroundColor Yellow
}

# Iniciar backend
Write-Host "Iniciando backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python simple_main.py" -WindowStyle Normal

# Esperar un poco
Start-Sleep -Seconds 3

# Volver al directorio raíz
Set-Location ".."

# Instalar dependencias del frontend
Write-Host "Instalando dependencias del frontend..." -ForegroundColor Yellow
Set-Location "frontend"
try {
    npm install
    Write-Host "✅ Dependencias del frontend instaladas" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Error instalando dependencias del frontend" -ForegroundColor Yellow
}

# Iniciar frontend
Write-Host "Iniciando frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Normal

# Volver al directorio raíz
Set-Location ".."

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    SERVIDORES INICIADOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 URLs del sistema:" -ForegroundColor Green
Write-Host "   📊 Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "   🔧 Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   📚 API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⏳ Espera unos segundos para que los servidores inicien completamente..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar esta ventana..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
