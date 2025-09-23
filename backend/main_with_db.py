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
from database_service import DatabaseService
from logging_config import setup_logging
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
                db = SessionLocal()
                db.execute("SELECT 1")
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
        db.execute("SELECT 1")
        
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
    reemplazar_datos: bool = Query(False, description="Si true, reemplaza todos los datos existentes"),
    db: Session = Depends(get_db)
):
    """Endpoint para subir archivos Excel con persistencia en base de datos"""
    try:
        # Validar tipo de archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        logger.info(f"Procesando archivo con persistencia: {file.filename}")
        
        # Leer contenido del archivo
        contents = await file.read()
        
        # Validar tamaño del archivo (máximo 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 10MB permitido.")
        
        # Guardar archivo temporalmente para procesamiento
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(contents)
        
        try:
            # Procesar archivo con algoritmo avanzado
            logger.info(f"Procesando archivo: {temp_file_path}")
            processed_data_dict, kpis = process_immermex_file_advanced(temp_file_path)
            
            # Preparar información del archivo
            archivo_info = {
                "nombre": file.filename,
                "tamaño": len(contents),
                "algoritmo": "advanced_cleaning",
                "reemplazar_datos": reemplazar_datos
            }
            
            # Guardar en base de datos
            db_service = DatabaseService(db)
            result = db_service.save_processed_data(processed_data_dict, archivo_info)
            
            if result["success"]:
                logger.info(f"Archivo procesado y guardado exitosamente: {file.filename}")
                
                return {
                    "mensaje": "Archivo procesado y guardado exitosamente en base de datos",
                    "nombre_archivo": file.filename,
                    "archivo_id": result["archivo_id"],
                    "registros_procesados": result["registros_procesados"],
                    "fecha_procesamiento": datetime.now().isoformat(),
                    "estado": "procesado",
                    "algoritmo": "advanced_cleaning_with_persistence",
                    "desglose": result["desglose"],
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
            else:
                raise HTTPException(status_code=500, detail=f"Error guardando datos: {result.get('error', 'Error desconocido')}")
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
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
