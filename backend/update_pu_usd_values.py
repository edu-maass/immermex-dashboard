import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

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

def update_pu_usd_values():
    try:
        with engine.connect() as connection:
            print("[RUNNING] Actualizando valores de pu_usd...")
            
            # Actualizar valores existentes
            result = connection.execute(text("""
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
            print(f"[OK] Actualizados {result.rowcount} registros con valores de pu_usd.")
            
            # Verificar algunos valores
            verification = connection.execute(text("""
                SELECT 
                    c2m.id,
                    c2m.pu_divisa,
                    c2m.pu_usd,
                    c2.moneda,
                    c2.tipo_cambio_real,
                    c2.tipo_cambio_estimado
                FROM compras_v2_materiales c2m
                JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
                WHERE c2m.pu_usd IS NOT NULL
                LIMIT 5
            """)).fetchall()
            
            print("[VERIFICATION] Primeros 5 registros actualizados:")
            for row in verification:
                print(f"  ID: {row[0]}, pu_divisa: {row[1]}, pu_usd: {row[2]}, moneda: {row[3]}, tc_real: {row[4]}, tc_est: {row[5]}")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Error actualizando valores de pu_usd: {str(e)}")
        return False

if __name__ == "__main__":
    print("[RUNNING] Actualizando valores de pu_usd en compras_v2_materiales...")
    success = update_pu_usd_values()
    
    if success:
        print("[SUCCESS] Actualización de valores completada exitosamente")
        sys.exit(0)
    else:
        print("[FAILED] Actualización de valores falló")
        sys.exit(1)
