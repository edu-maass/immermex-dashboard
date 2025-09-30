"""
Módulo de utilidades comunes para Immermex Dashboard
"""

from .validators import DataValidator
from .logging_config import setup_logging, log_api_request, log_file_processing, log_error
from .error_handlers import (
    ImmermexError, DataProcessingError, DatabaseError, ValidationError, FileProcessingError,
    handle_database_error, handle_file_processing_error, handle_validation_error,
    handle_api_error, convert_to_http_exception
)

__all__ = [
    'DataValidator',
    'setup_logging',
    'log_api_request', 
    'log_file_processing',
    'log_error',
    'ImmermexError',
    'DataProcessingError',
    'DatabaseError',
    'ValidationError',
    'FileProcessingError',
    'handle_database_error',
    'handle_file_processing_error',
    'handle_validation_error',
    'handle_api_error',
    'convert_to_http_exception'
]
