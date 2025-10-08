import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configurar logging para mostrar salida
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

def fix_tipo_cambio_zeros():
    """Convierte tipos de cambio en 0 a NULL para evitar cálculos incorrectos"""
    db = SessionLocal()
    try:
        with engine.connect() as connection:
            logger.info("============================================================")
            logger.info("CORRIGIENDO TIPOS DE CAMBIO EN 0 A NULL")
            logger.info("============================================================")
            
            # 1. Verificar cuántos registros tienen tipo_cambio_real = 0
            logger.info("1. Verificando registros con tipo_cambio_real = 0...")
            count_real_zeros = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM compras_v2 
                WHERE tipo_cambio_real = 0
            """)).fetchone()
            
            logger.info(f"   Registros con tipo_cambio_real = 0: {count_real_zeros.count}")
            
            # 2. Verificar cuántos registros tienen tipo_cambio_estimado = 0
            logger.info("2. Verificando registros con tipo_cambio_estimado = 0...")
            count_estimado_zeros = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM compras_v2 
                WHERE tipo_cambio_estimado = 0
            """)).fetchone()
            
            logger.info(f"   Registros con tipo_cambio_estimado = 0: {count_estimado_zeros.count}")
            
            # 3. Verificar cuántos registros tienen tipo_cambio_real = 1.0
            logger.info("3. Verificando registros con tipo_cambio_real = 1.0...")
            count_real_ones = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM compras_v2 
                WHERE tipo_cambio_real = 1.0
            """)).fetchone()
            
            logger.info(f"   Registros con tipo_cambio_real = 1.0: {count_real_ones.count}")
            
            # 3b. Verificar cuántos registros tienen tipo_cambio_estimado = 1.0
            logger.info("3b. Verificando registros con tipo_cambio_estimado = 1.0...")
            count_estimado_ones = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM compras_v2 
                WHERE tipo_cambio_estimado = 1.0
            """)).fetchone()
            
            logger.info(f"   Registros con tipo_cambio_estimado = 1.0: {count_estimado_ones.count}")
            
            # 4. Actualizar tipo_cambio_real = 0 a NULL
            if count_real_zeros.count > 0:
                logger.info("4. Actualizando tipo_cambio_real = 0 a NULL...")
                result_real = connection.execute(text("""
                    UPDATE compras_v2 
                    SET tipo_cambio_real = NULL 
                    WHERE tipo_cambio_real = 0
                """))
                connection.commit()
                logger.info(f"   ✅ Actualizados {result_real.rowcount} registros de tipo_cambio_real")
            else:
                logger.info("4. No hay registros con tipo_cambio_real = 0 para actualizar")
            
            # 5. Actualizar tipo_cambio_estimado = 0 a NULL
            if count_estimado_zeros.count > 0:
                logger.info("5. Actualizando tipo_cambio_estimado = 0 a NULL...")
                result_estimado = connection.execute(text("""
                    UPDATE compras_v2 
                    SET tipo_cambio_estimado = NULL 
                    WHERE tipo_cambio_estimado = 0
                """))
                connection.commit()
                logger.info(f"   ✅ Actualizados {result_estimado.rowcount} registros de tipo_cambio_estimado")
            else:
                logger.info("5. No hay registros con tipo_cambio_estimado = 0 para actualizar")
            
            # 6. Actualizar tipo_cambio_real = 1.0 a NULL (también problemático)
            if count_real_ones.count > 0:
                logger.info("6. Actualizando tipo_cambio_real = 1.0 a NULL...")
                result_ones = connection.execute(text("""
                    UPDATE compras_v2 
                    SET tipo_cambio_real = NULL 
                    WHERE tipo_cambio_real = 1.0
                """))
                connection.commit()
                logger.info(f"   ✅ Actualizados {result_ones.rowcount} registros de tipo_cambio_real = 1.0")
            else:
                logger.info("6. No hay registros con tipo_cambio_real = 1.0 para actualizar")
            
            # 7. Actualizar tipo_cambio_estimado = 1.0 a NULL (también problemático)
            if count_estimado_ones.count > 0:
                logger.info("7. Actualizando tipo_cambio_estimado = 1.0 a NULL...")
                result_estimado_ones = connection.execute(text("""
                    UPDATE compras_v2 
                    SET tipo_cambio_estimado = NULL 
                    WHERE tipo_cambio_estimado = 1.0
                """))
                connection.commit()
                logger.info(f"   ✅ Actualizados {result_estimado_ones.rowcount} registros de tipo_cambio_estimado = 1.0")
            else:
                logger.info("7. No hay registros con tipo_cambio_estimado = 1.0 para actualizar")
            
            # 8. Verificar estadísticas después de la corrección
            logger.info("8. Estadísticas después de la corrección:")
            
            stats_after = connection.execute(text("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(tipo_cambio_real) as con_tipo_cambio_real,
                    COUNT(tipo_cambio_estimado) as con_tipo_cambio_estimado,
                    AVG(tipo_cambio_real) as avg_tipo_cambio_real,
                    AVG(tipo_cambio_estimado) as avg_tipo_cambio_estimado,
                    MIN(tipo_cambio_real) as min_tipo_cambio_real,
                    MAX(tipo_cambio_real) as max_tipo_cambio_real
                FROM compras_v2 
                WHERE fecha_pedido IS NOT NULL
            """)).fetchone()
            
            logger.info(f"   Total registros: {stats_after.total_registros}")
            logger.info(f"   Con tipo_cambio_real: {stats_after.con_tipo_cambio_real}")
            logger.info(f"   Con tipo_cambio_estimado: {stats_after.con_tipo_cambio_estimado}")
            logger.info(f"   Promedio tipo_cambio_real: {stats_after.avg_tipo_cambio_real:.4f}")
            logger.info(f"   Promedio tipo_cambio_estimado: {stats_after.avg_tipo_cambio_estimado:.4f}")
            logger.info(f"   Min tipo_cambio_real: {stats_after.min_tipo_cambio_real:.4f}")
            logger.info(f"   Max tipo_cambio_real: {stats_after.max_tipo_cambio_real:.4f}")
            
            # 9. Mostrar algunos ejemplos de tipos de cambio válidos
            logger.info("9. Ejemplos de tipos de cambio válidos:")
            examples = connection.execute(text("""
                SELECT 
                    imi,
                    proveedor,
                    moneda,
                    tipo_cambio_real,
                    tipo_cambio_estimado,
                    total_con_iva_mxn
                FROM compras_v2 
                WHERE (tipo_cambio_real IS NOT NULL OR tipo_cambio_estimado IS NOT NULL)
                AND fecha_pedido IS NOT NULL
                LIMIT 5
            """)).fetchall()
            
            for row in examples:
                logger.info(f"   IMI: {row.imi}, Moneda: {row.moneda}, TC Real: {row.tipo_cambio_real}, TC Est: {row.tipo_cambio_estimado}")
            
            logger.info("============================================================")
            logger.info("✅ CORRECCIÓN DE TIPOS DE CAMBIO COMPLETADA")
            logger.info("============================================================")
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Error durante corrección de tipos de cambio: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_tipo_cambio_zeros()
    sys.exit(0 if success else 1)
