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
    from database import get_db, init_db, ArchivoProcesado
    DB_IMPORTS_OK = True
    print("✅ Database imports OK")
except Exception as e:
    DB_IMPORTS_OK = False
    print(f"❌ Database imports failed: {str(e)}")

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
        "database_imports": DB_IMPORTS_OK
    }

@app.get("/test")
async def test():
    return {"test": "OK"}
