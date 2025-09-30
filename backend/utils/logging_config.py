"""
Configuración optimizada de logging para Immermex Dashboard
"""

import logging
import sys
import os
from datetime import datetime

def setup_logging():
    """Configura el sistema de logging optimizado por entorno"""
    
    # Crear logger principal
    logger = logging.getLogger("immermex_dashboard")
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Determinar nivel de logging según entorno
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        log_level = logging.WARNING  # Solo warnings y errores en producción
    else:
        log_level = logging.INFO  # Más detallado en desarrollo
    
    logger.setLevel(log_level)
    
    # Crear formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Handler para archivo (solo en desarrollo o si se especifica)
    if environment != "production" or os.getenv("ENABLE_FILE_LOGGING", "").lower() == "true":
        try:
            file_handler = logging.FileHandler('immermex_dashboard.log')
            file_handler.setLevel(logging.DEBUG)  # Archivo siempre más detallado
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # Si no se puede crear el archivo de log, continuar sin él
            pass
    
    logger.addHandler(console_handler)
    
    # Configurar logging de librerías externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("pandas").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    return logger

def log_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Log optimizado de requests de API"""
    logger = logging.getLogger("immermex_dashboard")
    
    # Solo loggear errores en producción
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production" and status_code < 400:
        return
    
    logger.info(f"API {method} {endpoint} - {status_code} - {duration:.3f}s")

def log_file_processing(filename: str, records_processed: int, success: bool):
    """Log de procesamiento de archivos"""
    logger = logging.getLogger("immermex_dashboard")
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"File processing {status}: {filename} - {records_processed} records")

def log_error(error: Exception, context: str = ""):
    """Log de errores con contexto"""
    logger = logging.getLogger("immermex_dashboard")
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)

def log_performance(operation: str, duration: float, details: str = ""):
    """Log de rendimiento para operaciones críticas"""
    logger = logging.getLogger("immermex_dashboard")
    
    # Solo loggear si es lento (>1 segundo) o en desarrollo
    environment = os.getenv("ENVIRONMENT", "development")
    if environment != "production" or duration > 1.0:
        logger.info(f"Performance: {operation} took {duration:.3f}s {details}")
