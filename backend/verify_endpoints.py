#!/usr/bin/env python3
"""
Script para verificar que todos los endpoints estén funcionando correctamente
después del cambio de import de DatabaseService
"""

import requests
import time
import json

BASE_URL = "https://immermex-dashboard-api.vercel.app"

# Lista de endpoints a verificar
ENDPOINTS = [
    # Endpoints principales
    {"path": "/api/kpis", "method": "GET", "description": "KPIs principales"},
    {"path": "/api/filtros-disponibles", "method": "GET", "description": "Filtros disponibles"},
    {"path": "/api/pedidos-filtro", "method": "GET", "description": "Lista de pedidos"},
    {"path": "/api/clientes-filtro", "method": "GET", "description": "Lista de clientes"},
    {"path": "/api/materiales-filtro", "method": "GET", "description": "Lista de materiales"},
    
    # Endpoints de gráficos
    {"path": "/api/graficos/aging", "method": "GET", "description": "Gráfico aging"},
    {"path": "/api/graficos/top-clientes", "method": "GET", "description": "Gráfico top clientes"},
    {"path": "/api/graficos/consumo-material", "method": "GET", "description": "Gráfico consumo material"},
    
    # Endpoints de compras (nuevos)
    {"path": "/api/compras/kpis", "method": "GET", "description": "KPIs de compras"},
    {"path": "/api/compras/evolucion-precios", "method": "GET", "description": "Evolución de precios"},
    {"path": "/api/compras/flujo-pagos", "method": "GET", "description": "Flujo de pagos"},
    {"path": "/api/compras/aging-cuentas-pagar", "method": "GET", "description": "Aging cuentas por pagar"},
    {"path": "/api/compras/materiales", "method": "GET", "description": "Materiales de compras"},
    
    # Endpoints adicionales
    {"path": "/api/archivos-procesados", "method": "GET", "description": "Archivos procesados"},
    {"path": "/api/data-summary", "method": "GET", "description": "Resumen de datos"},
    {"path": "/api/system-performance", "method": "GET", "description": "Performance del sistema"},
]

def test_endpoint(endpoint):
    """Prueba un endpoint específico"""
    url = f"{BASE_URL}{endpoint['path']}"
    
    try:
        if endpoint['method'] == 'GET':
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, timeout=10)
        
        status = "✅ OK" if response.status_code == 200 else f"❌ ERROR {response.status_code}"
        
        # Intentar parsear JSON si es posible
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
            data_type = "text/other"
            data_size = len(response.text)
        
        return {
            'endpoint': endpoint['path'],
            'description': endpoint['description'],
            'status': status,
            'status_code': response.status_code,
            'data_type': data_type,
            'data_size': data_size,
            'response_time': response.elapsed.total_seconds()
        }
        
    except requests.exceptions.Timeout:
        return {
            'endpoint': endpoint['path'],
            'description': endpoint['description'],
            'status': "⏰ TIMEOUT",
            'status_code': None,
            'data_type': None,
            'data_size': None,
            'response_time': 10.0
        }
    except Exception as e:
        return {
            'endpoint': endpoint['path'],
            'description': endpoint['description'],
            'status': f"💥 ERROR: {str(e)[:50]}",
            'status_code': None,
            'data_type': None,
            'data_size': None,
            'response_time': None
        }

def main():
    """Función principal para verificar todos los endpoints"""
    print("🔍 Verificando endpoints de Immermex Dashboard API")
    print("=" * 60)
    print(f"🌐 URL Base: {BASE_URL}")
    print(f"📅 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    for i, endpoint in enumerate(ENDPOINTS, 1):
        print(f"[{i:2d}/{len(ENDPOINTS)}] Probando {endpoint['path']}...", end=" ")
        
        result = test_endpoint(endpoint)
        results.append(result)
        
        print(f"{result['status']}")
        
        # Pequeña pausa entre requests
        time.sleep(0.5)
    
    print()
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    # Contar resultados
    ok_count = sum(1 for r in results if "✅ OK" in r['status'])
    error_count = sum(1 for r in results if "❌ ERROR" in r['status'])
    timeout_count = sum(1 for r in results if "⏰ TIMEOUT" in r['status'])
    other_error_count = sum(1 for r in results if "💥 ERROR" in r['status'])
    
    print(f"✅ Exitosos: {ok_count}")
    print(f"❌ Errores HTTP: {error_count}")
    print(f"⏰ Timeouts: {timeout_count}")
    print(f"💥 Otros errores: {other_error_count}")
    print(f"📈 Total: {len(results)}")
    print()
    
    # Mostrar detalles de errores
    errors = [r for r in results if "❌ ERROR" in r['status'] or "⏰ TIMEOUT" in r['status'] or "💥 ERROR" in r['status']]
    
    if errors:
        print("🚨 ENDPOINTS CON PROBLEMAS:")
        print("-" * 40)
        for error in errors:
            print(f"  {error['endpoint']} - {error['description']}")
            print(f"    Estado: {error['status']}")
            if error['status_code']:
                print(f"    Código: {error['status_code']}")
            print()
    else:
        print("🎉 ¡Todos los endpoints están funcionando correctamente!")
    
    print()
    print("📋 TABLA DETALLADA:")
    print("-" * 80)
    print(f"{'Endpoint':<35} {'Estado':<15} {'Tipo':<10} {'Tamaño':<8} {'Tiempo':<8}")
    print("-" * 80)
    
    for result in results:
        endpoint_short = result['endpoint'][:34]
        status_short = result['status'][:14]
        data_type_short = str(result['data_type'])[:9] if result['data_type'] else "N/A"
        data_size_str = str(result['data_size'])[:7] if result['data_size'] else "N/A"
        response_time_str = f"{result['response_time']:.2f}s" if result['response_time'] else "N/A"
        
        print(f"{endpoint_short:<35} {status_short:<15} {data_type_short:<10} {data_size_str:<8} {response_time_str:<8}")

if __name__ == "__main__":
    main()
