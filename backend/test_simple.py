#!/usr/bin/env python3
"""
Script de prueba simple para verificar el sistema
"""

import sys
import os

def test_imports():
    """Prueba las importaciones básicas"""
    print("🔍 Probando importaciones...")
    
    try:
        # Probar importaciones del backend
        from database import init_db, get_db
        print("✅ database.py - OK")
        
        from models import KPIsResponse
        print("✅ models.py - OK")
        
        from services import DashboardService
        print("✅ services.py - OK")
        
        from data_processor import ImmermexDataProcessor
        print("✅ data_processor.py - OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_database():
    """Prueba la inicialización de la base de datos"""
    print("\n🔍 Probando base de datos...")
    
    try:
        from database import init_db
        init_db()
        print("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def test_data_processor():
    """Prueba el procesador de datos con archivos CSV"""
    print("\n🔍 Probando procesador de datos...")
    
    try:
        from data_processor import ImmermexDataProcessor
        processor = ImmermexDataProcessor()
        
        # Simular datos de prueba
        import pandas as pd
        
        # Leer archivos CSV
        facturacion_df = pd.read_csv('facturacion.csv')
        cobranza_df = pd.read_csv('cobranza.csv')
        cfdi_df = pd.read_csv('cfdi_relacionados.csv')
        inventario_df = pd.read_csv('inventario.csv')
        
        # Procesar datos
        facturacion_clean = processor.normalize_facturacion(facturacion_df)
        cobranza_clean = processor.normalize_cobranza(cobranza_df)
        cfdi_clean = processor.normalize_cfdi_relacionados(cfdi_df)
        inventario_clean = processor.normalize_inventario(inventario_df)
        
        # Crear DataFrame maestro
        master_df = processor.create_master_dataframe()
        
        # Calcular KPIs
        kpis = processor.calculate_kpis()
        
        print(f"✅ Datos procesados: {len(master_df)} registros")
        print(f"✅ KPIs calculados: {len(kpis)} métricas")
        print(f"   - Facturación total: ${kpis['facturacion_total']:,.2f}")
        print(f"   - Cobranza total: ${kpis['cobranza_total']:,.2f}")
        print(f"   - % Cobrado: {kpis['porcentaje_cobrado']}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error procesando datos: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 PRUEBAS DEL SISTEMA IMMERMEX DASHBOARD")
    print("=" * 50)
    
    tests = [
        ("Importaciones", test_imports),
        ("Base de datos", test_database),
        ("Procesador de datos", test_data_processor),
    ]
    
    results = []
    for test_name, test_func in tests:
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
        print("\n💡 Para ejecutar el servidor:")
        print("   python run.py")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
