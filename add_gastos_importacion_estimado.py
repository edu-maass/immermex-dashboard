#!/usr/bin/env python3
"""
Script para agregar la columna gastos_importacion_estimado y calcular valores estimados
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_gastos_importacion_estimado_column():
    """Agrega la columna gastos_importacion_estimado y calcula valores estimados"""
    
    # Configuración de base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
    
    try:
        # Crear engine
        engine = create_engine(DATABASE_URL)
        
        # Verificar si la columna ya existe
        with engine.connect() as conn:
            # Para SQLite
            if DATABASE_URL.startswith("sqlite"):
                result = conn.execute(text("""
                    PRAGMA table_info(compras_v2);
                """)).fetchall()
                
                column_exists = any(row[1] == 'gastos_importacion_estimado' for row in result)
                
                if not column_exists:
                    logger.info("Agregando columna gastos_importacion_estimado...")
                    conn.execute(text("""
                        ALTER TABLE compras_v2 
                        ADD COLUMN gastos_importacion_estimado REAL DEFAULT 0.0;
                    """))
                    conn.commit()
                    logger.info("Columna agregada exitosamente")
                else:
                    logger.info("La columna gastos_importacion_estimado ya existe")
            
            # Para PostgreSQL
            elif DATABASE_URL.startswith("postgresql"):
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'compras_v2' 
                    AND column_name = 'gastos_importacion_estimado';
                """)).fetchall()
                
                if not result:
                    logger.info("Agregando columna gastos_importacion_estimado...")
                    conn.execute(text("""
                        ALTER TABLE compras_v2 
                        ADD COLUMN gastos_importacion_estimado REAL DEFAULT 0.0;
                    """))
                    conn.commit()
                    logger.info("Columna agregada exitosamente")
                else:
                    logger.info("La columna gastos_importacion_estimado ya existe")
        
        # Calcular gastos estimados (15% del costo total)
        logger.info("Calculando gastos de importación estimados...")
        
        with engine.connect() as conn:
            # Actualizar registros donde gastos_importacion_estimado es 0 o NULL
            # y hay un costo total disponible
            update_query = text("""
                UPDATE compras_v2 
                SET gastos_importacion_estimado = (
                    CASE 
                        WHEN gastos_importacion_mxn > 0 THEN gastos_importacion_mxn
                        WHEN total_con_iva_mxn > 0 THEN total_con_iva_mxn * 0.15
                        ELSE 0
                    END
                )
                WHERE gastos_importacion_estimado = 0 OR gastos_importacion_estimado IS NULL;
            """)
            
            result = conn.execute(update_query)
            conn.commit()
            
            logger.info(f"Actualizados {result.rowcount} registros con gastos estimados")
        
        logger.info("Proceso completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    add_gastos_importacion_estimado_column()
