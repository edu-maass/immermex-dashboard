"""
API REST para Immermex Dashboard con persistencia en base de datos
Integra el procesador avanzado con almacenamiento persistente

VERCEL DEPLOYMENT VERIFICATION - 2025-10-03 21:05
UPDATED CODE RUNNING - SUPABASE POSTGRESQL CONFIGURED
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
import hashlib
from typing import List, Optional

# Imports locales
from database import get_db, init_db, ArchivoProcesado
from database_service import DatabaseService
try:
    from utils import setup_logging, handle_api_error, FileProcessingError, DatabaseError
except ImportError:
    # Para desarrollo local
    from .utils import setup_logging, handle_api_error, FileProcessingError, DatabaseError
from datetime import datetime
from data_processor import process_immermex_file_advanced
from fastapi import HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

# Configurar logging
logger = setup_logging()

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API (Con Base de Datos)",
    description="API REST para dashboard de indicadores financieros con persistencia en base de datos",
    version="2.0.0"
)

# Pedidos endpoints will be added after middleware setup

# Configurar CORS dinámicamente según el entorno
def get_cors_origins():
    """Obtiene los orígenes CORS según el entorno"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return [
            "https://edu-maass.github.io"
        ]
    else:
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://edu-maass.github.io"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agregar compresión GZIP para optimizar el ancho de banda
app.add_middleware(GZipMiddleware, minimum_size=1000)

# PEDIDOS ENDPOINTS - Now Active

# Endpoint OPTIONS genérico para CORS preflight
@app.options("/{path:path}")
async def options_handler(path: str):
    """Maneja solicitudes OPTIONS para CORS preflight"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "https://edu-maass.github.io",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Fully commented out startup event

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {
        "message": "Immermex Dashboard API (Con Base de Datos) - SUPABASE POSTGRESQL - PEDIDOS ENDPOINTS ACTIVE",
        "status": "active",
        "version": "2.0.0",
        "features": ["persistencia_db", "procesamiento_avanzado", "filtros_dinamicos"],
        "database": "supabase_postgresql"
    }

@app.get("/api/simple-health")
async def simple_health():
    """Endpoint simple de salud sin base de datos"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "API funcionando correctamente"
    }

@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Endpoint de verificación de salud con base de datos"""
    try:
        # Verificar conexión a base de datos
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        
        # Obtener resumen de datos
        db_service = DatabaseService(db)
        data_summary = db_service.get_data_summary()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "data_available": data_summary.get("has_data", False),
            "data_summary": data_summary
        }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/kpis")
async def get_kpis(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
    db: Session = Depends(get_db)
):
    """Obtiene KPIs principales del dashboard con filtros opcionales"""
    try:
        db_service = DatabaseService(db)

        # Preparar filtros
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if pedidos:
            pedidos_list = [p.strip() for p in pedidos.split(',') if p.strip()]
            filtros['pedidos'] = pedidos_list

        kpis = db_service.calculate_kpis(filtros)
        return kpis

    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/disponibles")
async def get_filtros_disponibles(db: Session = Depends(get_db)):
    """Obtiene opciones disponibles para filtros"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros
    except Exception as e:
        logger.error(f"Error obteniendo filtros disponibles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/pedidos")
async def get_pedidos_filtro(db: Session = Depends(get_db)):
    """Obtiene lista de pedidos para filtros (compatible con frontend actual)"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros.get("pedidos", [])
    except Exception as e:
        logger.error(f"Error obteniendo pedidos para filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Test route right after a working endpoint
@app.get("/api/test-after-filtros")
def test_after_filtros():
    """Test route after filtros endpoints"""
    return {"message": "test after filtros works"}

@app.get("/api/filtros/clientes")
async def get_clientes_filtro(db: Session = Depends(get_db)):
    """Obtiene lista de clientes para filtros"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros.get("clientes", [])
    except Exception as e:
        logger.error(f"Error obteniendo clientes para filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/materiales")
async def get_materiales_filtro(db: Session = Depends(get_db)):
    """Obtiene lista de materiales para filtros"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros.get("materiales", [])
    except Exception as e:
        logger.error(f"Error obteniendo materiales para filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filtros/aplicar")
async def aplicar_filtros(
    mes: Optional[int] = Query(None),
    año: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Aplica filtros de mes y año (compatible con frontend actual)"""
    try:
        # Los filtros se aplican automáticamente en get_kpis
        return {
            "message": "Filtros aplicados correctamente",
            "filtros": {"mes": mes, "año": año}
        }
    except Exception as e:
        logger.error(f"Error aplicando filtros: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filtros/pedidos/aplicar")
