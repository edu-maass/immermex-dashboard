from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Immermex Dashboard API",
    description="API para análisis de datos financieros de Immermex",
    version="2.0.0"
)

# CORS
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

@app.get("/")
def read_root():
    return {
        "message": "Immermex Dashboard API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/test")
def test():
    return {
        "success": True,
        "message": "API funcionando correctamente",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint básico de upload (sin procesamiento por ahora)"""
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
            "message": "Archivo recibido correctamente (procesamiento básico)",
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
def get_kpis(
    mes: int = Query(None, description="Filtrar por mes"),
    año: int = Query(None, description="Filtrar por año"),
    pedidos: str = Query(None, description="Lista de pedidos separados por coma")
):
    """KPIs simulados para testing"""
    kpis = {
        "facturacion_total": 1000000.00,
        "facturacion_sin_iva": 862068.97,
        "cobranza_total": 800000.00,
        "cobranza_general_total": 800000.00,
        "cobranza_sin_iva": 689655.17,
        "anticipos_total": 50000.00,
        "porcentaje_anticipos": 5.0,
        "total_facturas": 100,
        "clientes_unicos": 25,
        "pedidos_unicos": 200,
        "toneladas_total": 1500.75,
        "porcentaje_cobrado": 80.0,
        "porcentaje_cobrado_general": 80.0,
        "expectativa_cobranza": {
            "Semana 1": {"cobranza_esperada": 50000, "cobranza_real": 45000},
            "Semana 2": {"cobranza_esperada": 45000, "cobranza_real": 42000},
            "Semana 3": {"cobranza_esperada": 40000, "cobranza_real": 38000},
            "Semana 4": {"cobranza_esperada": 35000, "cobranza_real": 32000}
        }
    }
    
    # Aplicar filtros básicos si se proporcionan
    if mes or año or pedidos:
        kpis["filtros_aplicados"] = {
            "mes": mes,
            "año": año,
            "pedidos": pedidos.split(",") if pedidos else None
        }
    
    return kpis

@app.get("/api/data/summary")
def get_data_summary():
    """Resumen de datos simulado"""
    return {
        "has_data": True,
        "message": "Datos disponibles (modo simulación)",
        "conteos": {
            "facturas": 100,
            "cobranzas": 80,
            "pedidos": 200
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/filtros/pedidos")
def get_pedidos_filtros():
    """Filtros de pedidos simulados"""
    return [
        "1585", "1875", "1739", "1801", "1830",
        "1770", "1903", "1777", "1624", "1732",
        "1890", "1855", "1820", "1785", "1750"
    ]

@app.get("/api/graficos/aging")
def get_aging_data():
    """Datos de aging simulados"""
    return {
        "0-30": 45000,
        "31-60": 25000,
        "61-90": 15000,
        "91-120": 8000,
        "120+": 5000
    }

@app.get("/api/graficos/top-clientes")
def get_top_clientes_data(limit: int = Query(10, ge=1, le=50)):
    """Datos de top clientes simulados"""
    return {
        "Cliente A": 500000,
        "Cliente B": 450000,
        "Cliente C": 300000,
        "Cliente D": 250000,
        "Cliente E": 200000
    }

@app.get("/api/graficos/consumo-material")
def get_consumo_material_data(limit: int = Query(10, ge=1, le=50)):
    """Datos de consumo de material simulados"""
    return {
        "Material A": 150.5,
        "Material B": 120.3,
        "Material C": 95.7,
        "Material D": 80.2,
        "Material E": 65.1
    }

# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de errores"""
    logger.error(f"Global error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )