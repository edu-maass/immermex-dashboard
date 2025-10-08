import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")

if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///./immermex.db"

POSTGRES_URL = os.getenv("POSTGRES_URL", "")
if POSTGRES_URL and POSTGRES_URL.startswith("postgresql://"):
    DATABASE_URL = POSTGRES_URL
    print("Usando URL PostgreSQL directa de POSTGRES_URL")
elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_PASSWORD"):
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_PASSWORD")
        
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
            DATABASE_URL = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
            print(f"Construida URL PostgreSQL desde Supabase pooler: aws-1-us-west-1.pooler.supabase.com")
        else:
            print("URL de Supabase no reconocida, usando SQLite por defecto.")
    except Exception as e:
        print(f"Error al construir URL de Supabase: {e}, usando SQLite por defecto.")
        DATABASE_URL = "sqlite:///./immermex.db"
else:
    print("No se encontraron variables de entorno para Supabase o PostgreSQL, usando SQLite por defecto.")

print(f"Conectando a la base de datos: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def add_facturacion_id_column():
    db = SessionLocal()
    try:
        with engine.connect() as connection:
            # Verificar si la tabla facturacion existe
            if DATABASE_URL.startswith("postgresql"):
                # PostgreSQL
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'facturacion'
                    );
                """))
                table_exists = result.scalar()
                
                if not table_exists:
                    print("[INFO] La tabla 'facturacion' no existe. No se requiere migración.")
                    return True
                
                # Verificar si la columna id ya existe
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'facturacion' 
                        AND column_name = 'id'
                    );
                """))
                id_column_exists = result.scalar()
                
                if id_column_exists:
                    print("[INFO] La columna 'id' ya existe en la tabla 'facturacion'. No se requiere migración.")
                    return True
                
                # Agregar columna id como SERIAL (auto-increment)
                connection.execute(text("""
                    ALTER TABLE facturacion 
                    ADD COLUMN id SERIAL PRIMARY KEY
                """))
                connection.commit()
                print("[OK] Columna 'id' agregada como SERIAL PRIMARY KEY a 'facturacion'.")
                
            else:
                # SQLite
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='facturacion';
                """))
                table_exists = result.fetchone()
                
                if not table_exists:
                    print("[INFO] La tabla 'facturacion' no existe. No se requiere migración.")
                    return True
                
                # En SQLite, verificar si la columna existe es más complejo
                result = connection.execute(text("PRAGMA table_info(facturacion);"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'id' in columns:
                    print("[INFO] La columna 'id' ya existe en la tabla 'facturacion'. No se requiere migración.")
                    return True
                
                # En SQLite no se puede agregar una columna PRIMARY KEY después de crear la tabla
                # Necesitamos recrear la tabla
                print("[WARNING] SQLite no permite agregar PRIMARY KEY después de crear la tabla.")
                print("[WARNING] Se requiere recrear la tabla 'facturacion' con la columna 'id'.")
                print("[WARNING] Esto puede causar pérdida de datos. Por favor, haga backup primero.")
                return False
            
            return True
            
    except OperationalError as e:
        if "already exists" in str(e) or "duplicate column" in str(e):
            print("[INFO] La columna 'id' ya existe en 'facturacion'. No se requiere acción.")
            return True
        else:
            print(f"[ERROR] Error agregando columna: {str(e)}")
            return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("[RUNNING] Agregando columna id a facturacion...")
    success = add_facturacion_id_column()
    
    if success:
        print("[SUCCESS] Migración completada exitosamente")
        sys.exit(0)
    else:
        print("[FAILED] Migración falló")
        sys.exit(1)
