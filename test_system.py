#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema Immermex Dashboard
"""

import sys
import os
import requests
import time
import subprocess
from pathlib import Path

def test_backend():
    """Prueba el backend FastAPI"""
    print("🔍 Probando backend...")
    
    try:
        # Verificar que el backend esté ejecutándose
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend funcionando correctamente")
            return True
        else:
            print(f"❌ Backend respondió con código: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al backend. ¿Está ejecutándose?")
        return False
    except Exception as e:
        print(f"❌ Error probando backend: {e}")
        return False

def test_frontend():
    """Prueba el frontend React"""
    print("🔍 Probando frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend funcionando correctamente")
            return True
        else:
            print(f"❌ Frontend respondió con código: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al frontend. ¿Está ejecutándose?")
        return False
    except Exception as e:
        print(f"❌ Error probando frontend: {e}")
        return False

def test_api_endpoints():
    """Prueba los endpoints de la API"""
    print("🔍 Probando endpoints de API...")
    
    endpoints = [
        "/api/kpis",
        "/api/graficos/aging",
        "/api/graficos/top-clientes",
        "/api/graficos/consumo-material",
        "/api/archivos"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                success_count += 1
            else:
                print(f"❌ {endpoint} - Código: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    print(f"📊 {success_count}/{len(endpoints)} endpoints funcionando")
    return success_count == len(endpoints)

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    # Verificar Python
    try:
        import pandas
        import fastapi
        import sqlalchemy
        print("✅ Dependencias Python instaladas")
    except ImportError as e:
        print(f"❌ Faltan dependencias Python: {e}")
        return False
    
    # Verificar Node.js (opcional)
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js instalado: {result.stdout.strip()}")
        else:
            print("⚠️ Node.js no encontrado")
    except FileNotFoundError:
        print("⚠️ Node.js no encontrado")
    
    return True

def check_database():
    """Verifica que la base de datos esté configurada"""
    print("🔍 Verificando base de datos...")
    
    db_path = Path("backend/immermex.db")
    if db_path.exists():
        print("✅ Base de datos SQLite encontrada")
        return True
    else:
        print("❌ Base de datos no encontrada. Ejecuta: npm run setup")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas del sistema Immermex Dashboard")
    print("=" * 50)
    
    tests = [
        ("Dependencias", check_dependencies),
        ("Base de datos", check_database),
        ("Backend", test_backend),
        ("Frontend", test_frontend),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 20)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡Sistema funcionando correctamente!")
        print("\n🌐 Accede a:")
        print("   Frontend: http://localhost:3000")
        print("   Backend:  http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
        print("\n💡 Soluciones comunes:")
        print("   1. Ejecuta: npm run setup")
        print("   2. Ejecuta: npm run dev")
        print("   3. Verifica que los puertos 3000 y 8000 estén libres")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
