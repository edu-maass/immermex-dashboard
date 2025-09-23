"""
Script para verificar el despliegue en producción
"""

import requests
import time
from datetime import datetime

def test_production_endpoints():
    """Verifica que todos los endpoints de producción funcionen"""
    base_url = "https://immermex-dashboard.vercel.app"
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/api/health", "Health check"),
        ("/api/data/summary", "Data summary"),
        ("/api/kpis", "KPIs endpoint")
    ]
    
    print("🚀 Verificando endpoints de producción...")
    print(f"🌐 Base URL: {base_url}")
    print("=" * 60)
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"🔍 Probando: {description}")
            print(f"   URL: {url}")
            
            start_time = time.time()
            response = requests.get(url, timeout=30)
            end_time = time.time()
            
            response_time = round((end_time - start_time) * 1000, 2)
            
            if response.status_code == 200:
                print(f"   ✅ Status: {response.status_code} ({response_time}ms)")
                results.append(True)
            else:
                print(f"   ⚠️  Status: {response.status_code} ({response_time}ms)")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)}")
            results.append(False)
        
        print()
    
    # Resumen
    successful = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 Resumen: {successful}/{total} endpoints funcionando")
    
    if successful == total:
        print("🎉 ¡Todos los endpoints están funcionando!")
        return True
    else:
        print("⚠️  Algunos endpoints tienen problemas")
        return False

def test_database_connection():
    """Verifica la conexión a la base de datos"""
    print("\n🔍 Verificando conexión a base de datos...")
    
    try:
        # Probar el endpoint de health que incluye verificación de BD
        response = requests.get("https://immermex-dashboard.vercel.app/api/health", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("database") == "connected":
                print("✅ Base de datos conectada correctamente")
                return True
            else:
                print("⚠️  Base de datos no conectada")
                return False
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando base de datos: {str(e)}")
        return False

def main():
    """Función principal de verificación"""
    print("🚀 VERIFICACIÓN DE PRODUCCIÓN - IMMERMEX DASHBOARD")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificar endpoints
    endpoints_ok = test_production_endpoints()
    
    # Verificar base de datos
    db_ok = test_database_connection()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL")
    print("=" * 60)
    
    if endpoints_ok and db_ok:
        print("🎉 ¡DESPLIEGUE EXITOSO!")
        print("✅ Todos los endpoints funcionando")
        print("✅ Base de datos conectada")
        print("✅ Sistema listo para usar")
        print("\n🌐 URLs de producción:")
        print("   Frontend: https://immermex-dashboard.vercel.app")
        print("   Backend:  https://immermex-dashboard.vercel.app/api")
        print("   Health:   https://immermex-dashboard.vercel.app/api/health")
    else:
        print("⚠️  DESPLIEGUE CON PROBLEMAS")
        if not endpoints_ok:
            print("❌ Problemas con endpoints")
        if not db_ok:
            print("❌ Problemas con base de datos")
        print("\n🔧 Acciones recomendadas:")
        print("   1. Verificar logs en Vercel")
        print("   2. Verificar variables de entorno")
        print("   3. Verificar conexión a Supabase")

if __name__ == "__main__":
    main()
