"""
API REST para Immermex Dashboard - VERSION MINIMAL PARA DEBUG
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from datetime import datetime
import logging
import os

# Configurar logging
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API - Debug Version",
    description="API REST para dashboard de indicadores financieros - VERSION DEBUG",
    version="debug-1.0.0"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agregar compresión GZIP
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {
        "message": "Immermex Dashboard API - Debug Version", 
        "status": "active",
        "version": "debug-1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/api/simple-health")
async def simple_health():
    """Endpoint simple de salud sin base de datos"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Debug API funcionando correctamente",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/api/test")
async def test():
    """Endpoint de prueba"""
    return {
        "test": "OK",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "python_version": os.sys.version
    }
