#!/usr/bin/env python3
"""
Script de migración para agregar columnas a la tabla existente de Proveedores
Agrega las columnas:
- promedio_dias_produccion
- promedio_dias_transporte_maritimo
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
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

def add_columns_to_proveedores():
    """Agrega las columnas solicitadas a la tabla Proveedores existente"""
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
        
        # Verificar si la tabla Proveedores existe
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'Proveedores' not in existing_tables:
            logger.error("La tabla 'Proveedores' no existe en la base de datos")
            return False
        
        # Obtener columnas existentes
        columns = inspector.get_columns('Proveedores')
        existing_column_names = [col['name'] for col in columns]
        
        logger.info(f"Columnas existentes en Proveedores: {existing_column_names}")
        
        # Definir las columnas a agregar
        columns_to_add = [
            {
                'name': 'promedio_dias_produccion',
                'sql': 'ALTER TABLE "Proveedores" ADD COLUMN promedio_dias_produccion DECIMAL(10,2) DEFAULT 0.0;'
            },
            {
                'name': 'promedio_dias_transporte_maritimo', 
                'sql': 'ALTER TABLE "Proveedores" ADD COLUMN promedio_dias_transporte_maritimo DECIMAL(10,2) DEFAULT 0.0;'
            }
        ]
        
        with engine.connect() as conn:
            # Ejecutar en una transacción
            trans = conn.begin()
            try:
                added_columns = []
                
                for column_info in columns_to_add:
                    column_name = column_info['name']
                    alter_sql = column_info['sql']
                    
                    if column_name not in existing_column_names:
                        conn.execute(text(alter_sql))
                        added_columns.append(column_name)
                        logger.info(f"Columna '{column_name}' agregada exitosamente")
                    else:
                        logger.info(f"Columna '{column_name}' ya existe, omitiendo")
                
                if added_columns:
                    trans.commit()
                    logger.info(f"Migración completada. Columnas agregadas: {added_columns}")
                else:
                    trans.rollback()
                    logger.info("No se agregaron nuevas columnas (todas ya existían)")
                
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error durante la migración: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return False

def verify_columns():
    """Verifica que las columnas se hayan agregado correctamente"""
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
        
        inspector = inspect(engine)
        columns = inspector.get_columns('Proveedores')
        column_names = [col['name'] for col in columns]
        
        required_columns = ['promedio_dias_produccion', 'promedio_dias_transporte_maritimo']
        
        logger.info("Verificación de columnas:")
        for col in required_columns:
            if col in column_names:
                logger.info(f"✓ Columna '{col}' existe")
            else:
                logger.error(f"✗ Columna '{col}' NO existe")
        
        return all(col in column_names for col in required_columns)
        
    except Exception as e:
        logger.error(f"Error verificando columnas: {str(e)}")
        return False

def main():
    """Función principal del script de migración"""
    logger.info("Iniciando migración para agregar columnas a tabla Proveedores...")
    
    # Agregar columnas
    if add_columns_to_proveedores():
        logger.info("Columnas agregadas exitosamente")
        
        # Verificar que se agregaron correctamente
        if verify_columns():
            logger.info("✓ Verificación exitosa: todas las columnas están presentes")
        else:
            logger.error("✗ Error en la verificación de columnas")
            sys.exit(1)
    else:
        logger.error("Error agregando columnas")
        sys.exit(1)
    
    logger.info("Migración completada exitosamente")

if __name__ == "__main__":
    main()
