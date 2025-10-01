"""
API REST para Immermex Dashboard con persistencia en base de datos
Integra el procesador avanzado con almacenamiento persistente
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
from utils import setup_logging, handle_api_error, FileProcessingError, DatabaseError
from datetime import datetime
from data_processor import process_immermex_file_advanced

# Configurar logging
logger = setup_logging()

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API (Con Base de Datos)",
    description="API REST para dashboard de indicadores financieros con persistencia en base de datos",
    version="2.0.0"
)

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

@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al arrancar la aplicación"""
    try:
        # Verificar configuración de base de datos
        database_url = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
        
        if database_url.startswith("postgresql://"):
            logger.info("Conectando a Supabase/PostgreSQL en la nube")
            logger.info(f"Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'configurado'}")
        else:
            logger.info("Usando SQLite local para desarrollo")
        
        success = init_db()
        if success:
            logger.info("API con base de datos iniciada correctamente")
            
            # Verificar conexión
            try:
                from database import SessionLocal
                from sqlalchemy import text
                with SessionLocal() as db:
                    db.execute(text("SELECT 1"))
                logger.info("Conexion a base de datos verificada")
            except Exception as e:
                logger.warning(f"Advertencia en conexion: {str(e)}")
                
        else:
            logger.error("Error inicializando base de datos")
    except Exception as e:
        logger.error(f"Error en startup: {str(e)}")
        logger.error("Asegurate de que DATABASE_URL este configurada correctamente")

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {
        "message": "Immermex Dashboard API (Con Base de Datos)", 
        "status": "active",
        "version": "2.0.0",
        "features": ["persistencia_db", "procesamiento_avanzado", "filtros_dinamicos"]
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
                "nombre_archivo": file.filename,
                "tipo_archivo": file.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "contenido": contents.decode('utf-8', errors='ignore'),
                "reemplazar_datos": reemplazar_datos
            }
            
            # Guardar en base de datos
            logger.info("Iniciando guardado en base de datos...")
            db_service = DatabaseService(db)
            result = db_service.save_processed_data(processed_data_dict, archivo_info)
            logger.info(f"Guardado completado: {result}")
            
            logger.info(f"Archivo procesado y guardado exitosamente: {file.filename}")
            
            return {
                "mensaje": "Archivo procesado y guardado exitosamente en base de datos",
                "nombre_archivo": file.filename,
                "archivo_id": result["archivo_id"],
                "total_registros": result["total_registros"],
                "fecha_procesamiento": datetime.now().isoformat(),
                "estado": "procesado",
                "algoritmo": "memory_processing_with_persistence",
                "desglose": {
                    "facturas": result["facturas"],
                    "cobranzas": result["cobranzas"],
                    "anticipos": result["anticipos"],
                    "pedidos": result["pedidos"]
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

@app.post("/api/upload/compras")
async def upload_compras_file(
    file: UploadFile = File(...),
    reemplazar_datos: bool = Query(True, description="Si true, reemplaza todos los datos existentes"),
    db: Session = Depends(get_db)
):
    """Endpoint específico para subir archivos Excel de compras"""
    try:
        # Validación básica del archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Leer contenido para validar tamaño
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 10MB permitido.")
        
        logger.info(f"Procesando archivo de compras: {file.filename}")
        
        # Procesar archivo de compras usando el procesador específico V2
        try:
            from compras_processor_v2 import process_compras_v2
            
            logger.info(f"[V2] Procesando archivo de compras desde memoria: {file.filename}")
            logger.info(f"[V2] Tamaño del archivo: {len(content)} bytes")
            
            # Procesar usando el procesador V2
            processed_data_dict, kpis = process_compras_v2(content, file.filename)
            logger.info(f"Datos de compras procesados exitosamente. Claves: {list(processed_data_dict.keys())}")
            
            # Preparar información del archivo
            archivo_info = {
                "nombre_archivo": file.filename,
                "tipo_archivo": file.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "reemplazar_datos": reemplazar_datos,
                "tipo_datos": "compras"  # Marcar como datos de compras
            }
            
            # Guardar en base de datos
            logger.info("Iniciando guardado de datos de compras en base de datos...")
            db_service = DatabaseService(db)
            result = db_service.save_processed_data(processed_data_dict, archivo_info)
            logger.info(f"Guardado de compras completado: {result}")
            
            logger.info(f"Archivo de compras procesado y guardado exitosamente: {file.filename}")
            
            return {
                "mensaje": "Archivo de compras procesado y guardado exitosamente en base de datos",
                "nombre_archivo": file.filename,
                "archivo_id": result["archivo_id"],
                "total_registros": result["total_registros"],
                "registros_procesados": result["total_registros"],
                "kpis_compras": kpis,
                "datos_procesados": {
                    "compras": len(processed_data_dict.get('compras', []))
                },
                "archivo_info": archivo_info
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo de compras: {str(e)}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error procesando archivo de compras: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint de compras: {str(e)}")
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

# ==================== ENDPOINTS DE COMPRAS ====================

@app.get("/api/compras/kpis")
async def get_compras_kpis(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    material: Optional[str] = Query(None, description="Filtrar por material"),
    db: Session = Depends(get_db)
):
    """Obtiene KPIs principales de compras con filtros opcionales"""
    try:
        db_service = DatabaseService(db)
        
        # Preparar filtros
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        if material:
            filtros['material'] = material
        
        kpis = db_service.calculate_compras_kpis(filtros)
        return kpis
        
    except Exception as e:
        logger.error(f"Error obteniendo KPIs de compras: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras/evolucion-precios")
async def get_evolucion_precios(
    material: Optional[str] = Query(None, description="Filtrar por material"),
    moneda: str = Query("USD", description="Moneda para mostrar precios (USD/MXN)"),
    db: Session = Depends(get_db)
):
    """Obtiene evolución mensual de precios por kg"""
    try:
        db_service = DatabaseService(db)
        
        filtros = {}
        if material:
            filtros['material'] = material
        
        evolucion = db_service.get_evolucion_precios(filtros, moneda)
        return evolucion
        
    except Exception as e:
        logger.error(f"Error obteniendo evolución de precios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras/flujo-pagos")
async def get_flujo_pagos(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db)
):
    """Obtiene flujo de pagos de compras"""
    try:
        db_service = DatabaseService(db)
        
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        
        flujo = db_service.get_flujo_pagos_compras(filtros)
        return flujo
        
    except Exception as e:
        logger.error(f"Error obteniendo flujo de pagos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras/aging-cuentas-pagar")
async def get_aging_cuentas_pagar(
    mes: Optional[int] = Query(None, description="Filtrar por mes"),
    año: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db)
):
    """Obtiene aging de cuentas por pagar"""
    try:
        db_service = DatabaseService(db)
        
        filtros = {}
        if mes:
            filtros['mes'] = mes
        if año:
            filtros['año'] = año
        
        aging = db_service.get_aging_cuentas_pagar(filtros)
        return aging
        
    except Exception as e:
        logger.error(f"Error obteniendo aging de cuentas por pagar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras/materiales")
async def get_materiales_compras(db: Session = Depends(get_db)):
    """Obtiene lista de materiales disponibles en compras"""
    try:
        db_service = DatabaseService(db)
        materiales = db_service.get_materiales_compras()
        return materiales
        
    except Exception as e:
        logger.error(f"Error obteniendo materiales de compras: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor Immermex Dashboard (Con Base de Datos)")
    print("📊 Backend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔄 Frontend: http://localhost:3000")
    print("💾 Base de datos: Persistencia habilitada")
    print("=" * 60)
    
    uvicorn.run(
        "main_with_db:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
