#!/usr/bin/env python3
"""
Script para verificar que el sistema Immermex Dashboard esté funcionando
"""

import requests
import time
import sys

def check_backend():
    """Verifica que el backend esté funcionando"""
    print("🔍 Verificando backend...")
    
    try:
        # Esperar un poco para que el servidor inicie
        time.sleep(2)
        
        # Probar endpoint de salud
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

def check_frontend():
    """Verifica que el frontend esté funcionando"""
    print("🔍 Verificando frontend...")
    
    try:
        # Esperar un poco para que el servidor inicie
        time.sleep(2)
        
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

def check_api_endpoints():
    """Prueba los endpoints de la API"""
    print("🔍 Probando endpoints de API...")
    
    endpoints = [
        ("/api/kpis", "KPIs principales"),
        ("/api/graficos/aging", "Gráfico de aging"),
        ("/api/graficos/top-clientes", "Top clientes"),
        ("/api/graficos/consumo-material", "Consumo de material"),
        ("/api/archivos", "Archivos procesados")
    ]
    
    success_count = 0
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}")
                success_count += 1
            else:
                print(f"❌ {description} - Código: {response.status_code}")
        except Exception as e:
            print(f"❌ {description} - Error: {e}")
    
    print(f"📊 {success_count}/{len(endpoints)} endpoints funcionando")
    return success_count == len(endpoints)

def main():
    """Función principal de verificación"""
    print("🚀 VERIFICACIÓN DEL SISTEMA IMMERMEX DASHBOARD")
    print("=" * 60)
    
    tests = [
        ("Backend", check_backend),
        ("Frontend", check_frontend),
        ("API Endpoints", check_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ FUNCIONANDO" if result else "❌ FALLANDO"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} componentes funcionando")
    
    if passed == len(results):
        print("\n🎉 ¡SISTEMA FUNCIONANDO CORRECTAMENTE!")
        print("\n🌐 Accede a:")
        print("   📊 Dashboard: http://localhost:3000")
        print("   🔧 Backend:   http://localhost:8000")
        print("   📚 API Docs:  http://localhost:8000/docs")
        print("\n💡 Funcionalidades disponibles:")
        print("   - Visualización de KPIs")
        print("   - Gráficos interactivos")
        print("   - Filtros de datos")
        print("   - Subida de archivos")
    else:
        print("\n⚠️ Algunos componentes no están funcionando.")
        print("💡 Soluciones:")
        print("   1. Ejecuta: start_simple.bat")
        print("   2. Verifica que los puertos 3000 y 8000 estén libres")
        print("   3. Revisa que Python y Node.js estén instalados")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
