import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
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
Base = declarative_base()

def update_compras_v2_calculated_columns():
    """Actualiza columnas calculadas en compras_v2"""
    try:
        with engine.connect() as connection:
            logger.info("[RUNNING] Actualizando columnas calculadas en compras_v2...")
            
            # 1. Actualizar gastos_importacion_mxn basado en gastos_importacion_divisa y tipo de cambio
            logger.info("  - Calculando gastos_importacion_mxn...")
            result1 = connection.execute(text("""
                UPDATE compras_v2 
                SET gastos_importacion_mxn = CASE 
                    WHEN moneda = 'USD' AND gastos_importacion_divisa > 0 THEN 
                        gastos_importacion_divisa * COALESCE(tipo_cambio_real, tipo_cambio_estimado, 1.0)
                    WHEN moneda = 'MXN' THEN gastos_importacion_divisa
                    ELSE gastos_importacion_mxn
                END
                WHERE gastos_importacion_divisa > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result1.rowcount} registros de gastos_importacion_mxn")
            
            # 2. Actualizar gastos_importacion_mxn basado en porcentaje_gastos_importacion cuando sea necesario
            logger.info("  - Calculando gastos_importacion_mxn por porcentaje...")
            result2 = connection.execute(text("""
                UPDATE compras_v2 
                SET gastos_importacion_mxn = CASE 
                    WHEN porcentaje_gastos_importacion > 0 AND gastos_importacion_mxn = 0 THEN
                        (SELECT SUM(c2m.costo_total_mxn) * (porcentaje_gastos_importacion / 100.0)
                         FROM compras_v2_materiales c2m 
                         WHERE c2m.compra_imi = compras_v2.imi)
                    ELSE gastos_importacion_mxn
                END
                WHERE porcentaje_gastos_importacion > 0 AND gastos_importacion_mxn = 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result2.rowcount} registros de gastos_importacion_mxn por porcentaje")
            
            # 3. Actualizar iva_monto_mxn (16% de los gastos de importación)
            logger.info("  - Calculando iva_monto_mxn...")
            result3 = connection.execute(text("""
                UPDATE compras_v2 
                SET iva_monto_mxn = COALESCE(gastos_importacion_mxn, 0) * 0.16
                WHERE gastos_importacion_mxn > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result3.rowcount} registros de iva_monto_mxn")
            
            # 4. Actualizar total_con_iva_mxn (suma de costos de materiales + gastos + IVA)
            logger.info("  - Calculando total_con_iva_mxn...")
            result4 = connection.execute(text("""
                UPDATE compras_v2 
                SET total_con_iva_mxn = (
                    SELECT COALESCE(SUM(c2m.costo_total_mxn), 0) 
                    FROM compras_v2_materiales c2m 
                    WHERE c2m.compra_imi = compras_v2.imi
                ) + COALESCE(gastos_importacion_mxn, 0) + iva_monto_mxn
            """))
            connection.commit()
            logger.info(f"    Actualizados {result4.rowcount} registros de total_con_iva_mxn")
            
            # 5. Actualizar anticipo_monto basado en anticipo_pct
            logger.info("  - Calculando anticipo_monto...")
            result5 = connection.execute(text("""
                UPDATE compras_v2 
                SET anticipo_monto = CASE 
                    WHEN anticipo_pct > 0 AND anticipo_monto = 0 THEN
                        total_con_iva_mxn * (anticipo_pct / 100.0)
                    ELSE anticipo_monto
                END
                WHERE anticipo_pct > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result5.rowcount} registros de anticipo_monto")
            
            # Actualizar timestamp
            connection.execute(text("""
                UPDATE compras_v2 
                SET updated_at = %s
                WHERE id IN (
                    SELECT DISTINCT c2.id 
                    FROM compras_v2 c2
                    JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
                )
            """), (datetime.utcnow(),))
            connection.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Error actualizando compras_v2: {str(e)}")
        return False

def update_compras_v2_materiales_calculated_columns():
    """Actualiza columnas calculadas en compras_v2_materiales"""
    try:
        with engine.connect() as connection:
            logger.info("[RUNNING] Actualizando columnas calculadas en compras_v2_materiales...")
            
            # 1. Actualizar pu_mxn basado en pu_divisa y tipo de cambio
            logger.info("  - Calculando pu_mxn...")
            result1 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET pu_mxn = CASE 
                    WHEN c2.moneda = 'USD' THEN 
                        compras_v2_materiales.pu_divisa * COALESCE(c2.tipo_cambio_real, c2.tipo_cambio_estimado, 1.0)
                    WHEN c2.moneda = 'MXN' THEN compras_v2_materiales.pu_divisa
                    ELSE compras_v2_materiales.pu_mxn
                END
                FROM compras_v2 c2
                WHERE compras_v2_materiales.compra_imi = c2.imi
            """))
            connection.commit()
            logger.info(f"    Actualizados {result1.rowcount} registros de pu_mxn")
            
            # 2. Actualizar pu_usd basado en moneda y tipo de cambio
            logger.info("  - Calculando pu_usd...")
            result2 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET pu_usd = CASE 
                    WHEN c2.moneda = 'USD' THEN compras_v2_materiales.pu_divisa
                    WHEN c2.moneda = 'MXN' THEN 
                        CASE 
                            WHEN c2.tipo_cambio_real IS NOT NULL AND c2.tipo_cambio_real > 0 
                            THEN compras_v2_materiales.pu_divisa / c2.tipo_cambio_real
                            WHEN c2.tipo_cambio_estimado IS NOT NULL AND c2.tipo_cambio_estimado > 0 
                            THEN compras_v2_materiales.pu_divisa / c2.tipo_cambio_estimado
                            ELSE compras_v2_materiales.pu_divisa
                        END
                    ELSE compras_v2_materiales.pu_divisa
                END
                FROM compras_v2 c2
                WHERE compras_v2_materiales.compra_imi = c2.imi
            """))
            connection.commit()
            logger.info(f"    Actualizados {result2.rowcount} registros de pu_usd")
            
            # 3. Actualizar costo_total_divisa (kg * pu_divisa)
            logger.info("  - Calculando costo_total_divisa...")
            result3 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET costo_total_divisa = kg * pu_divisa
                WHERE kg > 0 AND pu_divisa > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result3.rowcount} registros de costo_total_divisa")
            
            # 4. Actualizar costo_total_mxn (kg * pu_mxn)
            logger.info("  - Calculando costo_total_mxn...")
            result4 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET costo_total_mxn = kg * pu_mxn
                WHERE kg > 0 AND pu_mxn > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result4.rowcount} registros de costo_total_mxn")
            
            # 5. Actualizar pu_mxn_importacion (pu_mxn + gastos de importación por kg)
            logger.info("  - Calculando pu_mxn_importacion...")
            result5 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET pu_mxn_importacion = compras_v2_materiales.pu_mxn + (
                    CASE 
                        WHEN c2.moneda = 'MXN' THEN 
                            COALESCE(c2.gastos_importacion_mxn, 0) / 
                            NULLIF((SELECT SUM(c2m2.kg) FROM compras_v2_materiales c2m2 WHERE c2m2.compra_imi = c2.imi), 0)
                        WHEN c2.moneda = 'USD' THEN 
                            COALESCE(c2.gastos_importacion_divisa, 0) * COALESCE(c2.tipo_cambio_real, c2.tipo_cambio_estimado, 1.0) / 
                            NULLIF((SELECT SUM(c2m2.kg) FROM compras_v2_materiales c2m2 WHERE c2m2.compra_imi = c2.imi), 0)
                        ELSE compras_v2_materiales.pu_mxn
                    END
                )
                FROM compras_v2 c2
                WHERE compras_v2_materiales.compra_imi = c2.imi
            """))
            connection.commit()
            logger.info(f"    Actualizados {result5.rowcount} registros de pu_mxn_importacion")
            
            # 6. Actualizar costo_total_mxn_imporacion (kg * pu_mxn_importacion)
            logger.info("  - Calculando costo_total_mxn_imporacion...")
            result6 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET costo_total_mxn_imporacion = kg * pu_mxn_importacion
                WHERE kg > 0 AND pu_mxn_importacion > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result6.rowcount} registros de costo_total_mxn_imporacion")
            
            # 7. Actualizar iva (16% del costo total con importación)
            logger.info("  - Calculando iva...")
            result7 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET iva = costo_total_mxn_imporacion * 0.16
                WHERE costo_total_mxn_imporacion > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result7.rowcount} registros de iva")
            
            # 8. Actualizar costo_total_con_iva (costo_total_mxn_imporacion + iva)
            logger.info("  - Calculando costo_total_con_iva...")
            result8 = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET costo_total_con_iva = costo_total_mxn_imporacion + iva
                WHERE costo_total_mxn_imporacion > 0
            """))
            connection.commit()
            logger.info(f"    Actualizados {result8.rowcount} registros de costo_total_con_iva")
            
            # Actualizar timestamp
            connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET updated_at = %s
            """), (datetime.utcnow(),))
            connection.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Error actualizando compras_v2_materiales: {str(e)}")
        return False

def update_all_calculated_columns():
    """Actualiza todas las columnas calculadas en ambas tablas"""
    logger.info("=" * 60)
    logger.info("INICIANDO ACTUALIZACIÓN DE TODAS LAS COLUMNAS CALCULADAS")
    logger.info("=" * 60)
    
    # Actualizar compras_v2
    success1 = update_compras_v2_calculated_columns()
    
    # Actualizar compras_v2_materiales
    success2 = update_compras_v2_materiales_calculated_columns()
    
    if success1 and success2:
        logger.info("=" * 60)
        logger.info("✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)
        
        # Mostrar resumen de datos actualizados
        try:
            with engine.connect() as connection:
                # Estadísticas de compras_v2
                stats1 = connection.execute(text("""
                    SELECT 
                        COUNT(*) as total_compras,
                        AVG(total_con_iva_mxn) as promedio_total,
                        SUM(total_con_iva_mxn) as suma_total
                    FROM compras_v2 
                    WHERE total_con_iva_mxn > 0
                """)).fetchone()
                
                # Estadísticas de materiales
                stats2 = connection.execute(text("""
                    SELECT 
                        COUNT(*) as total_materiales,
                        AVG(pu_usd) as promedio_pu_usd,
                        SUM(costo_total_con_iva) as suma_total_iva
                    FROM compras_v2_materiales 
                    WHERE costo_total_con_iva > 0
                """)).fetchone()
                
                logger.info(f"📊 RESUMEN DE DATOS:")
                logger.info(f"   Compras V2: {stats1[0]} registros, promedio total: ${stats1[1]:.2f}")
                logger.info(f"   Materiales: {stats2[0]} registros, promedio pu_usd: ${stats2[1]:.2f}")
                
        except Exception as e:
            logger.warning(f"No se pudo obtener estadísticas: {e}")
        
        return True
    else:
        logger.error("=" * 60)
        logger.error("❌ ACTUALIZACIÓN FALLÓ")
        logger.error("=" * 60)
        return False

if __name__ == "__main__":
    success = update_all_calculated_columns()
    sys.exit(0 if success else 1)
