"""
API simplificada para Immermex Dashboard
Versión mínima sin dependencias problemáticas
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os
from typing import List, Optional

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API",
    description="API para análisis de datos financieros de Immermex",
    version="2.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://edu-maass.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Immermex Dashboard API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "not_connected",
        "version": "2.0.0"
    }

@app.get("/api/test")
async def test_endpoint():
    """Endpoint de prueba"""
    return {
        "success": True,
        "message": "Test endpoint working",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production"
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint básico de upload (sin procesamiento)"""
    try:
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('application/vnd.openxmlformats'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Leer contenido
        content = await file.read()
        
        # Validar tamaño
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="Archivo demasiado grande. Máximo 10MB")
        
        return {
            "success": True,
            "message": "Archivo recibido correctamente (sin procesamiento)",
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/api/kpis")
async def get_kpis():
    """KPIs simulados para testing"""
    return {
        "facturacion_total": 1000000.00,
        "cobranza_total": 800000.00,
        "total_facturas": 100,
        "clientes_unicos": 25,
        "pedidos_unicos": 200,
        "message": "Datos simulados - API en modo testing",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/data/summary")
async def get_data_summary():
    """Resumen de datos simulado"""
    return {
        "has_data": False,
        "message": "API en modo testing - sin datos reales",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/filtros/pedidos")
async def get_pedidos_filtros():
    """Filtros de pedidos simulados"""
    return [
        "1585", "1875", "1739", "1801", "1830",
        "1770", "1903", "1777", "1624", "1732"
    ]

@app.get("/api/graficos/aging")
async def get_aging_data():
    """Datos de aging simulados"""
    return {
        "0-30": 45000,
        "31-60": 25000,
        "61-90": 15000,
        "91-120": 8000,
        "120+": 5000
    }

@app.get("/api/graficos/top-clientes")
async def get_top_clientes_data(limit: int = Query(10, ge=1, le=50)):
    """Datos de top clientes simulados"""
    return {
        "Cliente A": 500000,
        "Cliente B": 450000,
        "Cliente C": 300000,
        "Cliente D": 250000,
        "Cliente E": 200000
    }

@app.get("/api/graficos/consumo-material")
async def get_consumo_material_data(limit: int = Query(10, ge=1, le=50)):
    """Datos de consumo de material simulados"""
    return {
        "Material A": 150.5,
        "Material B": 120.3,
        "Material C": 95.7,
        "Material D": 80.2,
        "Material E": 65.1
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
