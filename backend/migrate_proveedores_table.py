#!/usr/bin/env python3
"""
Script de migración para crear la tabla de Proveedores en PostgreSQL
Agrega la tabla proveedores con las columnas:
- Promedio días de producción
- Promedio días de transporte marítimo
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

def create_proveedores_table():
    """Crea la tabla de proveedores en la base de datos"""
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
        
        # Verificar si la tabla ya existe
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'proveedores' in existing_tables:
            logger.info("La tabla 'proveedores' ya existe en la base de datos")
            return True
        
        # Crear la tabla proveedores
        create_table_sql = """
        CREATE TABLE proveedores (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) UNIQUE NOT NULL,
            promedio_dias_produccion DECIMAL(10,2) DEFAULT 0.0,
            promedio_dias_transporte_maritimo DECIMAL(10,2) DEFAULT 0.0,
            pais_origen VARCHAR(100),
            contacto VARCHAR(255),
            email VARCHAR(255),
            telefono VARCHAR(50),
            direccion TEXT,
            notas TEXT,
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Crear índices
        create_indexes_sql = [
            "CREATE INDEX idx_proveedor_nombre ON proveedores(nombre);",
            "CREATE INDEX idx_proveedor_activo ON proveedores(activo);"
        ]
        
        # Crear trigger para updated_at
        create_trigger_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_proveedores_updated_at 
        BEFORE UPDATE ON proveedores 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        with engine.connect() as conn:
            # Ejecutar en una transacción
            trans = conn.begin()
            try:
                # Crear tabla
                conn.execute(text(create_table_sql))
                logger.info("Tabla 'proveedores' creada exitosamente")
                
                # Crear índices
                for index_sql in create_indexes_sql:
                    conn.execute(text(index_sql))
                logger.info("Índices creados exitosamente")
                
                # Crear trigger
                conn.execute(text(create_trigger_sql))
                logger.info("Trigger para updated_at creado exitosamente")
                
                trans.commit()
                logger.info("Migración completada exitosamente")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error durante la migración: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return False

def populate_proveedores_from_compras():
    """Pobla la tabla proveedores con datos existentes de la tabla compras"""
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
        
        # Verificar si existen datos en compras
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM compras"))
            compras_count = result.fetchone()[0]
            
            if compras_count == 0:
                logger.info("No hay datos en la tabla compras para migrar")
                return True
            
            # Obtener proveedores únicos de compras
            result = conn.execute(text("""
                SELECT DISTINCT proveedor 
                FROM compras 
                WHERE proveedor IS NOT NULL AND proveedor != ''
                ORDER BY proveedor
            """))
            proveedores = result.fetchall()
            
            logger.info(f"Encontrados {len(proveedores)} proveedores únicos en compras")
            
            # Insertar proveedores en la nueva tabla
            insert_sql = """
                INSERT INTO proveedores (nombre, activo, created_at, updated_at)
                VALUES (:nombre, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (nombre) DO NOTHING
            """
            
            inserted_count = 0
            for proveedor_row in proveedores:
                proveedor_nombre = proveedor_row[0]
                if proveedor_nombre and proveedor_nombre.strip():
                    conn.execute(text(insert_sql), {"nombre": proveedor_nombre.strip()})
                    inserted_count += 1
            
            conn.commit()
            logger.info(f"Insertados {inserted_count} proveedores en la tabla proveedores")
            return True
            
    except Exception as e:
        logger.error(f"Error poblando proveedores: {str(e)}")
        return False

def main():
    """Función principal del script de migración"""
    logger.info("Iniciando migración de tabla proveedores...")
    
    # Crear tabla
    if create_proveedores_table():
        logger.info("Tabla proveedores creada exitosamente")
        
        # Poblar con datos existentes
        if populate_proveedores_from_compras():
            logger.info("Datos de proveedores migrados exitosamente")
        else:
            logger.warning("Error poblando datos de proveedores")
    else:
        logger.error("Error creando tabla proveedores")
        sys.exit(1)
    
    logger.info("Migración completada")

if __name__ == "__main__":
    main()
