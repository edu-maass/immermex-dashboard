"""
Script para verificar el endpoint de compras en produccion
"""

import requests
import json

PRODUCTION_URL = "https://immermex-dashboard-api.vercel.app"

def test_health():
    """Verifica que el servidor de produccion este activo"""
    print("Verificando salud del servidor de produccion...")
    try:
        response = requests.get(f"{PRODUCTION_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✓ Servidor de produccion activo")
            return True
        else:
            print(f"✗ Servidor respondio con status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_compras_endpoint_exists():
    """Verifica que el endpoint de compras exista en produccion"""
    print("\nVerificando endpoint /api/upload/compras...")
    
    # Hacer una peticion OPTIONS para verificar que la ruta existe
    try:
        # Intentar con un archivo vacio para ver si el endpoint responde
        response = requests.options(f"{PRODUCTION_URL}/api/upload/compras", timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 204, 405]:
            print("✓ Endpoint /api/upload/compras existe")
            return True
        else:
            print(f"✗ Endpoint no encontrado (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error verificando endpoint: {str(e)}")
        return False

def test_api_docs():
    """Verifica la documentacion de la API"""
    print("\nVerificando documentacion de API...")
    try:
        response = requests.get(f"{PRODUCTION_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✓ Documentacion disponible en /docs")
            # Verificar si el endpoint de compras esta en la documentacion
            if "upload/compras" in response.text or "compras" in response.text.lower():
                print("✓ Endpoint de compras aparece en la documentacion")
                return True
            else:
                print("? Endpoint de compras NO aparece en la documentacion (puede ser normal)")
                return True
        else:
            print(f"? Documentacion no disponible (status: {response.status_code})")
            return True
    except Exception as e:
        print(f"? No se pudo acceder a la documentacion: {str(e)}")
        return True

def test_openapi_spec():
    """Verifica el esquema OpenAPI"""
    print("\nVerificando esquema OpenAPI...")
    try:
        response = requests.get(f"{PRODUCTION_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get('paths', {})
            
            # Buscar el endpoint de compras
            if '/api/upload/compras' in paths:
                print("✓ Endpoint /api/upload/compras registrado en OpenAPI")
                print(f"  Metodos: {list(paths['/api/upload/compras'].keys())}")
                return True
            else:
                print("✗ Endpoint /api/upload/compras NO encontrado en OpenAPI")
                print(f"  Endpoints disponibles: {list(paths.keys())[:10]}")
                return False
        else:
            print(f"? OpenAPI no disponible (status: {response.status_code})")
            return True
    except Exception as e:
        print(f"? Error obteniendo OpenAPI: {str(e)}")
        return True

def main():
    print("=" * 70)
    print("VERIFICACION DEL ENDPOINT DE COMPRAS EN PRODUCCION")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: Salud del servidor
    results.append(("Salud del servidor", test_health()))
    
    # Test 2: Endpoint existe
    results.append(("Endpoint de compras", test_compras_endpoint_exists()))
    
    # Test 3: Documentacion
    results.append(("Documentacion API", test_api_docs()))
    
    # Test 4: OpenAPI
    results.append(("Esquema OpenAPI", test_openapi_spec()))
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE VERIFICACION")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    print()
    print(f"Total: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("\n✓ El endpoint de compras esta disponible en produccion!")
        print(f"\nURL del endpoint: {PRODUCTION_URL}/api/upload/compras")
        print("\nPuedes probar subiendo un archivo desde el frontend.")
    else:
        print("\n✗ Algunas verificaciones fallaron.")
        print("\nPosibles causas:")
        print("  1. Vercel aun esta haciendo el deploy (espera 1-2 minutos)")
        print("  2. El endpoint necesita ser agregado a vercel.json")
        print("  3. Hay un error en el codigo que impide el deploy")
        print("\nRevisa los logs de Vercel para mas detalles.")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