async def aplicar_filtros_pedido(
    pedidos: List[str] = Query([]),
    db: Session = Depends(get_db)
):
    """Aplica filtros de pedidos (compatible con frontend actual)"""
    try:
        # Los filtros se aplican automáticamente en get_kpis
        return {
            "message": f"Filtros de pedidos aplicados correctamente",
            "pedidos_aplicados": len(pedidos),
            "filtros": {"pedidos": pedidos}
        }
    except Exception as e:
        logger.error(f"Error aplicando filtros de pedidos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    reemplazar_datos: bool = Query(True, description="Si true, reemplaza todos los datos existentes"),
    db: Session = Depends(get_db)
):
    """Endpoint para subir archivos Excel con persistencia en base de datos"""
    try:
        # Validar tipo de archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise FileProcessingError("Solo se permiten archivos Excel (.xlsx, .xls)")
        
        logger.info(f"Procesando archivo con persistencia: {file.filename}")
        
        # Leer contenido del archivo
        contents = await file.read()
        
        # Validar tamaño del archivo (máximo 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise FileProcessingError("El archivo es demasiado grande. Máximo 10MB permitido.")
        
        # Procesar archivo directamente desde memoria (compatible con Vercel)
        try:
            import io
            from data_processor import process_excel_from_bytes
            
            logger.info(f"Procesando archivo desde memoria: {file.filename}")
            logger.info(f"Tamaño del archivo: {len(contents)} bytes")
            
            # Procesar usando la nueva función desde bytes
            processed_data_dict, kpis = process_excel_from_bytes(contents, file.filename)
            logger.info(f"Datos procesados exitosamente. Claves: {list(processed_data_dict.keys())}")
            
            # Verificar estructura de datos procesados
            for key, data in processed_data_dict.items():
                logger.info(f"{key}: {len(data)} registros")
                if len(data) > 0:
                    logger.info(f"  Primer registro de {key}: {list(data[0].keys()) if isinstance(data, list) else 'No es lista'}")
            
            # Preparar información del archivo
            archivo_info = {
                "nombre": file.filename,  # Key expected by _create_archivo_record
                "tamaño": len(contents),   # Key expected by _create_archivo_record
                "nombre_archivo": file.filename,
                "tipo_archivo": file.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "contenido": contents.decode('utf-8', errors='ignore'),
                "reemplazar_datos": reemplazar_datos
            }
            
            # Guardar en base de datos
            logger.info("Iniciando guardado en base de datos...")
            db_service = DatabaseService(db)
            result = db_service.save_processed_data(processed_data_dict, archivo_info)
            
            # Verificar si hubo error en el guardado
            if not result.get("success", True):
                error_msg = result.get("error", "Error desconocido al guardar datos")
                logger.error(f"Error guardando datos: {error_msg}")
                raise Exception(f"Error guardando datos: {error_msg}")
            
            logger.info(f"Guardado completado: {result}")
            
            logger.info(f"Archivo procesado y guardado exitosamente: {file.filename}")
            
            return {
                "mensaje": "Archivo procesado y guardado exitosamente en base de datos",
                "nombre_archivo": file.filename,
                "archivo_id": result["archivo_id"],
                "total_registros": result["registros_procesados"],
                "fecha_procesamiento": datetime.now().isoformat(),
                "estado": "procesado",
                "algoritmo": "memory_processing_with_persistence",
                "desglose": {
                    "facturas": result["desglose"]["facturas"],
                    "cobranzas": result["desglose"]["cobranzas"],
                    "anticipos": result["desglose"]["anticipos"],
                    "pedidos": result["desglose"]["pedidos"],
                    "compras": result["desglose"].get("compras", 0)
                },
                "caracteristicas": {
                    "deteccion_automatica_encabezados": True,
                    "mapeo_flexible_columnas": True,
                    "validacion_datos": True,
                    "calculo_relaciones": True,
                    "limpieza_robusta": True,
                    "persistencia_base_datos": True,
                    "filtros_dinamicos": True
                }
            }
            
        finally:
            # No hay archivos temporales que limpiar (procesamiento en memoria)
            pass
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/compras-v2")
async def upload_compras_v2_file(
    file: UploadFile = File(...),
    reemplazar_datos: bool = Query(True, description="Si true, reemplaza todos los datos existentes")
):
    """Endpoint específico para subir archivos Excel de compras_v2 - SISTEMA COMPRAS_V2"""
    try:
        logger.info("🚀🚀🚀 SISTEMA COMPRAS_V2 ACTIVADO 🚀🚀🚀")
        logger.info(f"Procesando archivo: {file.filename}")
        
        # Validación básica del archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Leer contenido para validar tamaño
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 10MB permitido.")
        
        logger.info(f"Archivo leído: {len(content)} bytes")
        
        # Usar el nuevo servicio especializado de compras_v2
        from compras_v2_upload_service import ComprasV2UploadService
        
        service = ComprasV2UploadService()
        result = service.upload_compras_file(content, file.filename, reemplazar_datos)
        
        if result.get("success"):
            logger.info(f"✅ Upload exitoso: {result['compras_guardadas']} compras, {result['materiales_guardados']} materiales")
            return {
                "mensaje": "Archivo de compras procesado y guardado exitosamente con sistema compras_v2",
                "nombre_archivo": file.filename,
                "archivo_id": result["archivo_id"],
                "compras_guardadas": result["compras_guardadas"],
                "materiales_guardados": result["materiales_guardados"],
                "total_procesados": result["total_procesados"],
                "kpis": result.get("kpis", {}),
                "estado": "procesado",
                "servicio_usado": "ComprasV2UploadService",
                "sistema": "compras_v2"
            }
        else:
            logger.error(f"ERROR: Upload falló: {result.get('error', 'Error desconocido')}")
            raise HTTPException(status_code=500, detail=f"Error procesando archivo: {result.get('error', 'Error desconocido')}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint de compras_v2: {str(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archivos")
