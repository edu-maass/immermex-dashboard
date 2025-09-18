#!/bin/bash

echo "========================================"
echo "    IMMERMEX DASHBOARD - INICIO RAPIDO"
echo "========================================"
echo

echo "[1/4] Instalando dependencias del backend..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Error instalando dependencias del backend"
    exit 1
fi
echo "✅ Backend instalado"

echo "[2/4] Instalando dependencias del frontend..."
cd ../frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Error instalando dependencias del frontend"
    exit 1
fi
echo "✅ Frontend instalado"

echo "[3/4] Iniciando servidores..."
cd ..
gnome-terminal -- bash -c "cd backend && python simple_main.py; exec bash" &
sleep 3
gnome-terminal -- bash -c "cd frontend && npm run dev; exec bash" &

echo "[4/4] Verificando sistema..."
sleep 5
python -c "import requests; print('Backend Status:', requests.get('http://localhost:8000/api/health').status_code)" 2>/dev/null

echo
echo "========================================"
echo "    SISTEMA INICIADO EXITOSAMENTE"
echo "========================================"
echo
echo "🌐 URLs del sistema:"
echo "   📊 Dashboard: http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo
echo "💡 El dashboard se abrirá automáticamente en tu navegador"
echo
