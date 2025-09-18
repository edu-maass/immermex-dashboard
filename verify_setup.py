#!/usr/bin/env python3
"""
Script de verificación para el Dashboard Immermex
Verifica que todas las dependencias estén instaladas y el sistema funcione
"""

import subprocess
import sys
import requests
import time
import os

def check_python_packages():
    """Verifica que los paquetes de Python estén instalados"""
    print("🔍 Verificando paquetes de Python...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'sqlalchemy', 
        'requests', 'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - FALTANTE")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Instalando paquetes faltantes: {', '.join(missing_packages)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages)
    
    return len(missing_packages) == 0

def check_node_packages():
    """Verifica que los paquetes de Node.js estén instalados"""
    print("\n🔍 Verificando paquetes de Node.js...")
    
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    if not os.path.exists(frontend_dir):
        print("  ❌ Directorio frontend no encontrado")
        return False
    
    # Verificar si node_modules existe
    node_modules = os.path.join(frontend_dir, 'node_modules')
    if not os.path.exists(node_modules):
        print("  📦 Instalando dependencias de Node.js...")
        result = subprocess.run(['npm', 'install'], cwd=frontend_dir, capture_output=True)
        if result.returncode != 0:
            print(f"  ❌ Error instalando dependencias: {result.stderr.decode()}")
            return False
    
    print("  ✅ Dependencias de Node.js instaladas")
    return True

def check_backend():
    """Verifica que el backend esté funcionando"""
    print("\n🔍 Verificando backend...")
    
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            print("  ✅ Backend funcionando correctamente")
            return True
        else:
            print(f"  ❌ Backend respondió con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("  ❌ Backend no está ejecutándose")
        return False

def check_frontend():
    """Verifica que el frontend esté funcionando"""
    print("\n🔍 Verificando frontend...")
    
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("  ✅ Frontend funcionando correctamente")
            return True
        else:
            print(f"  ❌ Frontend respondió con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("  ❌ Frontend no está ejecutándose")
        return False

def main():
    """Función principal de verificación"""
    print("=" * 50)
    print("🚀 VERIFICACIÓN DEL DASHBOARD IMMERMEX")
    print("=" * 50)
    
    # Verificar paquetes
    python_ok = check_python_packages()
    node_ok = check_node_packages()
    
    if not python_ok or not node_ok:
        print("\n❌ Error en la instalación de dependencias")
        return False
    
    # Verificar servicios
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    print("\n" + "=" * 50)
    if backend_ok and frontend_ok:
        print("✅ SISTEMA COMPLETAMENTE FUNCIONAL")
        print("\n🌐 URLs del sistema:")
        print("   📊 Dashboard: http://localhost:3000")
        print("   🔧 Backend:   http://localhost:8000")
        print("   📚 API Docs:  http://localhost:8000/docs")
    else:
        print("❌ SISTEMA CON PROBLEMAS")
        if not backend_ok:
            print("   - Backend no está funcionando")
        if not frontend_ok:
            print("   - Frontend no está funcionando")
        print("\n💡 Ejecuta 'start.bat' (Windows) o './start.sh' (Linux/Mac)")
    
    print("=" * 50)
    return backend_ok and frontend_ok

if __name__ == "__main__":
    main()
