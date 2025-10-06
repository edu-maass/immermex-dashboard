#!/usr/bin/env python3
"""
Script para calcular el promedio de días de producción por proveedor
basado en la diferencia entre fecha_salida_puerto (BL) y fecha_compra
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Obtiene la URL de la base de datos desde las variables de entorno"""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
    
    # Verificar si hay una URL PostgreSQL directa configurada
    POSTGRES_URL = os.getenv("POSTGRES_URL", "")
    if POSTGRES_URL and POSTGRES_URL.startswith("postgresql://"):
        DATABASE_URL = POSTGRES_URL
        logger.info("Usando URL PostgreSQL directa de POSTGRES_URL")
    elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_PASSWORD"):
        # Construir URL PostgreSQL desde variables de Supabase
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_password = os.getenv("SUPABASE_PASSWORD")
            
            # Extraer project ref de la URL de Supabase
            if "supabase.co" in supabase_url:
                project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
                # Usar pooler de Supabase para IPv4 compatibility
                DATABASE_URL = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
                logger.info(f"Construida URL PostgreSQL desde Supabase pooler: aws-1-us-west-1.pooler.supabase.com")
            else:
                logger.warning("Formato de SUPABASE_URL no reconocido, usando SQLite")
                DATABASE_URL = "sqlite:///./immermex.db"
        except Exception as e:
            logger.error(f"Error construyendo URL de Supabase: {str(e)}")
            DATABASE_URL = "sqlite:///./immermex.db"
    
    return DATABASE_URL

def calculate_production_days_averages():
    """Calcula el promedio de días de producción por proveedor"""
    DATABASE_URL = get_database_url()
    
    if not DATABASE_URL.startswith("postgresql://"):
        logger.warning("Este script está diseñado para PostgreSQL. URL actual: " + DATABASE_URL)
        return False
    
    try:
        # Crear engine
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={
                "sslmode": "require"
            }
        )
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"Conectado a PostgreSQL: {version}")
        
        # Consulta para calcular días de producción por proveedor
        # Días de producción = fecha_salida_puerto - fecha_compra
        calculation_sql = """
            SELECT 
                proveedor,
                COUNT(*) as total_registros,
                AVG(
                    CASE 
                        WHEN fecha_salida_puerto IS NOT NULL AND fecha_compra IS NOT NULL 
                        THEN EXTRACT(DAYS FROM (fecha_salida_puerto - fecha_compra))
                        ELSE NULL 
                    END
                ) as promedio_dias_produccion,
                MIN(fecha_compra) as primera_compra,
                MAX(fecha_compra) as ultima_compra
            FROM compras 
            WHERE proveedor IS NOT NULL 
                AND proveedor != ''
                AND fecha_salida_puerto IS NOT NULL 
                AND fecha_compra IS NOT NULL
                AND fecha_salida_puerto >= fecha_compra  -- Validar que BL sea posterior a compra
            GROUP BY proveedor
            ORDER BY promedio_dias_produccion DESC
        """
        
        logger.info("Calculando promedios de días de producción...")
        result = conn.execute(text(calculation_sql))
        averages = result.fetchall()
        
        if not averages:
            logger.warning("No se encontraron registros válidos para calcular promedios")
            return False
        
        logger.info(f"Se encontraron {len(averages)} proveedores con datos válidos")
        
        # Mostrar resultados
        logger.info("Resultados del cálculo:")
        logger.info("-" * 80)
        for row in averages:
            proveedor, total_registros, promedio, primera_compra, ultima_compra = row
            logger.info(f"Proveedor: {proveedor}")
            logger.info(f"  - Total registros: {total_registros}")
            logger.info(f"  - Promedio días producción: {promedio:.2f}")
            logger.info(f"  - Primera compra: {primera_compra}")
            logger.info(f"  - Última compra: {ultima_compra}")
            logger.info("-" * 40)
        
        return averages
        
    except Exception as e:
        logger.error(f"Error calculando promedios: {str(e)}")
        return False

def update_proveedores_table(averages):
    """Actualiza la tabla Proveedores con los promedios calculados"""
    DATABASE_URL = get_database_url()
    
    if not DATABASE_URL.startswith("postgresql://"):
        logger.warning("Este script está diseñado para PostgreSQL")
        return False
    
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={
                "sslmode": "require"
            }
        )
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                updated_count = 0
                
                for row in averages:
                    proveedor, total_registros, promedio, primera_compra, ultima_compra = row
                    
                    if promedio is not None:
                        # Actualizar o insertar en la tabla Proveedores
                        update_sql = """
                            INSERT INTO "Proveedores" ("Nombre", promedio_dias_produccion, created_at)
                            VALUES (:nombre, :promedio, CURRENT_TIMESTAMP)
                            ON CONFLICT ("Nombre") 
                            DO UPDATE SET 
                                promedio_dias_produccion = EXCLUDED.promedio_dias_produccion,
                                created_at = CASE 
                                    WHEN "Proveedores".created_at IS NULL THEN EXCLUDED.created_at
                                    ELSE "Proveedores".created_at
                                END
                        """
                        
                        conn.execute(text(update_sql), {
                            "nombre": proveedor,
                            "promedio": round(promedio, 2)
                        })
                        updated_count += 1
                        logger.info(f"Actualizado proveedor: {proveedor} con promedio: {promedio:.2f} días")
                
                trans.commit()
                logger.info(f"Se actualizaron {updated_count} proveedores exitosamente")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error actualizando tabla Proveedores: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return False

def verify_updates():
    """Verifica que las actualizaciones se realizaron correctamente"""
    DATABASE_URL = get_database_url()
    
    if not DATABASE_URL.startswith("postgresql://"):
        return False
    
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={
                "sslmode": "require"
            }
        )
        
        with engine.connect() as conn:
            # Consultar proveedores con promedios actualizados
            verify_sql = """
                SELECT "Nombre", promedio_dias_produccion, created_at
                FROM "Proveedores" 
                WHERE promedio_dias_produccion IS NOT NULL 
                    AND promedio_dias_produccion > 0
                ORDER BY promedio_dias_produccion DESC
            """
            
            result = conn.execute(text(verify_sql))
            updated_proveedores = result.fetchall()
            
            logger.info(f"Verificación: {len(updated_proveedores)} proveedores tienen promedios actualizados")
            
            for row in updated_proveedores:
                nombre, promedio, created_at = row
                logger.info(f"  - {nombre}: {promedio} días")
            
            return len(updated_proveedores) > 0
            
    except Exception as e:
        logger.error(f"Error verificando actualizaciones: {str(e)}")
        return False

def main():
    """Función principal del script"""
    logger.info("Iniciando cálculo de promedios de días de producción...")
    
    # Calcular promedios
    averages = calculate_production_days_averages()
    if not averages:
        logger.error("No se pudieron calcular los promedios")
        sys.exit(1)
    
    # Actualizar tabla Proveedores
    if update_proveedores_table(averages):
        logger.info("Tabla Proveedores actualizada exitosamente")
        
        # Verificar actualizaciones
        if verify_updates():
            logger.info("Verificación exitosa: los promedios se actualizaron correctamente")
        else:
            logger.error("Error en la verificación de actualizaciones")
            sys.exit(1)
    else:
        logger.error("Error actualizando tabla Proveedores")
        sys.exit(1)
    
    logger.info("Proceso completado exitosamente")

if __name__ == "__main__":
    main()
