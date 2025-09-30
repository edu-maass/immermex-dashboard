"""
API REST para Immermex Dashboard con persistencia en base de datos
Integra el procesador avanzado con almacenamiento persistente
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
import hashlib
from typing import List, Optional

# Imports locales
from database import get_db, init_db, ArchivoProcesado
from database_service_refactored import DatabaseService
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

@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al arrancar la aplicación"""
    try:
        # Verificar configuración de base de datos
        database_url = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
        
        if database_url.startswith("postgresql://"):
            logger.info("🌐 Conectando a Supabase/PostgreSQL en la nube")
            logger.info(f"🔗 Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'configurado'}")
        else:
            logger.info("💾 Usando SQLite local para desarrollo")
        
        success = init_db()
        if success:
            logger.info("✅ API con base de datos iniciada correctamente")
            
            # Verificar conexión
            try:
                from database import SessionLocal
                from sqlalchemy import text
                db = SessionLocal()
                db.execute(text("SELECT 1"))
                db.close()
                logger.info("✅ Conexión a base de datos verificada")
            except Exception as e:
                logger.warning(f"⚠️  Advertencia en conexión: {str(e)}")
                
        else:
            logger.error("❌ Error inicializando base de datos")
    except Exception as e:
        logger.error(f"❌ Error en startup: {str(e)}")
        logger.error("💡 Asegúrate de que DATABASE_URL esté configurada correctamente")

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
@handle_api_error
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
