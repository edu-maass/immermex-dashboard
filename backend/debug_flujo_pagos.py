import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")

if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///./immermex.db"

POSTGRES_URL = os.getenv("POSTGRES_URL", "")
if POSTGRES_URL and POSTGRES_URL.startswith("postgresql://"):
    DATABASE_URL = POSTGRES_URL
    logger.info("Usando URL PostgreSQL directa de POSTGRES_URL")
elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_PASSWORD"):
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_PASSWORD")
        
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
            DATABASE_URL = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
            logger.info(f"Construida URL PostgreSQL desde Supabase pooler: aws-1-us-west-1.pooler.supabase.com")
        else:
            logger.warning("URL de Supabase no reconocida, usando SQLite por defecto.")
    except Exception as e:
        logger.error(f"Error al construir URL de Supabase: {e}, usando SQLite por defecto.")
        DATABASE_URL = "sqlite:///./immermex.db"
else:
    logger.info("No se encontraron variables de entorno para Supabase o PostgreSQL, usando SQLite por defecto.")

logger.info(f"Conectando a la base de datos: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_flujo_pagos():
    """Diagnostica los datos del flujo de pagos para entender los montos"""
    db = SessionLocal()
    try:
        with engine.connect() as connection:
            logger.info("============================================================")
            logger.info("DIAGNÓSTICO DE FLUJO DE PAGOS SEMANAL")
            logger.info("============================================================")
            
            # 1. Verificar estructura de la tabla compras_v2
            logger.info("1. ESTRUCTURA DE LA TABLA compras_v2:")
            structure_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'compras_v2'
                ORDER BY ordinal_position
            """)
            
            try:
                structure_result = connection.execute(structure_query).fetchall()
                for row in structure_result:
                    logger.info(f"  {row.column_name}: {row.data_type} ({'NULL' if row.is_nullable == 'YES' else 'NOT NULL'})")
            except Exception as e:
                logger.warning(f"No se pudo obtener estructura: {e}")
            
            # 2. Verificar datos de ejemplo
            logger.info("\n2. DATOS DE EJEMPLO (primeros 5 registros):")
            sample_query = text("""
                SELECT 
                    imi,
                    proveedor,
                    fecha_pedido,
                    fecha_vencimiento,
                    fecha_pago_factura,
                    moneda,
                    tipo_cambio_real,
                    tipo_cambio_estimado,
                    total_con_iva_mxn,
                    total_con_iva_divisa,
                    gastos_importacion_mxn,
                    gastos_importacion_divisa,
                    anticipo_monto,
                    anticipo_pct
                FROM compras_v2 
                WHERE fecha_pedido IS NOT NULL
                LIMIT 5
            """)
            
            sample_result = connection.execute(sample_query).fetchall()
            for row in sample_result:
                logger.info(f"  IMI: {row.imi}")
                logger.info(f"    Proveedor: {row.proveedor}")
                logger.info(f"    Fecha Pedido: {row.fecha_pedido}")
                logger.info(f"    Fecha Vencimiento: {row.fecha_vencimiento}")
                logger.info(f"    Moneda: {row.moneda}")
                logger.info(f"    Tipo Cambio Real: {row.tipo_cambio_real}")
                logger.info(f"    Tipo Cambio Estimado: {row.tipo_cambio_estimado}")
                logger.info(f"    Total con IVA MXN: {row.total_con_iva_mxn}")
                logger.info(f"    Total con IVA Divisa: {row.total_con_iva_divisa}")
                logger.info(f"    Gastos Importación MXN: {row.gastos_importacion_mxn}")
                logger.info(f"    Gastos Importación Divisa: {row.gastos_importacion_divisa}")
                logger.info(f"    Anticipo Monto: {row.anticipo_monto}")
                logger.info(f"    Anticipo %: {row.anticipo_pct}")
                logger.info("    ---")
            
            # 3. Calcular montos para diferentes monedas
            logger.info("\n3. CÁLCULOS DE MONTO POR MONEDA (USD y MXN):")
            calculation_query = text("""
                SELECT 
                    imi,
                    moneda,
                    total_con_iva_mxn,
                    total_con_iva_divisa,
                    gastos_importacion_mxn,
                    gastos_importacion_divisa,
                    anticipo_monto,
                    tipo_cambio_real,
                    tipo_cambio_estimado,
                    -- Liquidaciones en MXN
                    (total_con_iva_mxn - COALESCE(anticipo_monto, 0)) as liquidaciones_mxn,
                    -- Liquidaciones en USD (si moneda es USD)
                    CASE 
                        WHEN moneda = 'USD' THEN (total_con_iva_divisa - COALESCE(anticipo_monto, 0)) * COALESCE(tipo_cambio_real, tipo_cambio_estimado, 1.0)
                        WHEN tipo_cambio_real > 0 THEN (total_con_iva_mxn - COALESCE(anticipo_monto, 0)) / tipo_cambio_real
                        ELSE 0
                    END as liquidaciones_usd,
                    -- Gastos de importación en MXN
                    gastos_importacion_mxn as gastos_mxn,
                    -- Gastos de importación en USD
                    CASE 
                        WHEN moneda = 'USD' THEN gastos_importacion_divisa * COALESCE(tipo_cambio_real, tipo_cambio_estimado, 1.0)
                        WHEN tipo_cambio_real > 0 THEN gastos_importacion_mxn / tipo_cambio_real
                        ELSE 0
                    END as gastos_usd
                FROM compras_v2 
                WHERE fecha_pedido IS NOT NULL
                LIMIT 10
            """)
            
            calc_result = connection.execute(calculation_query).fetchall()
            for row in calc_result:
                logger.info(f"  IMI: {row.imi} ({row.moneda})")
                logger.info(f"    Liquidaciones MXN: ${row.liquidaciones_mxn:,.2f}")
                logger.info(f"    Liquidaciones USD: ${row.liquidaciones_usd:,.2f}")
                logger.info(f"    Gastos MXN: ${row.gastos_mxn:,.2f}")
                logger.info(f"    Gastos USD: ${row.gastos_usd:,.2f}")
                logger.info("    ---")
            
            # 4. Verificar fechas y semanas
            logger.info("\n4. ANÁLISIS DE FECHAS Y SEMANAS:")
            date_query = text("""
                SELECT 
                    COUNT(*) as total_registros,
                    MIN(fecha_pedido) as fecha_min,
                    MAX(fecha_pedido) as fecha_max,
                    COUNT(CASE WHEN fecha_vencimiento IS NOT NULL THEN 1 END) as con_fecha_vencimiento,
                    COUNT(CASE WHEN fecha_pago_factura IS NOT NULL THEN 1 END) as con_fecha_pago,
                    COUNT(CASE WHEN fecha_arribo_real IS NOT NULL THEN 1 END) as con_fecha_arribo_real,
                    COUNT(CASE WHEN fecha_arribo_estimada IS NOT NULL THEN 1 END) as con_fecha_arribo_estimada
                FROM compras_v2 
                WHERE fecha_pedido IS NOT NULL
            """)
            
            date_result = connection.execute(date_query).fetchone()
            logger.info(f"  Total registros: {date_result.total_registros}")
            logger.info(f"  Fecha mínima: {date_result.fecha_min}")
            logger.info(f"  Fecha máxima: {date_result.fecha_max}")
            logger.info(f"  Con fecha vencimiento: {date_result.con_fecha_vencimiento}")
            logger.info(f"  Con fecha pago: {date_result.con_fecha_pago}")
            logger.info(f"  Con fecha arribo real: {date_result.con_fecha_arribo_real}")
            logger.info(f"  Con fecha arribo estimada: {date_result.con_fecha_arribo_estimada}")
            
            # 5. Verificar montos totales
            logger.info("\n5. MONTOS TOTALES:")
            totals_query = text("""
                SELECT 
                    SUM(total_con_iva_mxn) as total_mxn,
                    SUM(total_con_iva_divisa) as total_divisa,
                    SUM(gastos_importacion_mxn) as gastos_mxn,
                    SUM(gastos_importacion_divisa) as gastos_divisa,
                    SUM(anticipo_monto) as total_anticipo,
                    AVG(tipo_cambio_real) as avg_tipo_cambio_real,
                    AVG(tipo_cambio_estimado) as avg_tipo_cambio_estimado
                FROM compras_v2 
                WHERE fecha_pedido IS NOT NULL
            """)
            
            totals_result = connection.execute(totals_query).fetchone()
            logger.info(f"  Total MXN: ${totals_result.total_mxn:,.2f}")
            logger.info(f"  Total Divisa: ${totals_result.total_divisa:,.2f}")
            logger.info(f"  Gastos MXN: ${totals_result.gastos_mxn:,.2f}")
            logger.info(f"  Gastos Divisa: ${totals_result.gastos_divisa:,.2f}")
            logger.info(f"  Total Anticipo: ${totals_result.total_anticipo:,.2f}")
            logger.info(f"  Promedio Tipo Cambio Real: {totals_result.avg_tipo_cambio_real:,.4f}")
            logger.info(f"  Promedio Tipo Cambio Estimado: {totals_result.avg_tipo_cambio_estimado:,.4f}")
            
            logger.info("============================================================")
            logger.info("DIAGNÓSTICO COMPLETADO")
            logger.info("============================================================")
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Error durante diagnóstico: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = debug_flujo_pagos()
    sys.exit(0 if success else 1)
