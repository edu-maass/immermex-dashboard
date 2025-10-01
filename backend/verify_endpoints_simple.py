#!/usr/bin/env python3
"""
Script simple para verificar endpoints sin emojis
"""

import requests
import time
import json

BASE_URL = "https://immermex-dashboard-api.vercel.app"

# Endpoints principales a verificar
ENDPOINTS = [
    {"path": "/api/kpis", "description": "KPIs principales"},
    {"path": "/api/filtros-disponibles", "description": "Filtros disponibles"},
    {"path": "/api/pedidos-filtro", "description": "Lista de pedidos"},
    {"path": "/api/clientes-filtro", "description": "Lista de clientes"},
    {"path": "/api/materiales-filtro", "description": "Lista de materiales"},
    {"path": "/api/graficos/aging", "description": "Grafico aging"},
    {"path": "/api/graficos/top-clientes", "description": "Grafico top clientes"},
    {"path": "/api/graficos/consumo-material", "description": "Grafico consumo material"},
    {"path": "/api/compras/kpis", "description": "KPIs de compras"},
    {"path": "/api/compras/evolucion-precios", "description": "Evolucion de precios"},
    {"path": "/api/compras/flujo-pagos", "description": "Flujo de pagos"},
    {"path": "/api/compras/aging-cuentas-pagar", "description": "Aging cuentas por pagar"},
    {"path": "/api/compras/materiales", "description": "Materiales de compras"},
    {"path": "/api/archivos-procesados", "description": "Archivos procesados"},
    {"path": "/api/data-summary", "description": "Resumen de datos"},
]

def test_endpoint(endpoint):
    """Prueba un endpoint específico"""
    url = f"{BASE_URL}{endpoint['path']}"
    
    try:
        response = requests.get(url, timeout=15)
        status = "OK" if response.status_code == 200 else f"ERROR {response.status_code}"
        
        try:
            json_data = response.json()
            data_type = type(json_data).__name__
            if isinstance(json_data, dict):
                data_size = len(json_data)
            elif isinstance(json_data, list):
                data_size = len(json_data)
            else:
                data_size = "N/A"
        except:
            data_type = "text"
            data_size = len(response.text)
        
        return {
            'path': endpoint['path'],
            'description': endpoint['description'],
            'status': status,
            'status_code': response.status_code,
            'data_type': data_type,
            'data_size': data_size,
            'response_time': response.elapsed.total_seconds()
        }
        
    except requests.exceptions.Timeout:
        return {
            'path': endpoint['path'],
            'description': endpoint['description'],
            'status': "TIMEOUT",
            'status_code': None,
            'data_type': None,
            'data_size': None,
            'response_time': 15.0
        }
    except Exception as e:
        return {
            'path': endpoint['path'],
            'description': endpoint['description'],
            'status': f"ERROR: {str(e)[:30]}",
            'status_code': None,
            'data_type': None,
            'data_size': None,
            'response_time': None
        }

def main():
    """Función principal"""
    print("Verificando endpoints de Immermex Dashboard API")
    print("=" * 50)
    print(f"URL Base: {BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    for i, endpoint in enumerate(ENDPOINTS, 1):
        print(f"[{i:2d}/{len(ENDPOINTS)}] Probando {endpoint['path']}...", end=" ")
        
        result = test_endpoint(endpoint)
        results.append(result)
        
        print(f"{result['status']}")
        
        time.sleep(0.5)
    
    print()
    print("RESUMEN DE RESULTADOS")
    print("=" * 50)
    
    ok_count = sum(1 for r in results if r['status'] == "OK")
    error_count = sum(1 for r in results if "ERROR" in r['status'])
    timeout_count = sum(1 for r in results if r['status'] == "TIMEOUT")
    
    print(f"Exitosos: {ok_count}")
    print(f"Errores: {error_count}")
    print(f"Timeouts: {timeout_count}")
    print(f"Total: {len(results)}")
    print()
    
    # Mostrar errores
    errors = [r for r in results if r['status'] != "OK"]
    
    if errors:
        print("ENDPOINTS CON PROBLEMAS:")
        print("-" * 30)
        for error in errors:
            print(f"  {error['path']} - {error['description']}")
            print(f"    Estado: {error['status']}")
            if error['status_code']:
                print(f"    Codigo: {error['status_code']}")
            print()
    else:
        print("Todos los endpoints estan funcionando correctamente!")
    
    print()
    print("TABLA DETALLADA:")
    print("-" * 70)
    print(f"{'Endpoint':<30} {'Estado':<15} {'Tipo':<10} {'Tamaño':<8} {'Tiempo':<8}")
    print("-" * 70)
    
    for result in results:
        path_short = result['path'][:29]
        status_short = result['status'][:14]
        data_type_short = str(result['data_type'])[:9] if result['data_type'] else "N/A"
        data_size_str = str(result['data_size'])[:7] if result['data_size'] else "N/A"
        response_time_str = f"{result['response_time']:.2f}s" if result['response_time'] else "N/A"
        
        print(f"{path_short:<30} {status_short:<15} {data_type_short:<10} {data_size_str:<8} {response_time_str:<8}")

if __name__ == "__main__":
    main()
