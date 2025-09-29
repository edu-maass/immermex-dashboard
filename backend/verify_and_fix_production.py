#!/usr/bin/env python3
"""
Script completo para verificar y corregir días de crédito en producción
Ejecutar con: python verify_and_fix_production.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# URL de la base de datos de producción
PRODUCTION_DATABASE_URL = "postgresql://postgres.ldxahcawfrvlmdiwapli:Database_Immermex@aws-1-us-west-1.pooler.supabase.com:6543/postgres"

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        engine = create_engine(
            PRODUCTION_DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={"sslmode": "require"}
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                print("✅ Conexión a producción exitosa")
                return engine
            else:
                print("❌ Error en la prueba de conexión")
                return None
                
    except Exception as e:
        print(f"❌ Error conectando a producción: {str(e)}")
        return None

def verify_credit_days(engine):
    """Verifica la congruencia de días de crédito"""
    
    try:
        with engine.connect() as conn:
            # Verificar tablas
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('pedidos', 'facturacion')
            ORDER BY table_name;
            """
            
            result = conn.execute(text(tables_query))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n📊 Tablas encontradas: {tables}")
            
            if 'pedidos' not in tables or 'facturacion' not in tables:
                print("❌ No se encontraron las tablas necesarias")
                return False
            
            # Contar registros
            pedidos_count = conn.execute(text("SELECT COUNT(*) FROM pedidos")).fetchone()[0]
            facturas_count = conn.execute(text("SELECT COUNT(*) FROM facturacion")).fetchone()[0]
            
            print(f"📈 Registros en producción:")
            print(f"   Pedidos: {pedidos_count:,}")
            print(f"   Facturas: {facturas_count:,}")
            
            if pedidos_count == 0 or facturas_count == 0:
                print("⚠️  No hay datos en las tablas")
                return True
            
            # Verificar discrepancias
            discrepancies_query = """
            SELECT 
                COUNT(*) as total_relaciones,
                SUM(CASE WHEN p.dias_credito = f.dias_credito THEN 1 ELSE 0 END) as coincidencias,
                SUM(CASE WHEN p.dias_credito != f.dias_credito THEN 1 ELSE 0 END) as discrepancias
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            """
            
            result = conn.execute(text(discrepancies_query))
            total_relaciones, coincidencias, discrepancias = result.fetchone()
            
            print(f"\n🔍 VERIFICACIÓN DE DÍAS DE CRÉDITO:")
            print("="*60)
            print(f"Total de relaciones pedido-factura: {total_relaciones:,}")
            print(f"Coincidencias: {coincidencias:,}")
            print(f"Discrepancias: {discrepancias:,}")
            
            if total_relaciones > 0:
                porcentaje = (coincidencias / total_relaciones) * 100
                print(f"Porcentaje de coincidencia: {porcentaje:.2f}%")
            
            if discrepancias > 0:
                print(f"\n⚠️  SE ENCONTRARON {discrepancias} DISCREPANCIAS")
                
                # Mostrar algunas discrepancias de ejemplo
                examples_query = """
                SELECT 
                    p.id as pedido_id,
                    p.folio_factura,
                    p.dias_credito as dias_pedido,
                    f.dias_credito as dias_factura,
                    f.cliente
                FROM pedidos p
                INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
                WHERE p.dias_credito != f.dias_credito
                LIMIT 5
                """
                
                result = conn.execute(text(examples_query))
                examples = result.fetchall()
                
                print("\nEjemplos de discrepancias:")
                print("-"*50)
                for pedido_id, folio, dias_pedido, dias_factura, cliente in examples:
                    print(f"Pedido {pedido_id} ({folio}): Pedido={dias_pedido}, Factura={dias_factura}, Cliente={cliente}")
                
                return False
            else:
                print("\n✅ ¡PERFECTO! No hay discrepancias en los días de crédito")
                
                # Mostrar estadísticas de días de crédito
                stats_query = """
                SELECT 
                    dias_credito,
                    COUNT(*) as count
                FROM pedidos 
                GROUP BY dias_credito
                ORDER BY dias_credito;
                """
                
                result = conn.execute(text(stats_query))
                stats = result.fetchall()
                
                print(f"\n📈 DISTRIBUCIÓN DE DÍAS DE CRÉDITO:")
                print("-"*40)
                for dias, count in stats:
                    print(f"{dias or 0:>3} días: {count:>6,} registros")
                
                return True
                
    except Exception as e:
        logger.error(f"Error durante la verificación: {str(e)}")
        return False

def fix_discrepancies(engine):
    """Corrige las discrepancias encontradas"""
    
    try:
        with engine.connect() as conn:
            print(f"\n🔧 CORRIGIENDO DISCREPANCIAS...")
            
            # Contar discrepancias antes de corregir
            count_query = """
            SELECT COUNT(*) 
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            WHERE p.dias_credito != f.dias_credito
            """
            
            result = conn.execute(text(count_query))
            discrepancies_before = result.fetchone()[0]
            
            if discrepancies_before == 0:
                print("✅ No hay discrepancias que corregir")
                return True
            
            print(f"Discrepancias encontradas: {discrepancies_before}")
            
            # Aplicar correcciones
            fix_query = """
            UPDATE pedidos 
            SET dias_credito = f.dias_credito
            FROM facturacion f 
            WHERE pedidos.folio_factura = f.folio_factura 
            AND pedidos.dias_credito != f.dias_credito
            """
            
            result = conn.execute(text(fix_query))
            rows_updated = result.rowcount
            
            # Confirmar cambios
            conn.commit()
            
            print(f"✅ Se corrigieron {rows_updated} registros")
            
            # Verificar que las correcciones funcionaron
            result = conn.execute(text(count_query))
            discrepancies_after = result.fetchone()[0]
            
            if discrepancies_after == 0:
                print("✅ Todas las discrepancias han sido corregidas")
                return True
            else:
                print(f"⚠️  Aún quedan {discrepancies_after} discrepancias")
                return False
                
    except Exception as e:
        logger.error(f"Error corrigiendo discrepancias: {str(e)}")
        return False

def main():
    """Función principal"""
    
    print("🔍 VERIFICACIÓN Y CORRECCIÓN DE DÍAS DE CRÉDITO - PRODUCCIÓN")
    print("=" * 70)
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Probar conexión
    engine = test_connection()
    if not engine:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    # Verificar días de crédito
    is_consistent = verify_credit_days(engine)
    
    if not is_consistent:
        # Preguntar si quiere corregir
        print(f"\n¿Quieres corregir las discrepancias automáticamente?")
        respuesta = input("Escribe 'SI' para confirmar: ").strip()
        
        if respuesta == 'SI':
            success = fix_discrepancies(engine)
            
            if success:
                print(f"\n✅ Corrección completada exitosamente")
                # Verificar nuevamente
                print(f"\n🔍 Verificación post-corrección:")
                verify_credit_days(engine)
            else:
                print(f"\n❌ Error durante la corrección")
        else:
            print(f"\nℹ️  Corrección cancelada")
    else:
        print(f"\n✅ Los datos están congruentes, no se requiere corrección")
    
    print(f"\nLog guardado en: production_verification.log")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Operación cancelada por el usuario")
    except Exception as e:
        logger.error(f"Error en el script principal: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
