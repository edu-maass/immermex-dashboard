#!/usr/bin/env python3
"""
Script para hacer deployment y pruebas en producción
"""

import os
import sys
import requests
import json
import io
import pandas as pd
from datetime import datetime

def setup_environment():
    """Configura el entorno para producción"""
    print("=== Configurando Entorno de Producción ===")
    
    # Verificar variables de entorno
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        print("Configura la variable de entorno con la URL de Supabase:")
        print("export DATABASE_URL='postgresql://usuario:password@host:puerto/database'")
        return False
    
    print(f"✅ DATABASE_URL configurada: {database_url[:50]}...")
    
    # Verificar otras variables necesarias
    environment = os.getenv("ENVIRONMENT", "development")
    print(f"✅ ENVIRONMENT: {environment}")
    
    return True

def create_test_compras_excel():
    """Crea un archivo Excel de prueba para compras"""
    sample_data = {
        'IMI': ['IMI001', 'IMI002', 'IMI003', 'IMI004', 'IMI005'],
        'Proveedor': ['Proveedor A', 'Proveedor B', 'Proveedor C', 'Proveedor D', 'Proveedor E'],
        'Material': ['Material 1', 'Material 2', 'Material 3', 'Material 4', 'Material 5'],
        'fac prov': ['FAC001', 'FAC002', 'FAC003', 'FAC004', 'FAC005'],
        'Kilogramos': [100.0, 200.0, 150.0, 300.0, 250.0],
        'PU': [10.50, 15.75, 12.25, 8.90, 11.40],
        'DIVISA': ['USD', 'USD', 'USD', 'USD', 'USD'],
        'Fecha Pedido': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'Puerto Origen': ['Puerto A', 'Puerto B', 'Puerto C', 'Puerto D', 'Puerto E'],
        'PRECIO DLLS': [1050.0, 3150.0, 1837.5, 2670.0, 2850.0],
        'XR': [17.5, 17.5, 17.5, 17.5, 17.5],
        'Dias Credito': [30, 45, 30, 60, 30],
        'COSTO TOTAL': [1050.0, 3150.0, 1837.5, 2670.0, 2850.0],
        'IVA': [0.0, 0.0, 0.0, 0.0, 0.0],
        'PRECIO MXN': [18375.0, 55125.0, 32156.25, 46725.0, 49875.0],
        'FECHA VENCIMIENTO FACTURA': ['2024-02-14', '2024-03-01', '2024-02-16', '2024-03-18', '2024-02-18'],
        'FECHA PAGO FACTURA': ['2024-02-10', None, None, '2024-03-15', None],
        'Pedimento': ['PED001', 'PED002', 'PED003', 'PED004', 'PED005'],
        'Gastos aduanales': [50.0, 100.0, 75.0, 120.0, 90.0],
        'Agente': ['Agente A', 'Agente B', 'Agente C', 'Agente D', 'Agente E'],
        'fac agente': ['FAC_AG001', 'FAC_AG002', 'FAC_AG003', 'FAC_AG004', 'FAC_AG005']
    }
    
    df = pd.DataFrame(sample_data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name="Resumen Compras")
    excel_buffer.seek(0)
    return excel_buffer.getvalue()

def test_production_endpoints(base_url):
    """Prueba los endpoints en producción"""
    print(f"\n=== Probando Endpoints en {base_url} ===")
    
    # Probar health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            print(f"   Data available: {data.get('data_available')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en health check: {str(e)}")
        return False
    
    # Probar endpoint de compras
    try:
        excel_content = create_test_compras_excel()
        files = {
            'file': ('test_compras_production.xlsx', excel_content, 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        params = {'reemplazar_datos': True}
        
        print("📤 Enviando archivo de compras a producción...")
        response = requests.post(f"{base_url}/api/upload/compras", 
                               files=files, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload de compras exitoso!")
            print(f"   Archivo ID: {data.get('archivo_id')}")
            print(f"   Total registros: {data.get('total_registros')}")
            print(f"   KPIs: {data.get('kpis_compras')}")
            
            # Verificar que los datos se guardaron
            if data.get('total_registros', 0) > 0:
                print("✅ Datos guardados correctamente en la base de datos")
                return True
            else:
                print("❌ No se guardaron datos en la base de datos")
                return False
        else:
            print(f"❌ Upload de compras falló: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en upload de compras: {str(e)}")
        return False

def test_kpis_endpoint(base_url):
    """Prueba el endpoint de KPIs"""
    try:
        print("📊 Probando endpoint de KPIs...")
        response = requests.get(f"{base_url}/api/kpis", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ KPIs obtenidos exitosamente")
            print(f"   Total facturación: {data.get('facturacion_total', 'N/A')}")
            print(f"   Total cobranza: {data.get('cobranza_total', 'N/A')}")
            print(f"   Compras totales: {data.get('total_compras', 'N/A')}")
            return True
        else:
            print(f"❌ Error obteniendo KPIs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en KPIs: {str(e)}")
        return False

def main():
    print("🚀 === Deployment y Pruebas en Producción ===")
    
    # Configurar entorno
    if not setup_environment():
        return
    
    # URLs de producción (ajustar según tu configuración)
    production_urls = [
        "https://immermex-dashboard.vercel.app",  # Si está en Vercel
        "https://immermex-api.herokuapp.com",     # Si está en Heroku
        "https://api.immermex.com",               # Si tienes dominio personalizado
    ]
    
    # Probar cada URL
    for base_url in production_urls:
        print(f"\n🌐 Probando: {base_url}")
        try:
            # Probar endpoints
            if test_production_endpoints(base_url):
                print(f"✅ {base_url} - Todas las pruebas pasaron")
                
                # Probar KPIs
                test_kpis_endpoint(base_url)
                
                print(f"\n🎉 Deployment exitoso en {base_url}")
                print("Los datos de compras se están procesando y guardando correctamente en Supabase")
                return
            else:
                print(f"❌ {base_url} - Pruebas fallaron")
        except Exception as e:
            print(f"❌ {base_url} - Error: {str(e)}")
    
    print("\n❌ No se pudo conectar a ningún endpoint de producción")
    print("Verifica que el servidor esté desplegado y funcionando")

if __name__ == "__main__":
    main()
