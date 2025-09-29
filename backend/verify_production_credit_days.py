#!/usr/bin/env python3
"""
Script para verificar días de crédito en la base de datos de producción
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_credit_days_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_production_database_connection():
    """Obtiene la conexión a la base de datos de producción"""
    
    # Intentar obtener DATABASE_URL del entorno
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        # Intentar cargar desde production.env
        try:
            from dotenv import load_dotenv
            load_dotenv('production.env')
            DATABASE_URL = os.getenv("DATABASE_URL")
        except ImportError:
            print("❌ python-dotenv no está instalado. Instálalo con: pip install python-dotenv")
        except Exception as e:
            print(f"❌ Error cargando production.env: {str(e)}")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL no está configurada")
        print("💡 Opciones:")
        print("   1. Configurar variable de entorno: set DATABASE_URL=postgresql://...")
        print("   2. Instalar python-dotenv: pip install python-dotenv")
        print("   3. Configurar la contraseña en production.env")
        return None
    
    if not DATABASE_URL.startswith("postgresql://"):
        print("❌ DATABASE_URL debe ser una URL de PostgreSQL")
        return None
    
    # Verificar que no tenga placeholder de contraseña
    if "[YOUR-PASSWORD]" in DATABASE_URL:
        print("❌ Debes configurar la contraseña real en production.env")
        print("   Reemplaza [YOUR-PASSWORD] con tu contraseña de Supabase")
        return None
    
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={"sslmode": "require"}
        )
        logger.info("✅ Conectando a base de datos de producción (Supabase/PostgreSQL)")
        return engine
    except Exception as e:
        logger.error(f"❌ Error conectando a producción: {str(e)}")
        return None

def verify_production_credit_days():
    """Verifica la congruencia de días de crédito en producción"""
    
    engine = get_production_database_connection()
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            # Verificar que las tablas existen
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
            
            # Contar registros totales
            pedidos_count = conn.execute(text("SELECT COUNT(*) FROM pedidos")).fetchone()[0]
            facturas_count = conn.execute(text("SELECT COUNT(*) FROM facturacion")).fetchone()[0]
            
            print(f"📈 Registros en producción:")
            print(f"   Pedidos: {pedidos_count:,}")
            print(f"   Facturas: {facturas_count:,}")
            
            if pedidos_count == 0 or facturas_count == 0:
                print("⚠️  No hay datos en las tablas de producción")
                return True
            
            # Verificar discrepancias
            discrepancies_query = """
            SELECT 
                p.id as pedido_id,
                p.folio_factura,
                p.pedido,
                p.dias_credito as dias_credito_pedido,
                f.id as factura_id,
                f.dias_credito as dias_credito_factura,
                f.cliente,
                f.fecha_factura,
                CASE 
                    WHEN p.dias_credito != f.dias_credito THEN 'DISCREPANCIA'
                    ELSE 'COINCIDE'
                END as estado
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            ORDER BY p.folio_factura, p.id
            LIMIT 50;
            """
            
            result = conn.execute(text(discrepancies_query))
            rows = result.fetchall()
            
            if not rows:
                print("⚠️  No se encontraron pedidos con facturas relacionadas")
                return True
            
            print(f"\n🔍 Verificando {len(rows)} relaciones pedido-factura...")
            
            # Contadores
            coincidencias = 0
            discrepancias = 0
            discrepancias_detalle = []
            
            print("\n" + "="*100)
            print("VERIFICACIÓN DE DÍAS DE CRÉDITO - PRODUCCIÓN")
            print("="*100)
            print(f"{'Pedido ID':<10} {'Folio':<15} {'Cliente':<25} {'Días Pedido':<12} {'Días Factura':<13} {'Estado':<12}")
            print("-"*100)
            
            for row in rows:
                pedido_id, folio, pedido, dias_pedido, factura_id, dias_factura, cliente, fecha_factura, estado = row
                
                # Truncar cliente si es muy largo
                cliente_display = cliente[:22] + "..." if cliente and len(cliente) > 25 else cliente or "N/A"
                
                print(f"{pedido_id:<10} {folio or 'N/A':<15} {cliente_display:<25} {dias_pedido or 0:<12} {dias_factura or 0:<13} {estado:<12}")
                
                if estado == 'COINCIDE':
                    coincidencias += 1
                else:
                    discrepancias += 1
                    discrepancias_detalle.append({
                        'pedido_id': pedido_id,
                        'folio': folio,
                        'cliente': cliente,
                        'dias_pedido': dias_pedido,
                        'dias_factura': dias_factura,
                        'fecha_factura': fecha_factura
                    })
            
            print("-"*100)
            print(f"\n📊 RESUMEN DE VERIFICACIÓN:")
            print(f"Total de relaciones verificadas: {len(rows)}")
            print(f"Coincidencias: {coincidencias}")
            print(f"Discrepancias: {discrepancias}")
            print(f"Porcentaje de coincidencia: {(coincidencias/len(rows))*100:.2f}%")
            
            if discrepancias > 0:
                print(f"\n⚠️  SE ENCONTRARON {discrepancias} DISCREPANCIAS:")
                print("="*80)
                for disc in discrepancias_detalle[:10]:  # Mostrar solo las primeras 10
                    print(f"Pedido ID: {disc['pedido_id']}")
                    print(f"  Folio: {disc['folio']}")
                    print(f"  Cliente: {disc['cliente']}")
                    print(f"  Días crédito Pedido: {disc['dias_pedido']}")
                    print(f"  Días crédito Factura: {disc['dias_factura']}")
                    print(f"  Fecha Factura: {disc['fecha_factura']}")
                    print("-"*40)
                
                if discrepancias > 10:
                    print(f"... y {discrepancias - 10} discrepancias más")
                
                # Estadísticas de días de crédito
                stats_query = """
                SELECT 
                    'Pedidos' as tabla,
                    dias_credito,
                    COUNT(*) as count
                FROM pedidos 
                GROUP BY dias_credito
                UNION ALL
                SELECT 
                    'Facturas' as tabla,
                    dias_credito,
                    COUNT(*) as count
                FROM facturacion 
                GROUP BY dias_credito
                ORDER BY tabla, dias_credito;
                """
                
                result = conn.execute(text(stats_query))
                stats = result.fetchall()
                
                print(f"\n📈 ESTADÍSTICAS DE DÍAS DE CRÉDITO:")
                print("-"*50)
                for tabla, dias, count in stats:
                    print(f"{tabla:<10} {dias or 0:>3} días: {count:>6,} registros")
                
                return False
            else:
                print("\n✅ ¡PERFECTO! No se encontraron discrepancias en los días de crédito.")
                
                # Estadísticas generales
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

if __name__ == "__main__":
    print("🔍 Verificación de Días de Crédito - PRODUCCIÓN")
    print("=" * 60)
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        success = verify_production_credit_days()
        
        if success:
            print(f"\n✅ Verificación completada exitosamente")
            print("Los días de crédito son congruentes entre pedidos y facturas")
        else:
            print(f"\n⚠️  Se encontraron discrepancias que requieren atención")
            print("Considera ejecutar el script de corrección si es necesario")
        
        print(f"\nLog guardado en: production_credit_days_verification.log")
        
    except Exception as e:
        logger.error(f"Error en el script principal: {str(e)}")
        sys.exit(1)
