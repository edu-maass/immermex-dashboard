"""
Sistema avanzado de logging estructurado para Immermex Dashboard
"""
import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from enum import Enum
import traceback
from functools import wraps
import time
from pathlib import Path

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    PROCESSING = "processing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    VALIDATION = "validation"

class StructuredFormatter(logging.Formatter):
    """Formatter para logs estructurados en formato JSON"""
    
    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea el log record como JSON estructurado"""
        
        # Información básica del log
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Agregar información de request si está disponible
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        # Agregar información de performance
        if hasattr(record, 'execution_time'):
            log_entry['execution_time_ms'] = record.execution_time
        
        if hasattr(record, 'memory_usage'):
            log_entry['memory_usage_mb'] = record.memory_usage
        
        # Agregar información de error
        if record.exc_info and self.include_traceback:
            log_entry['exception'] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Agregar metadata adicional
        if hasattr(record, 'metadata') and record.metadata:
            log_entry['metadata'] = record.metadata
        
        # Agregar categoría
        if hasattr(record, 'category'):
            log_entry['category'] = record.category.value if isinstance(record.category, LogCategory) else record.category
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

class AdvancedLogger:
    """Logger avanzado con funcionalidades estructuradas"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Crear logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicación de handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers para el logger"""
        
        # Handler para consola (formato legible)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Solo agregar handlers de archivo si no estamos en un entorno serverless (sistema de solo lectura)
        if not self._is_serverless_environment():
            try:
                # Handler para archivo general (JSON estructurado)
                general_file = self.log_dir / f"{self.name}_general.log"
                general_handler = logging.handlers.RotatingFileHandler(
                    general_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
                )
                general_handler.setLevel(logging.DEBUG)
                general_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(general_handler)
                
                # Handler para errores (solo ERROR y CRITICAL)
                error_file = self.log_dir / f"{self.name}_errors.log"
                error_handler = logging.handlers.RotatingFileHandler(
                    error_file, maxBytes=5*1024*1024, backupCount=10, encoding='utf-8'
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(error_handler)
                
                # Handler para performance (archivo separado)
                perf_file = self.log_dir / f"{self.name}_performance.log"
                perf_handler = logging.handlers.RotatingFileHandler(
                    perf_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
                )
                perf_handler.setLevel(logging.DEBUG)
                perf_handler.setFormatter(StructuredFormatter())
                
                # Filtrar solo logs de performance
                perf_filter = PerformanceFilter()
                perf_handler.addFilter(perf_filter)
                self.logger.addHandler(perf_handler)
                
                # Handler para auditoría (archivo separado)
                audit_file = self.log_dir / f"{self.name}_audit.log"
                audit_handler = logging.handlers.RotatingFileHandler(
                    audit_file, maxBytes=10*1024*1024, backupCount=20, encoding='utf-8'
                )
                audit_handler.setLevel(logging.INFO)
                audit_handler.setFormatter(StructuredFormatter())
                
                # Filtrar solo logs de auditoría
                audit_filter = AuditFilter()
                audit_handler.addFilter(audit_filter)
                self.logger.addHandler(audit_handler)
            except (OSError, PermissionError) as e:
                # Si no se pueden crear archivos de log, solo usar consola
                self.logger.warning(f"Could not create file handlers: {e}. Using console logging only.")
    
    def _is_serverless_environment(self) -> bool:
        """Verifica si estamos en un entorno serverless (Render, etc.)"""
        return (
            os.environ.get('RENDER') == 'true' or  # Render
            os.environ.get('RENDER_SERVICE_NAME') is not None or  # Render
            os.environ.get('VCAP_APPLICATION') is not None  # Otros PaaS
        )
    
    def log_with_context(
        self,
        level: LogLevel,
        message: str,
        category: Optional[LogCategory] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log con contexto adicional"""
        
        extra = {
            'category': category,
            'metadata': metadata or {}
        }
        
        # Agregar contexto adicional
        for key, value in kwargs.items():
            extra[key] = value
        
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra=extra)
    
    def debug(self, message: str, category: LogCategory = None, **kwargs):
        """Log de debug"""
        self.log_with_context(LogLevel.DEBUG, message, category, **kwargs)
    
    def info(self, message: str, category: LogCategory = None, **kwargs):
        """Log de información"""
        self.log_with_context(LogLevel.INFO, message, category, **kwargs)
    
    def warning(self, message: str, category: LogCategory = None, **kwargs):
        """Log de advertencia"""
        self.log_with_context(LogLevel.WARNING, message, category, **kwargs)
    
    def error(self, message: str, category: LogCategory = None, exc_info: bool = True, **kwargs):
        """Log de error"""
        self.log_with_context(LogLevel.ERROR, message, category, **kwargs)
    
    def critical(self, message: str, category: LogCategory = None, exc_info: bool = True, **kwargs):
        """Log crítico"""
        self.log_with_context(LogLevel.CRITICAL, message, category, **kwargs)
    
    def audit(self, action: str, user_id: str = None, resource: str = None, **kwargs):
        """Log de auditoría"""
        self.log_with_context(
            LogLevel.INFO,
            f"AUDIT: {action}",
            LogCategory.AUDIT,
            metadata={
                "action": action,
                "user_id": user_id,
                "resource": resource,
                **kwargs
            }
        )
    
    def performance(self, operation: str, execution_time: float, **kwargs):
        """Log de performance"""
        self.log_with_context(
            LogLevel.INFO,
            f"PERFORMANCE: {operation}",
            LogCategory.PERFORMANCE,
            execution_time=execution_time * 1000,  # Convertir a ms
            metadata={
                "operation": operation,
                **kwargs
            }
        )

class PerformanceFilter(logging.Filter):
    """Filtro para logs de performance"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        return hasattr(record, 'category') and record.category == LogCategory.PERFORMANCE

class AuditFilter(logging.Filter):
    """Filtro para logs de auditoría"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        return hasattr(record, 'category') and record.category == LogCategory.AUDIT

# Decoradores para logging automático
def log_execution_time(logger: AdvancedLogger, operation: str):
    """Decorador para loggear tiempo de ejecución"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.performance(operation, execution_time, success=True)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.performance(operation, execution_time, success=False, error=str(e))
                raise
        return async_wrapper
    return decorator

def log_execution_time_sync(logger: AdvancedLogger, operation: str):
    """Decorador para loggear tiempo de ejecución (síncrono)"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.performance(operation, execution_time, success=True)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.performance(operation, execution_time, success=False, error=str(e))
                raise
        return sync_wrapper
    return decorator

def log_api_call(logger: AdvancedLogger):
    """Decorador para loggear llamadas a API"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraer información de request si está disponible
            request_info = {}
            for arg in args:
                if hasattr(arg, 'url'):
                    request_info['endpoint'] = str(arg.url.path)
                    request_info['method'] = arg.method
                    request_info['ip_address'] = arg.client.host if arg.client else None
                    break
            
            logger.info(f"API call: {func.__name__}", LogCategory.API, **request_info)
            
            try:
                result = await func(*args, **kwargs)
                logger.info(f"API call successful: {func.__name__}", LogCategory.API, **request_info)
                return result
            except Exception as e:
                logger.error(f"API call failed: {func.__name__}", LogCategory.API, **request_info)
                raise
        return wrapper
    return decorator

# Loggers globales
def get_logger(name: str) -> AdvancedLogger:
    """Obtiene o crea un logger avanzado"""
    return AdvancedLogger(name)

# Logger principal del sistema
system_logger = get_logger("immermex_system")
api_logger = get_logger("immermex_api")
database_logger = get_logger("immermex_database")
processing_logger = get_logger("immermex_processing")
security_logger = get_logger("immermex_security")

# Configuración de logging global
def setup_global_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """Configura el logging global del sistema"""
    
    # Configurar nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar logging root
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler básico para el root logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Configurar logging de bibliotecas externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    system_logger.info("Global logging configured", LogCategory.SYSTEM, 
                      log_level=log_level, log_dir=log_dir)

# Utilidades para logging contextual
class LogContext:
    """Context manager para logging con contexto"""
    
    def __init__(self, logger: AdvancedLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting: {self.operation}", metadata=self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation}", 
                           LogCategory.PERFORMANCE,
                           execution_time=execution_time * 1000,
                           metadata=self.context)
        else:
            self.logger.error(f"Failed: {self.operation}", 
                            LogCategory.PERFORMANCE,
                            execution_time=execution_time * 1000,
                            metadata=self.context,
                            error_type=exc_type.__name__,
                            error_message=str(exc_val))

def log_context(logger: AdvancedLogger, operation: str, **context):
    """Decorador para crear contexto de logging"""
    return LogContext(logger, operation, **context)
