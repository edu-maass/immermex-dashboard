"""
Manejo centralizado de errores para Immermex Dashboard
"""

import logging
from fastapi import HTTPException
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ImmermexError(Exception):
    """Excepción base para errores de Immermex"""
    
    def __init__(self, message: str, error_code: str = "IMMERMEX_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DataProcessingError(ImmermexError):
    """Error en procesamiento de datos"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "DATA_PROCESSING_ERROR", details)

class DatabaseError(ImmermexError):
    """Error en operaciones de base de datos"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "DATABASE_ERROR", details)

class ValidationError(ImmermexError):
    """Error de validación de datos"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class FileProcessingError(ImmermexError):
    """Error en procesamiento de archivos"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "FILE_PROCESSING_ERROR", details)

def handle_database_error(func):
    """Decorator para manejo de errores de base de datos"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise DatabaseError(f"Error en operación de base de datos: {str(e)}")
    return wrapper

def handle_file_processing_error(func):
    """Decorator para manejo de errores de procesamiento de archivos"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"File processing error in {func.__name__}: {str(e)}")
            raise FileProcessingError(f"Error procesando archivo: {str(e)}")
    return wrapper

def handle_validation_error(func):
    """Decorator para manejo de errores de validación"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Validation error in {func.__name__}: {str(e)}")
            raise ValidationError(f"Error de validación: {str(e)}")
    return wrapper

def convert_to_http_exception(error: ImmermexError) -> HTTPException:
    """Convierte errores de Immermex a HTTPException"""
    
    error_mapping = {
        "DATA_PROCESSING_ERROR": 422,
        "DATABASE_ERROR": 500,
        "VALIDATION_ERROR": 400,
        "FILE_PROCESSING_ERROR": 422,
        "IMMERMEX_ERROR": 500
    }
    
    status_code = error_mapping.get(error.error_code, 500)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "message": error.message,
            "error_code": error.error_code,
            "details": error.details
        }
    )

def handle_api_error(func):
    """Decorator para manejo de errores en endpoints de API"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ImmermexError as e:
            raise convert_to_http_exception(e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Error interno del servidor",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "details": {"function": func.__name__}
                }
            )
    return wrapper
