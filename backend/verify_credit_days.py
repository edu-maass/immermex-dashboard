#!/usr/bin/env python3
"""
Script para verificar que la columna de días de crédito en la tabla de pedidos
coincida con la columna de días de crédito de la factura relacionada.

Este script:
1. Conecta a la base de datos
2. Busca pedidos que tienen facturas relacionadas
3. Compara los días de crédito entre ambas tablas
4. Reporta cualquier discrepancia encontrada
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
        logging.FileHandler('credit_days_verification.log'),
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

def verify_credit_days_consistency():
    """Verifica la consistencia de días de crédito entre pedidos y facturas"""
    
    engine = get_database_connection()
    
    # Query para encontrar discrepancias
    query = """
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
    ORDER BY p.folio_factura, p.id;
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            
            if not rows:
                logger.warning("No se encontraron pedidos con facturas relacionadas")
                return
            
            logger.info(f"Verificando {len(rows)} registros de pedidos con facturas relacionadas...")
            
            # Contadores para estadísticas
            total_registros = len(rows)
            coincidencias = 0
            discrepancias = 0
            discrepancias_detalle = []
            
            print("\n" + "="*100)
            print("VERIFICACIÓN DE DÍAS DE CRÉDITO - PEDIDOS vs FACTURAS")
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
            print(f"\nRESUMEN DE VERIFICACIÓN:")
            print(f"Total de registros verificados: {total_registros}")
            print(f"Coincidencias: {coincidencias}")
            print(f"Discrepancias: {discrepancias}")
            print(f"Porcentaje de coincidencia: {(coincidencias/total_registros)*100:.2f}%")
            
            if discrepancias > 0:
                print(f"\n⚠️  SE ENCONTRARON {discrepancias} DISCREPANCIAS:")
                print("="*80)
                for disc in discrepancias_detalle:
                    print(f"Pedido ID: {disc['pedido_id']}")
                    print(f"  Folio: {disc['folio']}")
                    print(f"  Cliente: {disc['cliente']}")
                    print(f"  Días crédito Pedido: {disc['dias_pedido']}")
                    print(f"  Días crédito Factura: {disc['dias_factura']}")
                    print(f"  Fecha Factura: {disc['fecha_factura']}")
                    print("-"*40)
                
                # Generar query para corregir discrepancias (opcional)
                print(f"\n🔧 QUERY PARA CORREGIR DISCREPANCIAS:")
                print("-- Ejecutar solo si se desea corregir automáticamente")
                print("-- ADVERTENCIA: Esta operación modificará datos existentes")
                print("""
UPDATE pedidos 
SET dias_credito = f.dias_credito
FROM facturacion f 
WHERE pedidos.folio_factura = f.folio_factura 
AND pedidos.dias_credito != f.dias_credito;
                """)
            else:
                print("\n✅ ¡PERFECTO! No se encontraron discrepancias en los días de crédito.")
            
            logger.info(f"Verificación completada: {coincidencias} coincidencias, {discrepancias} discrepancias")
            
    except Exception as e:
        logger.error(f"Error durante la verificación: {str(e)}")
        raise

def get_credit_days_statistics():
    """Obtiene estadísticas generales de días de crédito"""
    
    engine = get_database_connection()
    
    queries = {
        "Pedidos": "SELECT dias_credito, COUNT(*) as count FROM pedidos GROUP BY dias_credito ORDER BY dias_credito",
        "Facturas": "SELECT dias_credito, COUNT(*) as count FROM facturacion GROUP BY dias_credito ORDER BY dias_credito"
    }
    
    print("\n" + "="*60)
    print("ESTADÍSTICAS DE DÍAS DE CRÉDITO")
    print("="*60)
    
    try:
        with engine.connect() as conn:
            for tabla, query in queries.items():
                print(f"\n{tabla}:")
                print("-"*30)
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                if rows:
                    for dias, count in rows:
                        print(f"  {dias or 0} días: {count} registros")
                else:
                    print("  No hay datos")
                    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")

if __name__ == "__main__":
    try:
        print("Iniciando verificación de días de crédito...")
        print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verificar consistencia
        verify_credit_days_consistency()
        
        # Mostrar estadísticas
        get_credit_days_statistics()
        
        print(f"\nVerificación completada exitosamente.")
        print(f"Log guardado en: credit_days_verification.log")
        
    except Exception as e:
        logger.error(f"Error en el script principal: {str(e)}")
        sys.exit(1)
