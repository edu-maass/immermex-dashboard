#!/usr/bin/env python3
"""
Script para agregar la columna gastos_importacion_estimado a la tabla compras_v2
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Agregar el directorio backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")

# Verificar si hay una URL PostgreSQL directa configurada
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
if POSTGRES_URL and POSTGRES_URL.startswith("postgresql://"):
    DATABASE_URL = POSTGRES_URL
elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_PASSWORD"):
    # Construir URL PostgreSQL desde variables de Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_password = os.getenv("SUPABASE_PASSWORD")
    
    # Extraer project ref de la URL de Supabase
    if "supabase.co" in supabase_url:
        project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
        # Usar pooler de Supabase para IPv4 compatibility
        DATABASE_URL = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"

def add_gastos_importacion_estimado_column():
    """Agrega la columna gastos_importacion_estimado a la tabla compras_v2"""
    try:
        # Crear engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Verificar si la columna ya existe
            if DATABASE_URL.startswith("postgresql"):
                check_column_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'compras_v2' 
                    AND column_name = 'gastos_importacion_estimado'
                """)
            else:
                check_column_query = text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='compras_v2'
                """)
            
            result = connection.execute(check_column_query).fetchone()
            
            if DATABASE_URL.startswith("postgresql"):
                if result:
                    print("[OK] Columna 'gastos_importacion_estimado' ya existe en la tabla compras_v2")
                    return True
                
                # Agregar columna para PostgreSQL
                add_column_query = text("""
                    ALTER TABLE compras_v2 
                    ADD COLUMN gastos_importacion_estimado FLOAT DEFAULT 0.0
                """)
            else:
                # Para SQLite, verificar si la columna existe de otra manera
                try:
                    test_query = text("SELECT gastos_importacion_estimado FROM compras_v2 LIMIT 1")
                    connection.execute(test_query)
                    print("[OK] Columna 'gastos_importacion_estimado' ya existe en la tabla compras_v2")
                    return True
                except:
                    # Agregar columna para SQLite
                    add_column_query = text("""
                        ALTER TABLE compras_v2 
                        ADD COLUMN gastos_importacion_estimado REAL DEFAULT 0.0
                    """)
            
            # Ejecutar la consulta para agregar la columna
            connection.execute(add_column_query)
            connection.commit()
            
            print("[OK] Columna 'gastos_importacion_estimado' agregada exitosamente a la tabla compras_v2")
            return True
            
    except SQLAlchemyError as e:
        print(f"[ERROR] Error agregando columna: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    print("[RUNNING] Agregando columna gastos_importacion_estimado a compras_v2...")
    success = add_gastos_importacion_estimado_column()
    
    if success:
        print("[SUCCESS] Migración completada exitosamente")
        sys.exit(0)
    else:
        print("[FAILED] Migración falló")
        sys.exit(1)
