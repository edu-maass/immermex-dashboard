import os
import sys
from sqlalchemy import create_engine, text, Float
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

def add_pu_usd_column():
    db = SessionLocal()
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            try:
                # Agregar columna pu_usd
                connection.execute(text("""
                    ALTER TABLE compras_v2_materiales 
                    ADD COLUMN pu_usd REAL
                """))
                connection.commit()
                print("[OK] Columna 'pu_usd' agregada a 'compras_v2_materiales'.")
                
                # Actualizar valores existentes
                print("[RUNNING] Calculando valores para pu_usd...")
                connection.execute(text("""
                    UPDATE compras_v2_materiales 
                    SET pu_usd = CASE 
                        WHEN c2.moneda = 'USD' THEN c2m.pu_divisa
                        WHEN c2.moneda = 'MXN' THEN 
                            CASE 
                                WHEN c2.tipo_cambio_real IS NOT NULL AND c2.tipo_cambio_real > 0 
                                THEN c2m.pu_divisa / c2.tipo_cambio_real
                                WHEN c2.tipo_cambio_estimado IS NOT NULL AND c2.tipo_cambio_estimado > 0 
                                THEN c2m.pu_divisa / c2.tipo_cambio_estimado
                                ELSE c2m.pu_divisa
                            END
                        ELSE c2m.pu_divisa
                    END
                    FROM compras_v2 c2
                    WHERE compras_v2_materiales.compra_imi = c2.imi
                """))
                connection.commit()
                print("[OK] Valores de pu_usd calculados y actualizados.")
                
                return True
            except OperationalError as e:
                if "duplicate column" in str(e) or "already exists" in str(e):
                    print("[INFO] La columna 'pu_usd' ya existe en 'compras_v2_materiales'.")
                    print("[RUNNING] Actualizando valores existentes...")
                    
                    # Solo actualizar valores si la columna ya existe
                    connection.execute(text("""
                        UPDATE compras_v2_materiales 
                        SET pu_usd = CASE 
                            WHEN c2.moneda = 'USD' THEN c2m.pu_divisa
                            WHEN c2.moneda = 'MXN' THEN 
                                CASE 
                                    WHEN c2.tipo_cambio_real IS NOT NULL AND c2.tipo_cambio_real > 0 
                                    THEN c2m.pu_divisa / c2.tipo_cambio_real
                                    WHEN c2.tipo_cambio_estimado IS NOT NULL AND c2.tipo_cambio_estimado > 0 
                                    THEN c2m.pu_divisa / c2.tipo_cambio_estimado
                                    ELSE c2m.pu_divisa
                                END
                            ELSE c2m.pu_divisa
                        END
                        FROM compras_v2 c2
                        WHERE compras_v2_materiales.compra_imi = c2.imi
                    """))
                    connection.commit()
                    print("[OK] Valores de pu_usd actualizados.")
                    return True
                else:
                    print(f"[ERROR] Error agregando columna: {str(e)}")
                    return False
            except Exception as e:
                print(f"[ERROR] Error inesperado al ejecutar ALTER TABLE: {str(e)}")
                return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("[RUNNING] Agregando columna pu_usd a compras_v2_materiales...")
    success = add_pu_usd_column()
    
    if success:
        print("[SUCCESS] Migración completada exitosamente")
        sys.exit(0)
    else:
        print("[FAILED] Migración falló")
        sys.exit(1)