async def get_archivos_procesados(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Obtiene lista de archivos procesados"""
    try:
        archivos = db.query(ArchivoProcesado).order_by(
            ArchivoProcesado.fecha_procesamiento.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": archivo.id,
                "nombre_archivo": archivo.nombre_archivo,
                "fecha_procesamiento": archivo.fecha_procesamiento.isoformat(),
                "registros_procesados": archivo.registros_procesados,
                "estado": archivo.estado,
                "error_message": archivo.error_message,
                "mes": archivo.mes,
                "año": archivo.año,
                "tamaño_archivo": archivo.tamaño_archivo,
                "algoritmo_usado": archivo.algoritmo_usado
            }
            for archivo in archivos
        ]
    except Exception as e:
        logger.error(f"Error obteniendo archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/archivos/{archivo_id}")
async def eliminar_archivo(
    archivo_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un archivo y todos sus datos asociados"""
    try:
        # Verificar que el archivo existe
        archivo = db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo_id).first()
        if not archivo:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        # Limpiar datos asociados
        db_service = DatabaseService(db)
        db_service._clear_existing_data()
        
        # Eliminar archivo
        db.delete(archivo)
        db.commit()
        
        return {
            "mensaje": f"Archivo {archivo.nombre_archivo} y todos sus datos han sido eliminados",
            "archivo_id": archivo_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/summary")
async def get_data_summary(db: Session = Depends(get_db)):
    """Obtiene resumen de datos disponibles"""
    try:
        db_service = DatabaseService(db)
        summary = db_service.get_data_summary()
        return summary
    except Exception as e:
        logger.error(f"Error obteniendo resumen de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/aging")
async def get_grafico_aging(
    mes: Optional[int] = Query(None),
    año: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos para gráfico de aging de cartera"""
    try:
        db_service = DatabaseService(db)
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        
        kpis = db_service.calculate_kpis(filtros)
        aging = kpis.get("aging_cartera", {})
        
        return {
            "labels": list(aging.keys()),
            "data": list(aging.values()),
            "titulo": "Aging de Cartera"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de aging: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/top-clientes")
async def get_grafico_top_clientes(
    limite: int = Query(10, ge=1, le=50),
    mes: Optional[int] = Query(None),
    año: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos para gráfico de top clientes"""
    try:
        db_service = DatabaseService(db)
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        
        kpis = db_service.calculate_kpis(filtros)
        clientes = kpis.get("top_clientes", {})
        
        # Limitar resultados
        clientes_limitados = dict(list(clientes.items())[:limite])
        
        return {
            "labels": list(clientes_limitados.keys()),
            "data": list(clientes_limitados.values()),
            "titulo": f"Top {limite} Clientes por Facturación"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de top clientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/consumo-material")
async def get_grafico_consumo_material(
    limite: int = Query(10, ge=1, le=50),
    mes: Optional[int] = Query(None),
    año: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtiene datos para gráfico de consumo por material"""
    try:
        db_service = DatabaseService(db)
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        
        kpis = db_service.calculate_kpis(filtros)
        materiales = kpis.get("consumo_material", {})
        
        # Limitar resultados
        materiales_limitados = dict(list(materiales.items())[:limite])
        
        return {
            "labels": list(materiales_limitados.keys()),
            "data": list(materiales_limitados.values()),
            "titulo": f"Top {limite} Materiales por Consumo"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de consumo de material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debug/upload")
async def debug_upload(file: UploadFile = File(...)):
    """Endpoint de debugging temporal para diagnosticar problemas de upload"""
    try:
        logger.info(f"🔍 DEBUG: Procesando archivo: {file.filename}")
        
        # Validar tipo de archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            return {"error": "Solo se permiten archivos Excel (.xlsx, .xls)", "status": "validation_error"}
        
        # Leer contenido
        contents = await file.read()
        logger.info(f"🔍 DEBUG: Archivo leído: {len(contents)} bytes")
        
        # Validar tamaño
        if len(contents) > 10 * 1024 * 1024:
            return {"error": "Archivo demasiado grande", "status": "size_error"}
        
        # Probar procesamiento
        try:
            from data_processor import process_excel_from_bytes
            processed_data_dict, kpis = process_excel_from_bytes(contents, file.filename)
            logger.info(f"🔍 DEBUG: Procesamiento exitoso")
            
            return {
                "status": "success",
                "filename": file.filename,
                "size": len(contents),
                "processed_keys": list(processed_data_dict.keys()),
                "record_counts": {key: len(data) for key, data in processed_data_dict.items()},
                "kpis": kpis,
                "first_record_keys": {
                    key: list(data[0].keys()) if len(data) > 0 else [] 
                    for key, data in processed_data_dict.items()
                }
            }
        except Exception as e:
            logger.error(f"🔍 DEBUG: Error en procesamiento: {str(e)}")
            return {"error": f"Error en procesamiento: {str(e)}", "status": "processing_error"}
            
    except Exception as e:
        logger.error(f"🔍 DEBUG: Error general: {str(e)}")
        return {"error": f"Error general: {str(e)}", "status": "general_error"}

@app.get("/api/debug/test")
async def debug_test():
    """Endpoint simple para verificar que la API está funcionando"""
    try:
        logger.info("🔍 DEBUG: Test endpoint llamado")
        return {
            "status": "success",
            "message": "API funcionando correctamente",
            "timestamp": datetime.now().isoformat(),
            "version": "refactored"
        }
    except Exception as e:
        logger.error(f"🔍 DEBUG: Error en test: {str(e)}")
        return {"error": str(e), "status": "error"}

@app.post("/api/debug/simple-upload")
async def debug_simple_upload(file: UploadFile = File(...)):
    """Endpoint de upload simplificado para debugging"""
    try:
        logger.info(f"🔍 DEBUG SIMPLE: Archivo recibido: {file.filename}")
        
        # Validaciones básicas
        if not file.filename:
            raise FileProcessingError("No filename provided")
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise FileProcessingError("Invalid file type")
        
        contents = await file.read()
        logger.info(f"🔍 DEBUG SIMPLE: Archivo leído: {len(contents)} bytes")
        
        if len(contents) == 0:
            raise FileProcessingError("Empty file")
        
        if len(contents) > 10 * 1024 * 1024:
            raise FileProcessingError("File too large")
        
        return {
            "status": "success",
            "filename": file.filename,
            "size": len(contents),
            "message": "Archivo recibido correctamente"
        }
        
    except FileProcessingError as e:
        logger.error(f"🔍 DEBUG SIMPLE: Error de validación: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"🔍 DEBUG SIMPLE: Error general: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debug/upload-no-decorator")
async def debug_upload_no_decorator(file: UploadFile = File(...)):
    """Endpoint de upload sin decorador para debugging"""
    logger.info(f"🔍 DEBUG NO DECORATOR: Archivo recibido: {file.filename}")
    
    # Validaciones básicas
    if not file.filename:
        return {"error": "No filename provided", "status": "error"}
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return {"error": "Invalid file type", "status": "error"}
    
    contents = await file.read()
    logger.info(f"🔍 DEBUG NO DECORATOR: Archivo leído: {len(contents)} bytes")
    
    if len(contents) == 0:
        return {"error": "Empty file", "status": "error"}
    
    if len(contents) > 10 * 1024 * 1024:
        return {"error": "File too large", "status": "error"}
    
    return {
        "status": "success",
        "filename": file.filename,
        "size": len(contents),
        "message": "Archivo recibido correctamente sin decorador"
    }

@app.get("/api/system/performance")
async def get_system_performance(db: Session = Depends(get_db)):
    """Endpoint para monitorear el rendimiento del sistema"""
    try:
        from utils.cache import cache
        import psutil
        import time
        
        # Estadísticas de caché
        cache_stats = cache.get_stats()
        
        # Estadísticas de memoria
        try:
            memory_stats = {
                "total_memory_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
                "available_memory_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2),
                "memory_usage_percent": psutil.virtual_memory().percent
            }
        except Exception:
            # Fallback si psutil no está disponible
            memory_stats = {
                "total_memory_mb": 0,
                "available_memory_mb": 0,
                "memory_usage_percent": 0,
                "note": "Memory stats not available in this environment"
            }
        
        # Estadísticas de base de datos
        db_service = DatabaseService(db)
        data_summary = db_service.get_data_summary()
        
        return {
            "timestamp": time.time(),
            "cache": cache_stats,
            "memory": memory_stats,
            "database": {
                "has_data": data_summary.get("has_data", False),
                "total_records": sum(data_summary.get("conteos", {}).values())
            },
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas de rendimiento: {str(e)}")
        return {"error": str(e), "status": "error"}

@app.post("/api/system/cache/clear")
async def clear_cache():
    """Endpoint para limpiar el caché del sistema"""
    try:
        from utils.cache import invalidate_data_cache
        deleted_count = invalidate_data_cache()
        return {
            "success": True,
            "message": f"Cache cleared successfully",
            "entries_deleted": deleted_count
        }
    except Exception as e:
        logger.error(f"Error limpiando caché: {str(e)}")
        return {"error": str(e), "status": "error"}

@app.get("/api/data/paginated")
async def get_paginated_data(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(50, ge=1, le=100, description="Elementos por página"),
    table: str = Query("facturacion", description="Tabla a consultar (facturacion, cobranza, pedidos)"),
    db: Session = Depends(get_db)
):
    """Endpoint optimizado para obtener datos con paginación"""
    try:
        from utils.pagination import paginate, get_pagination_params
        from database import Facturacion, Cobranza, Pedido
        
        # Validar parámetros
        page, per_page = get_pagination_params(page, per_page)
        
        # Seleccionar tabla
        if table == "facturacion":
            query = db.query(Facturacion).order_by(Facturacion.fecha_factura.desc())
        elif table == "cobranza":
            query = db.query(Cobranza).order_by(Cobranza.fecha_pago.desc())
        elif table == "pedidos":
            query = db.query(Pedido).order_by(Pedido.fecha_factura.desc())
        else:
            raise HTTPException(status_code=400, detail="Tabla no válida")
        
        # Paginar resultados
        result = paginate(query, page, per_page)
        
        # Convertir a diccionario
        items = []
        for item in result.items:
            if hasattr(item, '__dict__'):
                item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                items.append(item_dict)
        
        return {
            "items": items,
            "pagination": {
                "page": result.page,
                "per_page": result.per_page,
                "total": result.total,
                "pages": result.pages,
                "has_prev": result.has_prev,
                "has_next": result.has_next,
                "prev_num": result.prev_num,
                "next_num": result.next_num
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos paginados: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DE COMPRAS_V2 ====================

@app.get("/api/compras-v2/kpis")
async def get_compras_v2_kpis(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    material: Optional[str] = Query(None, description="Filtrar por material")
):
    """Obtiene KPIs principales de compras_v2 con filtros opcionales"""
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Iniciando cálculo de KPIs de compras_v2 - filtros: {mes}, {año}, {proveedor}, {material}")
        
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        
        # Preparar filtros
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if proveedor:
            filtros['proveedor'] = proveedor
        if material:
            filtros['material'] = material
        
        kpis = service.calculate_kpis(filtros)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"KPIs de compras_v2 calculados exitosamente en {execution_time:.2f} segundos")
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error obteniendo KPIs de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/debug-precios")
async def debug_precios():
    """Endpoint de debug para verificar datos de precios"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        # Verificar datos en compras_v2_materiales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_materiales,
                COUNT(CASE WHEN pu_divisa IS NOT NULL AND pu_divisa > 0 THEN 1 END) as con_precio_divisa,
                COUNT(CASE WHEN pu_mxn IS NOT NULL AND pu_mxn > 0 THEN 1 END) as con_precio_mxn,
                AVG(pu_divisa) as avg_divisa,
                AVG(pu_mxn) as avg_mxn
            FROM compras_v2_materiales
        """)
        materiales_stats = cursor.fetchone()
        
        # Verificar JOIN entre compras_v2 y materiales
        cursor.execute("""
            SELECT COUNT(*) as total_joins
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_id
            WHERE c2.fecha_pedido IS NOT NULL
        """)
        joins_count = cursor.fetchone()
        
        # Verificar fechas disponibles
        cursor.execute("""
            SELECT 
                MIN(fecha_pedido) as fecha_min,
                MAX(fecha_pedido) as fecha_max,
                COUNT(DISTINCT DATE_TRUNC('month', fecha_pedido)) as meses_distintos
            FROM compras_v2
            WHERE fecha_pedido IS NOT NULL
        """)
        fechas_stats = cursor.fetchone()
        
        cursor.close()
        
        return {
            "success": True,
            "materiales_stats": {
                "total_materiales": materiales_stats['total_materiales'],
                "con_precio_divisa": materiales_stats['con_precio_divisa'],
                "con_precio_mxn": materiales_stats['con_precio_mxn'],
                "avg_divisa": float(materiales_stats['avg_divisa']) if materiales_stats['avg_divisa'] else 0,
                "avg_mxn": float(materiales_stats['avg_mxn']) if materiales_stats['avg_mxn'] else 0
            },
            "joins_count": joins_count['total_joins'],
            "fechas_stats": {
                "fecha_min": fechas_stats['fecha_min'].isoformat() if fechas_stats['fecha_min'] else None,
                "fecha_max": fechas_stats['fecha_max'].isoformat() if fechas_stats['fecha_max'] else None,
                "meses_distintos": fechas_stats['meses_distintos']
            }
        }
        
    except Exception as e:
        logger.error(f"Error en debug precios: {str(e)}")
        return {"error": str(e)}

@app.get("/api/compras-v2/debug-pagos")
async def debug_pagos():
    """Endpoint de debug para verificar datos de pagos"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        # Verificar datos de pagos
        cursor.execute("""
            SELECT 
                COUNT(*) as total_compras,
                COUNT(CASE WHEN fecha_pago_factura IS NOT NULL THEN 1 END) as compras_pagadas,
                COUNT(CASE WHEN fecha_pago_factura IS NULL THEN 1 END) as compras_pendientes,
                MIN(fecha_pago_factura) as primer_pago,
                MAX(fecha_pago_factura) as ultimo_pago
            FROM compras_v2
        """)
        pagos_stats = cursor.fetchone()
        
        # Verificar fechas de pago por semana
        cursor.execute("""
            SELECT 
                DATE_TRUNC('week', fecha_pago_factura) as semana,
                COUNT(*) as pagos_semana
            FROM compras_v2
            WHERE fecha_pago_factura IS NOT NULL
            GROUP BY DATE_TRUNC('week', fecha_pago_factura)
            ORDER BY semana DESC
            LIMIT 5
        """)
        pagos_semanales = cursor.fetchall()
        
        cursor.close()
        
        return {
            "success": True,
            "pagos_stats": {
                "total_compras": pagos_stats['total_compras'],
                "compras_pagadas": pagos_stats['compras_pagadas'],
                "compras_pendientes": pagos_stats['compras_pendientes'],
                "primer_pago": pagos_stats['primer_pago'].isoformat() if pagos_stats['primer_pago'] else None,
                "ultimo_pago": pagos_stats['ultimo_pago'].isoformat() if pagos_stats['ultimo_pago'] else None
            },
            "pagos_semanales": [
                {
                    "semana": row['semana'].isoformat() if row['semana'] else None,
                    "pagos": row['pagos_semana']
                } for row in pagos_semanales
            ]
        }
        
    except Exception as e:
        logger.error(f"Error en debug pagos: {str(e)}")
        return {"error": str(e)}

@app.get("/api/compras-v2/debug-relacion")
async def debug_relacion():
    """Endpoint de debug para verificar relación entre compras_v2 y materiales"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        # Verificar IDs en compras_v2
        cursor.execute("SELECT id, imi FROM compras_v2 ORDER BY id LIMIT 5")
        compras_ids = cursor.fetchall()
        
        # Verificar IDs en compras_v2_materiales
        cursor.execute("SELECT compra_id FROM compras_v2_materiales ORDER BY compra_id LIMIT 5")
        materiales_compra_ids = cursor.fetchall()
        
        # Verificar si hay overlap
        cursor.execute("""
            SELECT COUNT(*) as overlap_count
            FROM compras_v2 c2
            WHERE EXISTS (SELECT 1 FROM compras_v2_materiales c2m WHERE c2m.compra_id = c2.imi)
        """)
        overlap = cursor.fetchone()
        
        # Verificar materiales sin compra
        cursor.execute("""
            SELECT COUNT(*) as materiales_sin_compra
            FROM compras_v2_materiales c2m
            WHERE NOT EXISTS (SELECT 1 FROM compras_v2 c2 WHERE c2.imi = c2m.compra_id)
        """)
        materiales_sin_compra = cursor.fetchone()
        
        cursor.close()
        
        return {
            "success": True,
            "compras_ids": [{"id": row['id'], "imi": row['imi']} for row in compras_ids],
            "materiales_compra_ids": [row['compra_id'] for row in materiales_compra_ids],
            "overlap_count": overlap['overlap_count'],
            "materiales_sin_compra": materiales_sin_compra['materiales_sin_compra']
        }
        
    except Exception as e:
        logger.error(f"Error en debug relacion: {str(e)}")
        return {"error": str(e)}

@app.get("/api/compras-v2/debug")
async def debug_compras_v2():
    """Endpoint de debug para verificar estructura de base de datos"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%compras%'
        """)
        tables = cursor.fetchall()
        
        # Verificar estructura de compras_v2 si existe
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        cursor.close()
        
        return {
            "success": True,
            "tables": [t[0] for t in tables],
            "compras_v2_columns": [{"name": c[0], "type": c[1]} for c in columns]
        }
        
    except Exception as e:
        logger.error(f"Error en debug: {str(e)}")
        return {"error": str(e)}

@app.get("/api/compras-v2/test")
async def test_compras_v2_data():
    """Endpoint de prueba para verificar datos de compras_v2"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        
        # Prueba directa sin filtros
        conn = service.get_connection()
        if not conn:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        # Probar consulta simple
        cursor.execute("SELECT COUNT(*) FROM compras_v2")
        count_result = cursor.fetchone()
        count = count_result[0] if count_result else 0
        
        # Probar consulta con campos específicos
        cursor.execute("SELECT id, imi, proveedor FROM compras_v2 LIMIT 3")
        sample_data = cursor.fetchall()
        
        cursor.close()
        
        # Prueba con el método simple que funciona
        compras = service.get_compras_simple(limit=5)
        
        return {
            "success": True,
            "count_direct": count,
            "sample_data": sample_data,
            "count_method": len(compras),
            "compras": compras[:2] if compras else []
        }
        
    except Exception as e:
        logger.error(f"Error en test: {str(e)}")
        return {"error": str(e)}

@app.get("/api/compras-v2/data")
async def get_compras_v2_data(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    material: Optional[str] = Query(None, description="Filtrar por material"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """Obtiene datos de compras_v2 con filtros opcionales y paginación"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        
        # Preparar filtros
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if proveedor:
            filtros['proveedor'] = proveedor
        if material:
            filtros['material'] = material
        
        compras = service.get_compras_simple(limit=limit, offset=offset)
        total_count = service.get_compras_count(filtros)
        
        return {
            "success": True,
            "compras": compras,
            "total_compras": total_count,
            "limit": limit,
            "offset": offset,
            "filtros_aplicados": filtros
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/materiales/{imi}")
async def get_materiales_by_compra(imi: int):
    """Obtiene materiales de una compra específica por IMI"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        materiales = service.get_materiales_by_compra(imi)
        
        return {
            "success": True,
            "compra_imi": imi,
            "materiales": materiales,
            "total_materiales": len(materiales)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo materiales para compra {imi}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/evolucion-precios")
async def get_compras_v2_evolucion_precios(
    material: Optional[str] = Query(None, description="Filtrar por material"),
    moneda: str = Query("USD", description="Moneda para mostrar precios (USD/MXN)")
):
    """Obtiene evolución mensual de precios por kg para compras_v2"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        
        filtros = {}
        if material:
            filtros['material'] = material
        
        evolucion = service.get_evolucion_precios(filtros, moneda)
        return evolucion
        
    except Exception as e:
        logger.error(f"Error obteniendo evolución de precios de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/flujo-pagos")
async def get_compras_v2_flujo_pagos(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    material: Optional[str] = Query(None, description="Filtrar por material"),
    moneda: str = Query("USD", description="Moneda para mostrar (USD o MXN)")
):
    """Obtiene flujo de pagos de compras_v2 por semana"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if proveedor:
            filtros['proveedor'] = proveedor
        if material:
            filtros['material'] = material
        
        # Validar moneda
        if moneda not in ['USD', 'MXN']:
            moneda = 'USD'
        
        flujo = service.get_flujo_pagos(filtros, moneda)
        return flujo
        
    except Exception as e:
        logger.error(f"Error obteniendo flujo de pagos de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/top-proveedores")
async def get_compras_v2_top_proveedores(
    limite: int = Query(10, description="Número máximo de proveedores a retornar"),
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db)
):
    """Obtiene top proveedores por monto de compras_v2"""
    try:
        db_service = DatabaseService(db)

        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año

        result = db_service.get_top_proveedores_compras_v2(limite, filtros)
        return result

    except Exception as e:
        logger.error(f"Error obteniendo top proveedores de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/compras-por-material")
async def get_compras_v2_por_material(
    limite: int = Query(10, description="Número máximo de materiales a retornar"),
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    db: Session = Depends(get_db)
):
    """Obtiene compras agrupadas por material en compras_v2"""
    try:
        db_service = DatabaseService(db)

        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if proveedor:
            filtros['proveedor'] = proveedor

        result = db_service.get_compras_por_material_v2(limite, filtros)
        return result

    except Exception as e:
        logger.error(f"Error obteniendo compras por material de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/materiales")
async def get_compras_v2_materiales(db: Session = Depends(get_db)):
    """Obtiene lista de materiales disponibles en compras_v2"""
    try:
        db_service = DatabaseService(db)
        result = db_service.get_materiales_compras_v2()
        return result

    except Exception as e:
        logger.error(f"Error obteniendo materiales de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/proveedores")
async def get_compras_v2_proveedores(db: Session = Depends(get_db)):
    """Obtiene lista de proveedores disponibles en compras_v2"""
    try:
        db_service = DatabaseService(db)
        result = db_service.get_proveedores_compras_v2()
        return result

    except Exception as e:
        logger.error(f"Error obteniendo proveedores de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/aging-cuentas-pagar")
async def get_compras_v2_aging_cuentas_pagar(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    material: Optional[str] = Query(None, description="Filtrar por material")
):
    """Obtiene aging de cuentas por pagar para compras_v2"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if proveedor:
            filtros['proveedor'] = proveedor
        if material:
            filtros['material'] = material
        
        aging = service.get_aging_cuentas_pagar(filtros)
        return aging
        
    except Exception as e:
        logger.error(f"Error obteniendo aging de cuentas por pagar de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/materiales")
async def get_compras_v2_materiales():
    """Obtiene lista de materiales disponibles en compras_v2"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        materiales = service.get_materiales()
        return materiales
        
    except Exception as e:
        logger.error(f"Error obteniendo materiales de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/proveedores")
async def get_compras_v2_proveedores():
    """Obtiene lista de proveedores únicos de compras_v2"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        proveedores = service.get_proveedores()
        return proveedores
        
    except Exception as e:
        logger.error(f"Error obteniendo proveedores de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras-v2/anios-disponibles")
async def get_compras_v2_anios_disponibles():
    """Obtiene lista de años disponibles en compras_v2"""
    try:
        from compras_v2_service import ComprasV2Service
        
        service = ComprasV2Service()
        años = service.get_años_disponibles()
        return años
        
    except Exception as e:
        logger.error(f"Error obteniendo años disponibles de compras_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compras-v2/update-fechas-estimadas")
async def update_fechas_estimadas():
    """Actualiza las fechas estimadas para todos los registros existentes"""
    try:
        from compras_v2_service import ComprasV2Service
        from datetime import timedelta
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            logger.error("No se pudo conectar a la base de datos")
            raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")
        
        cursor = conn.cursor()
        
        # Verificar si la columna fecha_planta_estimada existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2' 
            AND column_name = 'fecha_planta_estimada'
        """)
        
        column_exists = cursor.fetchone()
        
        if not column_exists:
            logger.info("Agregando columna fecha_planta_estimada...")
            cursor.execute("""
                ALTER TABLE compras_v2 
                ADD COLUMN fecha_planta_estimada DATE
            """)
            conn.commit()
            logger.info("Columna fecha_planta_estimada agregada exitosamente")
        
        # Obtener todos los registros que necesitan actualización
        cursor.execute("""
            SELECT 
                imi, 
                proveedor, 
                fecha_pedido,
                fecha_salida_estimada,
                fecha_arribo_estimada,
                fecha_planta_estimada
            FROM compras_v2 
            WHERE fecha_pedido IS NOT NULL
            ORDER BY imi
        """)
        
        records = cursor.fetchall()
        
        if not records:
            cursor.close()
            conn.close()
            return {"message": "No se encontraron registros para actualizar", "updated": 0, "skipped": 0}
        
        logger.info(f"Encontrados {len(records)} registros para procesar")
        
        # Obtener datos de proveedores para cálculos
        cursor.execute("""
            SELECT 
                nombre,
                promedio_dias_produccion,
                promedio_dias_transporte_maritimo
            FROM proveedores
        """)
        
        proveedores_data = {}
        for row in cursor.fetchall():
            proveedores_data[row[0]] = {
                'promedio_dias_produccion': float(row[1] or 0.0),
                'promedio_dias_transporte_maritimo': float(row[2] or 0.0)
            }
        
        logger.info(f"Datos de {len(proveedores_data)} proveedores cargados")
        
        # Procesar cada registro
        updated_count = 0
        skipped_count = 0
        
        for record in records:
            imi = record['imi']
            proveedor = record['proveedor']
            fecha_pedido = record['fecha_pedido']
            fecha_salida_actual = record['fecha_salida_estimada']
            fecha_arribo_actual = record['fecha_arribo_estimada']
            fecha_planta_actual = record['fecha_planta_estimada']
            
            # Obtener datos del proveedor
            proveedor_data = proveedores_data.get(proveedor, {
                'promedio_dias_produccion': 0.0,
                'promedio_dias_transporte_maritimo': 0.0
            })
            
            # Calcular fechas estimadas
            fecha_salida_estimada = fecha_pedido + timedelta(days=proveedor_data['promedio_dias_produccion'])
            fecha_arribo_estimada = fecha_salida_estimada + timedelta(days=proveedor_data['promedio_dias_transporte_maritimo'])
            fecha_planta_estimada = fecha_arribo_estimada + timedelta(days=15)
            
            # Verificar si necesita actualización
            needs_update = False
            update_fields = []
            update_values = []
            
            if fecha_salida_actual != fecha_salida_estimada:
                update_fields.append("fecha_salida_estimada = %s")
                update_values.append(fecha_salida_estimada)
                needs_update = True
            
            if fecha_arribo_actual != fecha_arribo_estimada:
                update_fields.append("fecha_arribo_estimada = %s")
                update_values.append(fecha_arribo_estimada)
                needs_update = True
            
            if fecha_planta_actual != fecha_planta_estimada:
                update_fields.append("fecha_planta_estimada = %s")
                update_values.append(fecha_planta_estimada)
                needs_update = True
            
            if needs_update:
                # Siempre actualizar timestamp
                update_fields.append("updated_at = %s")
                update_values.append(datetime.utcnow())
                
                # Agregar IMI para WHERE
                update_values.append(imi)
                
                # Ejecutar actualización
                update_query = f"""
                    UPDATE compras_v2 SET
                        {', '.join(update_fields)}
                    WHERE imi = %s
                """
                
                cursor.execute(update_query, update_values)
                updated_count += 1
                
                logger.info(f"IMI {imi}: {fecha_pedido} -> Salida: {fecha_salida_estimada}, Arribo: {fecha_arribo_estimada}, Planta: {fecha_planta_estimada}")
            else:
                skipped_count += 1
        
        # Commit todos los cambios
        conn.commit()
        
        logger.info(f"Actualización completada: {updated_count} actualizados, {skipped_count} sin cambios")
        
        # Actualizar columnas automáticas en materiales (pu_usd)
        logger.info("Iniciando actualización de columnas automáticas en materiales...")
        materiales_updated = 0
        
        try:
            # Obtener todos los materiales que necesitan recalcular pu_usd
            cursor.execute("""
                SELECT 
                    c2m.id as material_id,
                    c2m.pu_divisa,
                    c2.moneda,
                    c2.tipo_cambio_real,
                    c2.tipo_cambio_estimado
                FROM compras_v2_materiales c2m
                JOIN compras_v2 c2 ON c2m.compra_id = c2.id
                WHERE c2m.pu_divisa > 0
            """)
            
            materiales = cursor.fetchall()
            logger.info(f"Encontrados {len(materiales)} materiales para recalcular pu_usd")
            
            for material in materiales:
                material_id = material[0]
                pu_divisa = float(material[1])
                moneda = material[2]
                tipo_cambio_real = material[3]
                tipo_cambio_estimado = material[4]
                
                # Calcular pu_usd
                pu_usd_calculated = 0.0
                if moneda == 'USD':
                    pu_usd_calculated = pu_divisa
                elif moneda == 'MXN':
                    tipo_cambio = tipo_cambio_real if tipo_cambio_real and tipo_cambio_real > 0 else tipo_cambio_estimado
                    if tipo_cambio and tipo_cambio > 0:
                        pu_usd_calculated = pu_divisa / tipo_cambio
                    else:
                        pu_usd_calculated = pu_divisa  # Fallback si no hay tipo de cambio
                else:
                    pu_usd_calculated = pu_divisa  # Para otras monedas, usar el valor original
                
                # Actualizar pu_usd
                cursor.execute("""
                    UPDATE compras_v2_materiales
                    SET pu_usd = %s, updated_at = %s
                    WHERE id = %s
                """, (pu_usd_calculated, datetime.utcnow(), material_id))
                
                materiales_updated += 1
            
            # Commit los cambios de materiales
            conn.commit()
            logger.info(f"Actualizados {materiales_updated} materiales con nuevos valores de pu_usd")
            
        except Exception as e:
            logger.error(f"Error actualizando columnas automáticas: {str(e)}")
            conn.rollback()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Actualización de fechas estimadas y columnas automáticas completada",
            "total_records": len(records),
            "updated": updated_count,
            "skipped": skipped_count,
            "proveedores_loaded": len(proveedores_data),
            "materiales_updated": materiales_updated
        }
        
    except Exception as e:
        logger.error(f"Error actualizando fechas estimadas: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error actualizando fechas estimadas: {str(e)}")

@app.get("/api/compras-v2/download-layout")
async def download_compras_layout():
    """Descarga el layout de Excel para compras_v2"""
    try:
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        
        logger.info("Generando layout de Excel para compras_v2")
        
        # Crear datos de ejemplo para el layout
        compras_ejemplo = {
            'imi': [1001, 1002, 1003],
            'proveedor': ['HONGKONG', 'PEREZ TRADING', 'COSMO'],
            'fecha_pedido': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'moneda': ['USD', 'USD', 'USD'],
            'dias_credito': [30, 45, 30],
            'anticipo_pct': [10.0, 15.0, 5.0],
            'anticipo_monto': [1000.0, 1500.0, 500.0],
            'fecha_anticipo': ['2024-01-10', '2024-01-11', '2024-01-12'],
            'fecha_pago_factura': ['2024-02-15', '2024-03-01', '2024-02-17'],
            'fecha_salida_real': ['2024-01-20', '2024-01-22', '2024-01-19'],
            'fecha_arribo_real': ['2024-02-15', '2024-02-20', '2024-02-12'],
            'fecha_planta_real': ['2024-02-18', '2024-02-23', '2024-02-15'],
                'tipo_cambio_estimado': [20.0, 20.5, 20.2],
                'tipo_cambio_real': [20.1, 20.6, 20.3],
                'gastos_importacion_divisa': [100.0, 150.0, 75.0]
        }
        
        materiales_ejemplo = {
            'imi': [1001, 1001, 1002, 1002, 1003],
            'material_codigo': ['MAT001', 'MAT002', 'MAT003', 'MAT004', 'MAT005'],
            'kg': [100.0, 150.0, 200.0, 100.0, 250.0],
            'pu_divisa': [10.0, 12.0, 15.0, 8.0, 6.0]
        }
        
        # Crear DataFrames
        compras_df = pd.DataFrame(compras_ejemplo)
        materiales_df = pd.DataFrame(materiales_ejemplo)
        
        # Crear archivo Excel en memoria
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Hoja de Compras Generales
            compras_df.to_excel(writer, sheet_name='Compras Generales', index=False)
            
            # Hoja de Materiales Detalle
            materiales_df.to_excel(writer, sheet_name='Materiales Detalle', index=False)
            
            # Hoja de Instrucciones
            instrucciones_data = {
                'Columna': [
                    'IMI', 'Proveedor', 'Fecha Pedido', 'Moneda', 'Dias Credito',
                    'Anticipo %', 'Anticipo Monto', 'Fecha Anticipo', 'Fecha Pago Factura',
                    'Fecha Salida Real', 'Fecha Arribo Real', 'Fecha Planta Real',
                    'Tipo Cambio Estimado', 'Tipo Cambio Real', 'Gastos Importacion Divisa',
                    'Material Codigo', 'KG', 'PU Divisa'
                ],
                'Tipo': [
                    'INTEGER', 'TEXT', 'DATE', 'VARCHAR', 'INTEGER',
                    'NUMERIC', 'NUMERIC', 'DATE', 'DATE',
                    'DATE', 'DATE', 'DATE',
                    'NUMERIC', 'NUMERIC', 'NUMERIC',
                    'VARCHAR', 'NUMERIC', 'NUMERIC'
                ],
                'Obligatorio': [
                    'SI', 'SI', 'SI', 'SI', 'NO',
                    'NO', 'NO', 'NO', 'NO',
                    'NO', 'NO', 'NO',
                    'NO', 'NO', 'NO',
                    'SI', 'SI', 'SI'
                ],
                'Descripcion': [
                    'Numero unico de compra', 'Nombre del proveedor', 'Fecha de pedido', 'Moneda de la compra', 'Dias de credito',
                    'Porcentaje de anticipo', 'Monto del anticipo en moneda original', 'Fecha de pago anticipo', 'Fecha de pago factura',
                    'Fecha real de salida del puerto', 'Fecha real de arribo al puerto', 'Fecha real de llegada a planta',
                    'Tipo de cambio estimado', 'Tipo de cambio real', 'Gastos de importacion en pesos',
                    'Codigo del material', 'Cantidad en kilogramos', 'Precio unitario en divisa'
                ]
            }
            
            instrucciones_df = pd.DataFrame(instrucciones_data)
            instrucciones_df.to_excel(writer, sheet_name='Instrucciones', index=False)
        
        excel_buffer.seek(0)
        
        # Crear respuesta de streaming
        def iter_file():
            yield from excel_buffer
        
        headers = {
            'Content-Disposition': 'attachment; filename="Layout_Compras_V2.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        logger.info("Layout de Excel generado exitosamente")
        
        return StreamingResponse(
            iter_file(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error generando layout de Excel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DE COMPRAS (LEGACY) - ELIMINADOS ====================
# Todos los endpoints de compras legacy han sido eliminados
# Usar /api/compras-v2/* en su lugar

# ==================== ENDPOINTS ADICIONALES (404 FIXES) ====================

@app.get("/api/filtros-disponibles")
async def get_filtros_disponibles(db: Session = Depends(get_db)):
    """Obtiene opciones disponibles para filtros (compatible con frontend)"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros
        
    except Exception as e:
        logger.error(f"Error obteniendo filtros disponibles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pedidos-filtro")
async def get_pedidos_filtro(db: Session = Depends(get_db)):
    """Obtiene lista de pedidos para filtros (compatible con frontend)"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros.get("pedidos", [])
        
    except Exception as e:
        logger.error(f"Error obteniendo pedidos para filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pedidos/ventas-por-material")
async def get_ventas_por_material(
    limite: int = Query(10, description="Número máximo de materiales a retornar"),
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
    db: Session = Depends(get_db)
):
    try:
        db_service = DatabaseService(db)
        filtros = {}
        if mes: filtros['mes'] = mes
        if año: filtros['año'] = año
        if pedidos: filtros['pedidos'] = pedidos

        pedidos_service = db_service.pedidos_service
        result = pedidos_service.get_ventas_por_material(limite, filtros)
        return result
    except Exception as e:
        logger.error(f"Error obteniendo ventas por material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clientes-filtro")
async def get_clientes_filtro(db: Session = Depends(get_db)):
    """Obtiene lista de clientes para filtros (compatible con frontend)"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros.get("clientes", [])
        
    except Exception as e:
        logger.error(f"Error obteniendo clientes para filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/materiales-filtro")
async def get_materiales_filtro(db: Session = Depends(get_db)):
    """Obtiene lista de materiales para filtros (compatible con frontend)"""
    try:
        db_service = DatabaseService(db)
        filtros = db_service.get_filtros_disponibles()
        return filtros.get("materiales", [])
        
    except Exception as e:
        logger.error(f"Error obteniendo materiales para filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archivos-procesados")
async def get_archivos_procesados(db: Session = Depends(get_db)):
    """Obtiene lista de archivos procesados (compatible con frontend)"""
    try:
        db_service = DatabaseService(db)
        archivos = db_service.get_archivos_procesados()
        return archivos
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos procesados: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data-summary")
async def get_data_summary(db: Session = Depends(get_db)):
    """Obtiene resumen de datos disponibles (compatible con frontend)"""
    try:
        db_service = DatabaseService(db)
        summary = db_service.get_data_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor Immermex Dashboard (Con Base de Datos)")
    print("Backend: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Frontend: http://localhost:3000")
    print("Base de datos: Persistencia habilitada")
    print("=" * 60)
    
    uvicorn.run(
        "main_with_db:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
