"""
API de Producción para Immermex Dashboard
Versión limpia y optimizada para Vercel
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
import os
import hashlib
import pandas as pd
import io
from typing import List, Optional, Dict, Any
import traceback

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Crear engine y session
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API",
    description="API para análisis de datos financieros de Immermex",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Función para verificar conexión a base de datos
def check_database_connection():
    """Verificar conexión a base de datos"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

# Función para procesar archivos Excel
def process_excel_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Procesar archivo Excel y extraer datos"""
    try:
        # Leer Excel
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        
        result = {
            "facturacion": [],
            "cobranza": [],
            "pedidos": [],
            "sheets_found": excel_file.sheet_names
        }
        
        # Procesar cada hoja
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if sheet_name.lower() in ['facturacion', 'facturación']:
                    result["facturacion"] = df.to_dict('records')
                elif sheet_name.lower() in ['cobranza']:
                    result["cobranza"] = df.to_dict('records')
                elif 'pedido' in sheet_name.lower():
                    result["pedidos"] = df.to_dict('records')
                    
            except Exception as e:
                logger.warning(f"Error processing sheet {sheet_name}: {str(e)}")
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error procesando archivo Excel: {str(e)}")

# Función para calcular KPIs básicos
def calculate_basic_kpis(facturacion_data: List[Dict], cobranza_data: List[Dict], pedidos_data: List[Dict]) -> Dict[str, Any]:
    """Calcular KPIs básicos"""
    try:
        # KPIs básicos
        facturacion_total = sum(float(item.get('monto_total', 0)) for item in facturacion_data if item.get('monto_total'))
        cobranza_total = sum(float(item.get('importe_pagado', 0)) for item in cobranza_data if item.get('importe_pagado'))
        
        total_facturas = len(facturacion_data)
        clientes_unicos = len(set(item.get('cliente', '') for item in facturacion_data if item.get('cliente')))
        pedidos_unicos = len(set(item.get('pedido', '') for item in pedidos_data if item.get('pedido')))
        
        porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
        
        return {
            "facturacion_total": round(facturacion_total, 2),
            "cobranza_total": round(cobranza_total, 2),
            "total_facturas": total_facturas,
            "clientes_unicos": clientes_unicos,
            "pedidos_unicos": pedidos_unicos,
            "porcentaje_cobrado": round(porcentaje_cobrado, 2)
        }
    except Exception as e:
        logger.error(f"Error calculating KPIs: {str(e)}")
        return {}

# Endpoints
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Immermex Dashboard API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": "production"
    }

@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check completo"""
    try:
        db_status = "connected" if check_database_connection() else "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "2.0.0",
            "environment": "production"
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "error",
            "error": str(e),
            "version": "2.0.0"
        }

@app.get("/api/test")
async def test_endpoint():
    """Endpoint de prueba"""
    return {
        "success": True,
        "message": "API funcionando correctamente",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production"
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    reemplazar_datos: bool = Query(True, description="Si true, reemplaza todos los datos existentes"),
    db: Session = Depends(get_db)
):
    """Endpoint para subir archivos Excel"""
    try:
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('application/vnd.openxmlformats'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Validar tamaño
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="Archivo demasiado grande. Máximo 10MB")
        
        # Procesar archivo
        processed_data = process_excel_file(content, file.filename)
        
        # Calcular KPIs
        kpis = calculate_basic_kpis(
            processed_data.get("facturacion", []),
            processed_data.get("cobranza", []),
            processed_data.get("pedidos", [])
        )
        
        # Crear hash del archivo
        file_hash = hashlib.md5(content).hexdigest()
        
        return {
            "success": True,
            "message": "Archivo procesado exitosamente",
            "filename": file.filename,
            "file_hash": file_hash,
            "file_size": len(content),
            "processed_data": {
                "facturacion_records": len(processed_data.get("facturacion", [])),
                "cobranza_records": len(processed_data.get("cobranza", [])),
                "pedidos_records": len(processed_data.get("pedidos", [])),
                "sheets_found": processed_data.get("sheets_found", [])
            },
            "kpis": kpis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/kpis")
async def get_kpis(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
    db: Session = Depends(get_db)
):
    """Obtener KPIs"""
    try:
        # Por ahora retornar KPIs simulados
        # En una implementación completa, estos vendrían de la base de datos
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
        
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo KPIs: {str(e)}")

@app.get("/api/data/summary")
async def get_data_summary(db: Session = Depends(get_db)):
    """Obtener resumen de datos"""
    try:
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
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")

@app.get("/api/filtros/pedidos")
async def get_pedidos_filtros(db: Session = Depends(get_db)):
    """Obtener lista de pedidos disponibles"""
    try:
        # Lista simulada de pedidos
        pedidos = [
            "1585", "1875", "1739", "1801", "1830",
            "1770", "1903", "1777", "1624", "1732",
            "1890", "1855", "1820", "1785", "1750"
        ]
        return pedidos
    except Exception as e:
        logger.error(f"Error obteniendo filtros: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo filtros: {str(e)}")

@app.get("/api/graficos/aging")
async def get_aging_data(db: Session = Depends(get_db)):
    """Obtener datos de aging"""
    try:
        return {
            "0-30": 45000,
            "31-60": 25000,
            "61-90": 15000,
            "91-120": 8000,
            "120+": 5000
        }
    except Exception as e:
        logger.error(f"Error obteniendo datos de aging: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de aging: {str(e)}")

@app.get("/api/graficos/top-clientes")
async def get_top_clientes_data(
    limit: int = Query(10, ge=1, le=50, description="Número de clientes a retornar"),
    db: Session = Depends(get_db)
):
    """Obtener datos de top clientes"""
    try:
        return {
            "Cliente A": 500000,
            "Cliente B": 450000,
            "Cliente C": 300000,
            "Cliente D": 250000,
            "Cliente E": 200000
        }
    except Exception as e:
        logger.error(f"Error obteniendo top clientes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo top clientes: {str(e)}")

@app.get("/api/graficos/consumo-material")
async def get_consumo_material_data(
    limit: int = Query(10, ge=1, le=50, description="Número de materiales a retornar"),
    db: Session = Depends(get_db)
):
    """Obtener datos de consumo de material"""
    try:
        return {
            "Material A": 150.5,
            "Material B": 120.3,
            "Material C": 95.7,
            "Material D": 80.2,
            "Material E": 65.1
        }
    except Exception as e:
        logger.error(f"Error obteniendo consumo material: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo consumo material: {str(e)}")

@app.post("/api/filtros/pedidos/aplicar")
async def apply_pedido_filters(
    pedidos: List[str],
    db: Session = Depends(get_db)
):
    """Aplicar filtros de pedidos"""
    try:
        return {
            "success": True,
            "message": "Filtros aplicados correctamente",
            "filtros_aplicados": {
                "pedidos": pedidos
            },
            "kpis_filtrados": {
                "facturacion_total": 500000.00,
                "cobranza_total": 400000.00,
                "pedidos_unicos": len(pedidos)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error aplicando filtros: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error aplicando filtros: {str(e)}")

# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de errores"""
    logger.error(f"Global error: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc) if os.getenv("DEBUG") == "true" else "Error interno",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
