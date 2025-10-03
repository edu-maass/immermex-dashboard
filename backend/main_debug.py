"""
API mínima para debug de deployment en Vercel
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from datetime import datetime
import os

# Probar importaciones locales una por una
try:
    # Verificar DATABASE_URL antes de importar
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
    print(f"🔍 DATABASE_URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"🔍 DATABASE_URL: {DATABASE_URL}")
    
    from database import get_db, init_db, ArchivoProcesado
    DB_IMPORTS_OK = True
    DB_ERROR = None
    print("✅ Database imports OK")
except Exception as e:
    DB_IMPORTS_OK = False
    DB_ERROR = str(e)
    print(f"❌ Database imports failed: {str(e)}")

# Probar importaciones específicas
try:
    import sqlalchemy
    SQLALCHEMY_OK = True
    SQLALCHEMY_ERROR = None
except Exception as e:
    SQLALCHEMY_OK = False
    SQLALCHEMY_ERROR = str(e)

try:
    import psycopg2
    PSYCOPG2_OK = True
    PSYCOPG2_ERROR = None
except Exception as e:
    PSYCOPG2_OK = False
    PSYCOPG2_ERROR = str(e)

app = FastAPI(title="Debug API")

# Agregar middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/")
async def root():
    return {
        "message": "Debug API funcionando con middleware",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "database_imports": DB_IMPORTS_OK,
        "database_error": DB_ERROR,
        "sqlalchemy_ok": SQLALCHEMY_OK,
        "sqlalchemy_error": SQLALCHEMY_ERROR,
        "psycopg2_ok": PSYCOPG2_OK,
        "psycopg2_error": PSYCOPG2_ERROR,
        "database_url_preview": os.getenv("DATABASE_URL", "not_set")[:20] + "..." if len(os.getenv("DATABASE_URL", "")) > 20 else os.getenv("DATABASE_URL", "not_set"),
        "supabase_password_set": "yes" if os.getenv("SUPABASE_PASSWORD") else "no",
        "postgres_url_set": "yes" if os.getenv("POSTGRES_URL") else "no",
        "supabase_url_set": "yes" if os.getenv("SUPABASE_URL") else "no",
        "supabase_key_set": "yes" if os.getenv("SUPABASE_KEY") else "no",
        "final_database_url_preview": os.getenv("DATABASE_URL", "not_set")[:30] + "..." if len(os.getenv("DATABASE_URL", "")) > 30 else os.getenv("DATABASE_URL", "not_set"),
        "supabase_url_value": os.getenv("SUPABASE_URL", "not_set")[:30] + "..." if len(os.getenv("SUPABASE_URL", "")) > 30 else os.getenv("SUPABASE_URL", "not_set")
    }

@app.get("/test")
async def test():
    return {"test": "OK"}
