import requests
import json
import time
import sys

def test_endpoint_detailed(endpoint, params=None, max_retries=3):
    """Prueba un endpoint con reintentos y análisis detallado"""
    base_urls = [
        "https://immermex-dashboard.vercel.app",
        "https://immermex-dashboard-backend.vercel.app"
    ]
    
    for base_url in base_urls:
        print(f"\n[TEST] Probando en: {base_url}")
        url = f"{base_url}/api{endpoint}"
        print(f"URL completa: {url}")
        
        if params:
            print(f"Parametros: {params}")
        
        for attempt in range(max_retries):
            try:
                print(f"Intento {attempt + 1}/{max_retries}")
                response = requests.get(url, params=params, timeout=30)
                
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print("[SUCCESS] Respuesta exitosa!")
                        print(f"Tipo de respuesta: {type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"Claves disponibles: {list(data.keys())}")
                            
                            # Analizar estructura específica
                            if 'labels' in data and 'data' in data:
                                labels_count = len(data.get('labels', []))
                                data_count = len(data.get('data', []))
                                print(f"Labels: {labels_count}, Data: {data_count}")
                                
                                if labels_count == 0 or data_count == 0:
                                    print("[WARNING] No hay datos en la respuesta")
                                    print(f"Labels: {data.get('labels', [])}")
                                    print(f"Data: {data.get('data', [])}")
                                else:
                                    print("[OK] Hay datos disponibles")
                                    print(f"Primeros labels: {data.get('labels', [])[:3]}")
                                    print(f"Primeros datos: {data.get('data', [])[:3]}")
                            
                            if 'titulo' in data:
                                print(f"Titulo: {data.get('titulo')}")
                                
                        elif isinstance(data, list):
                            print(f"Lista con {len(data)} elementos")
                            if len(data) == 0:
                                print("[WARNING] Lista vacia")
                            else:
                                print(f"Primer elemento: {data[0]}")
                        
                        # Mostrar respuesta completa si es pequeña
                        if len(json.dumps(data)) < 1000:
                            print(f"Respuesta completa: {json.dumps(data, indent=2)}")
                        
                        return True  # Exito en esta URL base
                        
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON invalido: {e}")
                        print(f"Contenido: {response.text[:500]}")
                        
                elif response.status_code == 404:
                    print("[ERROR] 404 - Endpoint no encontrado")
                    print(f"Contenido: {response.text}")
                    
                elif response.status_code == 500:
                    print("[ERROR] 500 - Error interno del servidor")
                    print(f"Contenido: {response.text}")
                    
                else:
                    print(f"[ERROR] HTTP {response.status_code}")
                    print(f"Contenido: {response.text[:500]}")
                
            except requests.exceptions.Timeout:
                print(f"[ERROR] Timeout en intento {attempt + 1}")
                if attempt < max_retries - 1:
                    print("Esperando 2 segundos antes del siguiente intento...")
                    time.sleep(2)
                    
            except requests.exceptions.ConnectionError as e:
                print(f"[ERROR] Error de conexion: {e}")
                if attempt < max_retries - 1:
                    print("Esperando 2 segundos antes del siguiente intento...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"[ERROR] Error inesperado: {e}")
    
    return False

def test_basic_endpoints():
    """Prueba endpoints basicos para verificar conectividad"""
    print("=" * 70)
    print("DIAGNOSTICO COMPLETO - ENDPOINTS COMPRAS V2")
    print("=" * 70)
    
    # Endpoints criticos a probar
    endpoints = [
        {
            "endpoint": "/compras-v2/kpis",
            "params": None,
            "name": "KPIs de Compras V2"
        },
        {
            "endpoint": "/compras-v2/compras-por-material", 
            "params": {"limite": 3},
            "name": "Compras por Material"
        },
        {
            "endpoint": "/compras-v2/flujo-pagos",
            "params": {"moneda": "MXN"},
            "name": "Flujo de Pagos"
        },
        {
            "endpoint": "/compras-v2/materiales",
            "params": None,
            "name": "Lista de Materiales"
        },
        {
            "endpoint": "/compras-v2/proveedores", 
            "params": None,
            "name": "Lista de Proveedores"
        }
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint_info in endpoints:
        print(f"\n{'='*50}")
        print(f"PROBANDO: {endpoint_info['name']}")
        print(f"{'='*50}")
        
        success = test_endpoint_detailed(
            endpoint_info["endpoint"], 
            endpoint_info["params"]
        )
        
        if success:
            success_count += 1
            print(f"[RESULTADO] {endpoint_info['name']}: EXITOSO")
        else:
            print(f"[RESULTADO] {endpoint_info['name']}: FALLO")
    
    print(f"\n{'='*70}")
    print(f"RESUMEN: {success_count}/{total_count} endpoints funcionando")
    print(f"{'='*70}")
    
    if success_count == 0:
        print("\n[CRITICO] Ningun endpoint funciona. Posibles causas:")
        print("1. Deployment en Vercel no completo")
        print("2. Problemas de configuracion")
        print("3. Base de datos no accesible")
        print("4. Errores en el codigo")
    elif success_count < total_count:
        print(f"\n[PARCIAL] Solo {success_count}/{total_count} endpoints funcionan")
        print("Algunos endpoints pueden tener problemas especificos")
    else:
        print("\n[EXITO] Todos los endpoints funcionan correctamente")

def test_cors_and_health():
    """Prueba conectividad basica y CORS"""
    print(f"\n{'='*50}")
    print("PRUEBAS DE CONECTIVIDAD BASICA")
    print(f"{'='*50}")
    
    # Probar CORS test endpoint
    test_endpoint_detailed("/cors-test", None)
    
    # Probar endpoint de health si existe
    test_endpoint_detailed("/health", None)

if __name__ == "__main__":
    print("Iniciando diagnostico completo...")
    print("Esto puede tomar unos minutos...")
    
    # Esperar un poco para que Vercel complete el deployment
    print("\nEsperando 10 segundos para deployment...")
    time.sleep(10)
    
    test_cors_and_health()
    test_basic_endpoints()
    
    print("\nDiagnostico completado.")
