#!/usr/bin/env python3
"""
Script para corregir discrepancias en días de crédito entre pedidos y facturas.
Este script sincroniza los días de crédito de los pedidos con los de las facturas relacionadas.
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
        logging.FileHandler('fix_credit_days.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Obtiene la conexión a la base de datos"""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
    
    if DATABASE_URL.startswith("postgresql://"):
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={"sslmode": "require"}
        )
        logger.info("Conectando a Supabase/PostgreSQL")
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        logger.info("Conectando a SQLite local")
    
    return engine

def fix_credit_days_discrepancies(dry_run=True):
    """
    Corrige las discrepancias en días de crédito entre pedidos y facturas.
    
    Args:
        dry_run (bool): Si es True, solo muestra qué se corregiría sin hacer cambios
    """
    
    engine = get_database_connection()
    
    try:
        with engine.connect() as conn:
            # Primero, identificar todas las discrepancias
            query_discrepancies = """
            SELECT 
                p.id as pedido_id,
                p.folio_factura,
                p.pedido,
                p.dias_credito as dias_credito_pedido,
                f.id as factura_id,
                f.dias_credito as dias_credito_factura,
                f.cliente,
                f.fecha_factura
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            WHERE p.dias_credito != f.dias_credito
            ORDER BY p.folio_factura, p.id;
            """
            
            result = conn.execute(text(query_discrepancies))
            discrepancies = result.fetchall()
            
            if not discrepancies:
                print("✅ No se encontraron discrepancias en días de crédito.")
                return True
            
            print(f"\n🔍 Se encontraron {len(discrepancies)} discrepancias:")
            print("="*80)
            print(f"{'Pedido ID':<10} {'Folio':<15} {'Cliente':<25} {'Pedido':<8} {'Factura':<8} {'Acción':<15}")
            print("-"*80)
            
            corrections_needed = []
            
            for row in discrepancies:
                pedido_id, folio, pedido, dias_pedido, factura_id, dias_factura, cliente, fecha_factura = row
                
                # Truncar cliente si es muy largo
                cliente_display = cliente[:22] + "..." if cliente and len(cliente) > 25 else cliente or "N/A"
                
                # Decidir qué valor usar como correcto
                # Prioridad: usar el valor de la factura como fuente de verdad
                correct_value = dias_factura
                action = f"Pedido → {correct_value}"
                
                print(f"{pedido_id:<10} {folio or 'N/A':<15} {cliente_display:<25} {dias_pedido or 0:<8} {dias_factura or 0:<8} {action:<15}")
                
                corrections_needed.append({
                    'pedido_id': pedido_id,
                    'folio': folio,
                    'correct_value': correct_value,
                    'current_value': dias_pedido
                })
            
            print("-"*80)
            
            if dry_run:
                print(f"\n🔍 MODO DRY RUN - No se realizaron cambios")
                print(f"Se corregirían {len(corrections_needed)} registros")
                print("\nPara aplicar las correcciones, ejecuta:")
                print("python fix_credit_days.py --apply")
                return True
            
            # Aplicar correcciones
            print(f"\n🔧 Aplicando correcciones...")
            
            corrections_applied = 0
            
            for correction in corrections_needed:
                update_query = """
                UPDATE pedidos 
                SET dias_credito = :correct_value, updated_at = CURRENT_TIMESTAMP
                WHERE id = :pedido_id
                """
                
                result = conn.execute(text(update_query), {
                    'correct_value': correction['correct_value'],
                    'pedido_id': correction['pedido_id']
                })
                
                if result.rowcount > 0:
                    corrections_applied += 1
                    logger.info(f"Corregido pedido {correction['pedido_id']}: {correction['current_value']} → {correction['correct_value']}")
            
            # Confirmar cambios
            conn.commit()
            
            print(f"✅ Se aplicaron {corrections_applied} correcciones exitosamente")
            
            # Verificar que las correcciones funcionaron
            verification_query = """
            SELECT COUNT(*) as remaining_discrepancies
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            WHERE p.dias_credito != f.dias_credito
            """
            
            result = conn.execute(text(verification_query))
            remaining = result.fetchone()[0]
            
            if remaining == 0:
                print("✅ Todas las discrepancias han sido corregidas")
            else:
                print(f"⚠️  Aún quedan {remaining} discrepancias")
            
            return True
            
    except Exception as e:
        logger.error(f"Error durante la corrección: {str(e)}")
        return False

def verify_corrections():
    """Verifica que las correcciones se aplicaron correctamente"""
    
    engine = get_database_connection()
    
    try:
        with engine.connect() as conn:
            # Contar discrepancias restantes
            query = """
            SELECT COUNT(*) as total_discrepancies
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            WHERE p.dias_credito != f.dias_credito
            """
            
            result = conn.execute(text(query))
            total_discrepancies = result.fetchone()[0]
            
            # Contar total de relaciones
            query_total = """
            SELECT COUNT(*) as total_relations
            FROM pedidos p
            INNER JOIN facturacion f ON p.folio_factura = f.folio_factura
            """
            
            result = conn.execute(text(query_total))
            total_relations = result.fetchone()[0]
            
            print(f"\n📊 VERIFICACIÓN POST-CORRECCIÓN:")
            print(f"Total de relaciones pedido-factura: {total_relations}")
            print(f"Discrepancias restantes: {total_discrepancies}")
            
            if total_discrepancies == 0:
                print("✅ ¡Perfecto! No hay discrepancias restantes")
            else:
                print(f"⚠️  Aún hay {total_discrepancies} discrepancias")
                
                # Mostrar las discrepancias restantes
                query_remaining = """
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
                
                result = conn.execute(text(query_remaining))
                remaining = result.fetchall()
                
                print("\nDiscrepancias restantes (primeras 5):")
                for row in remaining:
                    pedido_id, folio, dias_pedido, dias_factura, cliente = row
                    print(f"  Pedido {pedido_id} ({folio}): Pedido={dias_pedido}, Factura={dias_factura}, Cliente={cliente}")
            
            return total_discrepancies == 0
            
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Script de Corrección de Días de Crédito")
    print("=" * 50)
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar argumentos
    apply_changes = "--apply" in sys.argv
    
    if apply_changes:
        print("⚠️  MODO APLICAR CAMBIOS - Se modificarán datos existentes")
        confirm = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
        if confirm != 'SI':
            print("❌ Operación cancelada")
            sys.exit(0)
    else:
        print("🔍 MODO DRY RUN - Solo se mostrarán los cambios propuestos")
    
    try:
        # Ejecutar corrección
        success = fix_credit_days_discrepancies(dry_run=not apply_changes)
        
        if success and apply_changes:
            # Verificar correcciones
            verify_corrections()
        
        print(f"\n{'✅ Corrección completada exitosamente' if success else '❌ Error en la corrección'}")
        print(f"Log guardado en: fix_credit_days.log")
        
    except Exception as e:
        logger.error(f"Error en el script principal: {str(e)}")
        sys.exit(1)
