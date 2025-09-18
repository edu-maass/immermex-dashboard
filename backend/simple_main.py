"""
API REST simplificada para Immermex Dashboard (sin pandas)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API (Simple)",
    description="API REST simplificada para dashboard de indicadores financieros",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos de prueba en memoria
sample_kpis = {
    "facturacion_total": 500000.0,
    "cobranza_total": 400000.0,
    "anticipos_total": 50000.0,
    "porcentaje_cobrado": 80.0,
    "rotacion_inventario": 2.5,
    "total_facturas": 100,
    "clientes_unicos": 8,
    "aging_cartera": {
        "0-30 días": 5,
        "31-60 días": 3,
        "61-90 días": 2,
        "90+ días": 1
    },
    "top_clientes": {
        "ACME Corp": 150000.0,
        "Tech Solutions": 120000.0,
        "Industrial Supplies": 100000.0,
        "Manufacturing Co": 80000.0,
        "Global Systems": 50000.0
    },
    "consumo_material": {
        "Acero Inoxidable 304": 2000.0,
        "Aluminio 6061": 1500.0,
        "Cobre C11000": 1000.0,
        "Bronce C83600": 800.0,
        "Titanio Grade 2": 600.0
    }
}

@app.on_event("startup")
async def startup_event():
    logger.info("API simplificada iniciada correctamente")

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {"message": "Immermex Dashboard API (Simple)", "status": "active"}

@app.get("/api/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/kpis")
async def get_kpis():
    """Obtiene KPIs principales del dashboard"""
    try:
        return sample_kpis
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/aging")
async def get_grafico_aging():
    """Obtiene datos para gráfico de aging de cartera"""
    try:
        aging = sample_kpis["aging_cartera"]
        return {
            "labels": list(aging.keys()),
            "data": list(aging.values()),
            "titulo": "Aging de Cartera"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de aging: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/top-clientes")
async def get_grafico_top_clientes(limite: int = 10):
    """Obtiene datos para gráfico de top clientes"""
    try:
        clientes = sample_kpis["top_clientes"]
        labels = list(clientes.keys())[:limite]
        data = list(clientes.values())[:limite]
        return {
            "labels": labels,
            "data": data,
            "titulo": f"Top {limite} Clientes por Facturación"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de top clientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/consumo-material")
async def get_grafico_consumo_material(limite: int = 10):
    """Obtiene datos para gráfico de consumo por material"""
    try:
        materiales = sample_kpis["consumo_material"]
        labels = list(materiales.keys())[:limite]
        data = list(materiales.values())[:limite]
        return {
            "labels": labels,
            "data": data,
            "titulo": f"Top {limite} Materiales por Consumo"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de consumo de material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archivos")
async def get_archivos_procesados():
    """Obtiene lista de archivos procesados (simulado)"""
    try:
        return [
            {
                "id": 1,
                "nombre_archivo": "datos_prueba_immermex.xlsx",
                "fecha_procesamiento": "2024-01-15T10:30:00",
                "registros_procesados": 100,
                "estado": "procesado",
                "mes": 1,
                "año": 2024
            }
        ]
    except Exception as e:
        logger.error(f"Error obteniendo archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor Immermex Dashboard (Simple)")
    print("📊 Backend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔄 Frontend: http://localhost:3000")
    print("=" * 50)
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
