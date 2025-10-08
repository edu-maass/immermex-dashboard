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

def fix_pu_usd_calculation():
    """Corrige el cálculo de pu_usd usando tipos de cambio más realistas"""
    try:
        with engine.connect() as connection:
            logger.info("[RUNNING] Corrigiendo cálculo de pu_usd con tipos de cambio realistas...")
            
            # Tipos de cambio realistas para diferentes períodos (aproximados)
            # Basados en datos históricos del USD/MXN
            tipo_cambio_default = 20.0  # Tipo de cambio promedio realista para MXN a USD
            
            # Actualizar pu_usd con lógica corregida
            result = connection.execute(text("""
                UPDATE compras_v2_materiales 
                SET pu_usd = CASE 
                    WHEN c2.moneda = 'USD' THEN compras_v2_materiales.pu_divisa
                    WHEN c2.moneda = 'MXN' THEN 
                        CASE 
                            WHEN c2.tipo_cambio_real IS NOT NULL AND c2.tipo_cambio_real > 0 AND c2.tipo_cambio_real != 1.0 
                            THEN compras_v2_materiales.pu_divisa / c2.tipo_cambio_real
                            WHEN c2.tipo_cambio_estimado IS NOT NULL AND c2.tipo_cambio_estimado > 0 AND c2.tipo_cambio_estimado != 1.0 
                            THEN compras_v2_materiales.pu_divisa / c2.tipo_cambio_estimado
                            ELSE compras_v2_materiales.pu_divisa / :tipo_cambio_default
                        END
                    ELSE compras_v2_materiales.pu_divisa
                END
                FROM compras_v2 c2
                WHERE compras_v2_materiales.compra_imi = c2.imi
            """), {"tipo_cambio_default": tipo_cambio_default})
            
            connection.commit()
            logger.info(f"    Actualizados {result.rowcount} registros con cálculo corregido de pu_usd")
            
            # Verificar algunos valores corregidos
            verification = connection.execute(text("""
                SELECT 
                    c2m.material_codigo,
                    c2m.pu_divisa,
                    c2m.pu_usd,
                    c2m.pu_mxn,
                    c2.moneda,
                    c2.tipo_cambio_real,
                    c2.tipo_cambio_estimado
                FROM compras_v2_materiales c2m
                JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
                WHERE c2.moneda = 'MXN' AND c2m.pu_divisa > 50
                ORDER BY c2m.pu_divisa DESC
                LIMIT 5
            """)).fetchall()
            
            logger.info("[VERIFICATION] Registros corregidos (MXN con pu_divisa > 50):")
            for row in verification:
                logger.info(f"  Material: {row[0]}, pu_divisa: {row[1]:.2f}, pu_usd: {row[2]:.2f}, pu_mxn: {row[3]:.2f}, tc_real: {row[5]}, tc_est: {row[6]}")
            
            # Estadísticas finales
            stats = connection.execute(text("""
                SELECT 
                    COUNT(*) as total_registros,
                    AVG(CASE WHEN c2.moneda = 'USD' THEN c2m.pu_usd END) as avg_pu_usd_usd,
                    AVG(CASE WHEN c2.moneda = 'MXN' THEN c2m.pu_usd END) as avg_pu_usd_mxn,
                    MIN(CASE WHEN c2.moneda = 'MXN' THEN c2m.pu_usd END) as min_pu_usd_mxn,
                    MAX(CASE WHEN c2.moneda = 'MXN' THEN c2m.pu_usd END) as max_pu_usd_mxn
                FROM compras_v2_materiales c2m
                JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
                WHERE c2m.pu_usd > 0
            """)).fetchone()
            
            logger.info(f"[STATS] Total registros: {stats[0]}")
            logger.info(f"[STATS] Promedio pu_usd (USD): ${stats[1]:.2f}")
            logger.info(f"[STATS] Promedio pu_usd (MXN→USD): ${stats[2]:.2f}")
            logger.info(f"[STATS] Rango pu_usd (MXN→USD): ${stats[3]:.2f} - ${stats[4]:.2f}")
            
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Error corrigiendo pu_usd: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("CORRIGIENDO CÁLCULO DE PU_USD CON TIPOS DE CAMBIO REALISTAS")
    logger.info("=" * 60)
    
    success = fix_pu_usd_calculation()
    
    if success:
        logger.info("=" * 60)
        logger.info("✅ CORRECCIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("❌ CORRECCIÓN FALLÓ")
        logger.error("=" * 60)
        sys.exit(1)
