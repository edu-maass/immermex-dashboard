"""
Script para verificar el despliegue híbrido (GitHub Pages + Vercel)
"""

import requests
import time
from datetime import datetime

def test_github_pages():
    """Verifica que GitHub Pages esté funcionando"""
    print("🔍 Verificando GitHub Pages...")
    
    try:
        url = "https://edu-maass.github.io/immermex-dashboard/"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print("✅ GitHub Pages funcionando correctamente")
            return True
        else:
            print(f"⚠️  GitHub Pages - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en GitHub Pages: {str(e)}")
        return False

def test_vercel_backend():
    """Verifica que el backend en Vercel esté funcionando"""
    print("🔍 Verificando backend en Vercel...")
    
    endpoints = [
        ("/api/health", "Health check"),
        ("/api/data/summary", "Data summary"),
        ("/api/kpis", "KPIs endpoint")
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            url = f"https://immermex-dashboard.vercel.app{endpoint}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {description} - OK")
                results.append(True)
            else:
                print(f"⚠️  {description} - Status: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {description} - Error: {str(e)}")
            results.append(False)
    
    return all(results)

def test_cors_configuration():
    """Verifica la configuración de CORS"""
    print("🔍 Verificando configuración de CORS...")
    
    try:
        # Simular una petición desde GitHub Pages
        headers = {
            'Origin': 'https://edu-maass.github.io',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(
            "https://immermex-dashboard.vercel.app/api/health",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ CORS configurado correctamente")
            return True
        else:
            print(f"⚠️  CORS - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando CORS: {str(e)}")
        return False

def test_database_connection():
    """Verifica la conexión a la base de datos"""
    print("🔍 Verificando conexión a base de datos...")
    
    try:
        response = requests.get(
            "https://immermex-dashboard.vercel.app/api/health",
            timeout=30
        )
        
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
    print("🚀 VERIFICACIÓN DE DESPLIEGUE HÍBRIDO")
    print("📱 GitHub Pages + ☁️  Vercel + 🗄️  Supabase")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Verificar componentes
    github_ok = test_github_pages()
    backend_ok = test_vercel_backend()
    cors_ok = test_cors_configuration()
    db_ok = test_database_connection()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL")
    print("=" * 60)
    
    if github_ok and backend_ok and cors_ok and db_ok:
        print("🎉 ¡DESPLIEGUE HÍBRIDO EXITOSO!")
        print("✅ GitHub Pages funcionando")
        print("✅ Backend en Vercel funcionando")
        print("✅ CORS configurado correctamente")
        print("✅ Base de datos conectada")
        print("✅ Sistema listo para usar")
        print("\n🌐 URLs de producción:")
        print("   Frontend: https://edu-maass.github.io/immermex-dashboard/")
        print("   Backend:  https://immermex-dashboard.vercel.app/api")
        print("   Health:   https://immermex-dashboard.vercel.app/api/health")
    else:
        print("⚠️  DESPLIEGUE CON PROBLEMAS")
        if not github_ok:
            print("❌ Problemas con GitHub Pages")
        if not backend_ok:
            print("❌ Problemas con backend en Vercel")
        if not cors_ok:
            print("❌ Problemas con configuración CORS")
        if not db_ok:
            print("❌ Problemas con base de datos")
        print("\n🔧 Acciones recomendadas:")
        print("   1. Verificar logs en Vercel")
        print("   2. Verificar configuración en Supabase")
        print("   3. Verificar despliegue en GitHub")
        print("   4. Ejecutar este script para diagnóstico")

if __name__ == "__main__":
    main()
