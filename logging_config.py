"""
Configuración de logging para Immermex Dashboard
"""

import logging
import sys
from datetime import datetime

def setup_logging():
    """Configura el sistema de logging para la aplicación"""
    
    # Crear logger principal
    logger = logging.getLogger("immermex_dashboard")
    logger.setLevel(logging.INFO)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Crear formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Handler para archivo (opcional)
    try:
        file_handler = logging.FileHandler('immermex_dashboard.log')
        file_handler.setLevel(logging.DEBUG)
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
    
    return logger

def log_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Log de requests de API"""
    logger = logging.getLogger("immermex_dashboard")
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
