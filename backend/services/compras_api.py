"""
API endpoints para gestión de compras
Incluye endpoints para importación desde OneDrive y consulta de datos
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

from services.compras_import_service import ComprasImportService
from models import BaseModel
from database_service_refactored import DatabaseService

logger = logging.getLogger(__name__)

# Crear router para compras
compras_router = APIRouter(prefix="/api/compras", tags=["compras"])

# Servicios
compras_service = ComprasImportService()
db_service = DatabaseService()

# Modelos Pydantic para compras
class CompraResponse(BaseModel):
    id: int
    fecha_compra: Optional[date]
    numero_factura: Optional[str]
    proveedor: Optional[str]
    concepto: Optional[str]
    categoria: Optional[str]
    subcategoria: Optional[str]
    cantidad: Optional[float]
    unidad: Optional[str]
    precio_unitario: Optional[float]
    subtotal: Optional[float]
    iva: Optional[float]
    total: Optional[float]
    moneda: Optional[str]
    forma_pago: Optional[str]
    dias_credito: Optional[int]
    fecha_vencimiento: Optional[date]
    fecha_pago: Optional[date]
    estado_pago: Optional[str]
    centro_costo: Optional[str]
    proyecto: Optional[str]
    notas: Optional[str]
    archivo_origen: Optional[str]
    mes: Optional[int]
    año: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ComprasSummaryResponse(BaseModel):
    total_compras: int
    total_monto: float
    monto_pagado: float
    monto_pendiente: float
    monto_vencido: float
    compras_pagadas: int
    compras_pendientes: int
    compras_vencidas: int

class ImportResultResponse(BaseModel):
    success: bool
    message: str
    files_processed: int
    records_imported: int
    files: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

@compras_router.get("/", response_model=List[CompraResponse])
async def get_compras(
    mes: Optional[int] = Query(None, description="Mes de las compras"),
    año: Optional[int] = Query(None, description="Año de las compras"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    estado_pago: Optional[str] = Query(None, description="Filtrar por estado de pago"),
    limit: int = Query(100, description="Límite de registros"),
    offset: int = Query(0, description="Offset para paginación")
):
    """Obtiene lista de compras con filtros opcionales"""
    try:
        query = """
            SELECT * FROM compras
            WHERE 1=1
        """
        
        params = []
        if mes:
            query += " AND mes = %s"
            params.append(mes)
        if año:
            query += " AND año = %s"
            params.append(año)
        if proveedor:
            query += " AND proveedor ILIKE %s"
            params.append(f"%{proveedor}%")
        if categoria:
            query += " AND categoria ILIKE %s"
            params.append(f"%{categoria}%")
        if estado_pago:
            query += " AND estado_pago = %s"
            params.append(estado_pago)
        
        query += " ORDER BY fecha_compra DESC, created_at DESC"
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        result = await db_service.execute_query(query, params)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/summary", response_model=ComprasSummaryResponse)
async def get_compras_summary(
    mes: Optional[int] = Query(None, description="Mes para el resumen"),
    año: Optional[int] = Query(None, description="Año para el resumen")
):
    """Obtiene resumen de compras"""
    try:
        summary = await compras_service.get_compras_summary(mes, año)
        return ComprasSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/proveedores")
async def get_proveedores():
    """Obtiene lista de proveedores únicos"""
    try:
        query = """
            SELECT DISTINCT proveedor, COUNT(*) as total_compras, SUM(total) as total_monto
            FROM compras
            WHERE proveedor IS NOT NULL AND proveedor != ''
            GROUP BY proveedor
            ORDER BY total_monto DESC
        """
        
        result = await db_service.execute_query(query)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/categorias")
async def get_categorias():
    """Obtiene lista de categorías únicas"""
    try:
        query = """
            SELECT DISTINCT categoria, COUNT(*) as total_compras, SUM(total) as total_monto
            FROM compras
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria
            ORDER BY total_monto DESC
        """
        
        result = await db_service.execute_query(query)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.post("/import/onedrive", response_model=ImportResultResponse)
async def import_from_onedrive(background_tasks: BackgroundTasks):
    """Importa compras desde OneDrive"""
    try:
        logger.info("Iniciando importación desde OneDrive")
        
        # Ejecutar importación en background
        result = await compras_service.import_compras_from_onedrive()
        
        return ImportResultResponse(**result)
        
    except Exception as e:
        logger.error(f"Error importando desde OneDrive: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.post("/sync/automatic", response_model=ImportResultResponse)
async def sync_automatic():
    """Sincronización automática de compras"""
    try:
        logger.info("Iniciando sincronización automática")
        
        result = await compras_service.sync_compras_automatic()
        
        return ImportResultResponse(**result)
        
    except Exception as e:
        logger.error(f"Error en sincronización automática: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/aging")
async def get_compras_aging():
    """Obtiene análisis de aging de compras pendientes"""
    try:
        query = """
            SELECT 
                CASE 
                    WHEN fecha_vencimiento IS NULL THEN 'Sin fecha'
                    WHEN fecha_vencimiento < CURRENT_DATE THEN 'Vencidas'
                    WHEN fecha_vencimiento <= CURRENT_DATE + INTERVAL '7 days' THEN 'Por vencer (7 días)'
                    WHEN fecha_vencimiento <= CURRENT_DATE + INTERVAL '30 days' THEN 'Por vencer (30 días)'
                    ELSE 'Futuras'
                END as categoria_vencimiento,
                COUNT(*) as cantidad_compras,
                SUM(total) as monto_total
            FROM compras
            WHERE estado_pago = 'pendiente'
            GROUP BY categoria_vencimiento
            ORDER BY 
                CASE categoria_vencimiento
                    WHEN 'Vencidas' THEN 1
                    WHEN 'Por vencer (7 días)' THEN 2
                    WHEN 'Por vencer (30 días)' THEN 3
                    WHEN 'Futuras' THEN 4
                    WHEN 'Sin fecha' THEN 5
                END
        """
        
        result = await db_service.execute_query(query)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo aging de compras: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/monthly-trend")
async def get_monthly_trend(
    año: int = Query(..., description="Año para el análisis de tendencias")
):
    """Obtiene tendencia mensual de compras"""
    try:
        query = """
            SELECT 
                mes,
                COUNT(*) as total_compras,
                SUM(total) as total_monto,
                SUM(CASE WHEN estado_pago = 'pagado' THEN total ELSE 0 END) as monto_pagado,
                SUM(CASE WHEN estado_pago = 'pendiente' THEN total ELSE 0 END) as monto_pendiente
            FROM compras
            WHERE año = %s
            GROUP BY mes
            ORDER BY mes
        """
        
        result = await db_service.execute_query(query, [año])
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo tendencia mensual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/top-proveedores")
async def get_top_proveedores(
    limit: int = Query(10, description="Número de proveedores a retornar"),
    año: Optional[int] = Query(None, description="Año para el análisis")
):
    """Obtiene top proveedores por monto"""
    try:
        query = """
            SELECT 
                proveedor,
                COUNT(*) as total_compras,
                SUM(total) as total_monto,
                AVG(total) as promedio_compra,
                MAX(fecha_compra) as ultima_compra
            FROM compras
            WHERE proveedor IS NOT NULL AND proveedor != ''
        """
        
        params = []
        if año:
            query += " AND año = %s"
            params.append(año)
        
        query += """
            GROUP BY proveedor
            ORDER BY total_monto DESC
            LIMIT %s
        """
        params.append(limit)
        
        result = await db_service.execute_query(query, params)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo top proveedores: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@compras_router.get("/status")
async def get_import_status():
    """Obtiene estado de la última importación"""
    try:
        query = """
            SELECT 
                ap.nombre_archivo,
                ap.fecha_procesamiento,
                ap.registros_procesados,
                ap.estado,
                ap.error_message,
                COUNT(c.id) as registros_importados
            FROM archivos_procesados ap
            LEFT JOIN compras c ON c.archivo_id = ap.id
            WHERE ap.algoritmo_usado = 'compras_import'
            GROUP BY ap.id, ap.nombre_archivo, ap.fecha_procesamiento, ap.registros_procesados, ap.estado, ap.error_message
            ORDER BY ap.fecha_procesamiento DESC
            LIMIT 10
        """
        
        result = await db_service.execute_query(query)
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de importación: {e}")
        raise HTTPException(status_code=500, detail=str(e))
