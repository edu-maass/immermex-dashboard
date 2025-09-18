"""
API REST para Immermex Dashboard
FastAPI backend con endpoints para KPIs, gráficos y gestión de datos
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import os
from datetime import datetime
import logging

from database import get_db, init_db, ArchivoProcesado
from models import (
    KPIsResponse, FiltrosDashboard, PedidoDetalleResponse, 
    ClienteDetalleResponse, ArchivoUploadResponse
)
from services import DashboardService
from data_processor import ImmermexDataProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API",
    description="API REST para dashboard de indicadores financieros y operativos",
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

# Inicializar base de datos al startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("API iniciada correctamente")

# Endpoints principales

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {"message": "Immermex Dashboard API", "status": "active"}

@app.get("/api/kpis", response_model=KPIsResponse)
async def get_kpis(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    cliente: Optional[str] = Query(None, description="Filtrar por cliente"),
    agente: Optional[str] = Query(None, description="Filtrar por agente"),
    numero_pedido: Optional[str] = Query(None, description="Filtrar por número de pedido"),
    material: Optional[str] = Query(None, description="Filtrar por material"),
    mes: Optional[int] = Query(None, description="Filtrar por mes (1-12)"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db)
):
    """Obtiene KPIs principales del dashboard"""
    try:
        # Construir filtros
        filtros = FiltrosDashboard(
            fecha_inicio=datetime.fromisoformat(fecha_inicio) if fecha_inicio else None,
            fecha_fin=datetime.fromisoformat(fecha_fin) if fecha_fin else None,
            cliente=cliente,
            agente=agente,
            numero_pedido=numero_pedido,
            material=material,
            mes=mes,
            año=año
        )
        
        service = DashboardService(db)
        kpis = service.get_kpis(filtros)
        
        return KPIsResponse(**kpis)
        
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pedido/{numero_pedido}", response_model=PedidoDetalleResponse)
async def get_pedido_detalle(numero_pedido: str, db: Session = Depends(get_db)):
    """Obtiene detalles de un pedido específico"""
    try:
        service = DashboardService(db)
        detalle = service.get_pedido_detalle(numero_pedido)
        return detalle
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo detalle de pedido: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cliente/{cliente}", response_model=ClienteDetalleResponse)
async def get_cliente_detalle(cliente: str, db: Session = Depends(get_db)):
    """Obtiene detalles de un cliente específico"""
    try:
        service = DashboardService(db)
        detalle = service.get_cliente_detalle(cliente)
        return detalle
        
    except Exception as e:
        logger.error(f"Error obteniendo detalle de cliente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/aging")
async def get_grafico_aging(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos para gráfico de aging de cartera"""
    try:
        filtros = FiltrosDashboard(
            fecha_inicio=datetime.fromisoformat(fecha_inicio) if fecha_inicio else None,
            fecha_fin=datetime.fromisoformat(fecha_fin) if fecha_fin else None,
            cliente=cliente
        )
        
        service = DashboardService(db)
        grafico = service.get_grafico_aging(filtros)
        return grafico
        
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de aging: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/top-clientes")
async def get_grafico_top_clientes(
    limite: int = Query(10, description="Número de clientes a mostrar"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos para gráfico de top clientes"""
    try:
        filtros = FiltrosDashboard(
            fecha_inicio=datetime.fromisoformat(fecha_inicio) if fecha_inicio else None,
            fecha_fin=datetime.fromisoformat(fecha_fin) if fecha_fin else None
        )
        
        service = DashboardService(db)
        grafico = service.get_grafico_top_clientes(filtros, limite)
        return grafico
        
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de top clientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/consumo-material")
async def get_grafico_consumo_material(
    limite: int = Query(10, description="Número de materiales a mostrar"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos para gráfico de consumo por material"""
    try:
        filtros = FiltrosDashboard(
            fecha_inicio=datetime.fromisoformat(fecha_inicio) if fecha_inicio else None,
            fecha_fin=datetime.fromisoformat(fecha_fin) if fecha_fin else None
        )
        
        service = DashboardService(db)
        grafico = service.get_grafico_consumo_material(filtros, limite)
        return grafico
        
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de consumo de material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload", response_model=ArchivoUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Sube y procesa archivo Excel mensual"""
    try:
        # Validar tipo de archivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Crear registro de archivo
        archivo_record = ArchivoProcesado(
            nombre_archivo=file.filename,
            estado='en_proceso',
            mes=datetime.now().month,
            año=datetime.now().year
        )
        db.add(archivo_record)
        db.commit()
        db.refresh(archivo_record)
        
        # Guardar archivo temporalmente
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{archivo_record.id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Procesar archivo
            processor = ImmermexDataProcessor()
            master_df, kpis = processor.process_file(file_path)
            
            # Guardar datos en base de datos
            registros_procesados = await save_processed_data(master_df, db)
            
            # Actualizar registro de archivo
            archivo_record.estado = 'procesado'
            archivo_record.registros_procesados = registros_procesados
            db.commit()
            
            # Limpiar archivo temporal
            os.remove(file_path)
            
            return ArchivoUploadResponse(
                mensaje="Archivo procesado exitosamente",
                archivo_id=archivo_record.id,
                registros_procesados=registros_procesados,
                estado='procesado'
            )
            
        except Exception as e:
            # Actualizar registro con error
            archivo_record.estado = 'error'
            archivo_record.error_message = str(e)
            db.commit()
            
            # Limpiar archivo temporal
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.error(f"Error procesando archivo: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subiendo archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def save_processed_data(master_df: pd.DataFrame, db: Session) -> int:
    """Guarda datos procesados en la base de datos"""
    from database import Facturacion, Cobranza, CFDIRelacionado, Inventario
    
    registros_guardados = 0
    
    try:
        # Guardar facturación
        facturacion_data = master_df.to_dict('records')
        for record in facturacion_data:
            factura = Facturacion(**{k: v for k, v in record.items() if k in Facturacion.__table__.columns})
            db.add(factura)
            registros_guardados += 1
        
        db.commit()
        logger.info(f"Guardados {registros_guardados} registros de facturación")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando datos: {str(e)}")
        raise
    
    return registros_guardados

@app.get("/api/archivos")
async def get_archivos_procesados(
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):
    """Obtiene lista de archivos procesados"""
    try:
        archivos = db.query(ArchivoProcesado).offset(skip).limit(limit).all()
        return [
            {
                "id": archivo.id,
                "nombre_archivo": archivo.nombre_archivo,
                "fecha_procesamiento": archivo.fecha_procesamiento,
                "registros_procesados": archivo.registros_procesados,
                "estado": archivo.estado,
                "mes": archivo.mes,
                "año": archivo.año
            }
            for archivo in archivos
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
