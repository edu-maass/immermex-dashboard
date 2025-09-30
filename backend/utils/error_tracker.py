"""
Sistema avanzado de tracking y manejo de errores
"""
import logging
import traceback
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    VALIDATION = "validation"
    DATABASE = "database"
    API = "api"
    PROCESSING = "processing"
    FILE = "file"
    SYSTEM = "system"
    NETWORK = "network"

@dataclass
class ErrorContext:
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None

@dataclass
class ErrorInfo:
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception_type: str
    stack_trace: str
    context: ErrorContext
    metadata: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution_notes: Optional[str] = None

class ErrorTracker:
    """Sistema de tracking y manejo de errores"""
    
    def __init__(self):
        self.errors: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.recent_errors: List[ErrorInfo] = []
        self.max_recent_errors = 100
        
    def track_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_log: bool = True
    ) -> ErrorInfo:
        """Registra un error en el sistema de tracking"""
        
        error_id = f"ERR_{int(time.time() * 1000)}"
        timestamp = datetime.utcnow()
        
        # Crear contexto por defecto si no se proporciona
        if context is None:
            context = ErrorContext(timestamp=timestamp)
        
        # Crear información del error
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(error),
            exception_type=type(error).__name__,
            stack_trace=traceback.format_exc(),
            context=context,
            metadata=metadata or {},
            timestamp=timestamp
        )
        
        # Agregar a la lista de errores
        self.errors.append(error_info)
        
        # Actualizar contadores
        error_key = f"{category.value}_{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Agregar a errores recientes
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Log automático según severidad
        if auto_log:
            self._log_error(error_info)
        
        # Alertas para errores críticos
        if severity == ErrorSeverity.CRITICAL:
            self._send_critical_alert(error_info)
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """Log del error según su severidad"""
        log_message = f"[{error_info.error_id}] {error_info.message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error_info": asdict(error_info)})
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"error_info": asdict(error_info)})
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"error_info": asdict(error_info)})
        else:
            logger.info(log_message, extra={"error_info": asdict(error_info)})
    
    def _send_critical_alert(self, error_info: ErrorInfo):
        """Envía alerta para errores críticos"""
        alert_message = f"CRITICAL ERROR [{error_info.error_id}]: {error_info.message}"
        logger.critical(f"ALERT: {alert_message}")
        
        # Aquí se podría integrar con servicios de alertas como Slack, email, etc.
        # Por ahora solo se loggea
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de errores"""
        total_errors = len(self.errors)
        recent_errors = len(self.recent_errors)
        
        # Errores por categoría
        category_counts = {}
        for error in self.errors:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Errores por severidad
        severity_counts = {}
        for error in self.errors:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Errores recientes (últimas 24 horas)
        now = datetime.utcnow()
        recent_24h = [
            error for error in self.errors 
            if (now - error.timestamp).total_seconds() < 86400
        ]
        
        return {
            "total_errors": total_errors,
            "recent_errors": recent_errors,
            "errors_last_24h": len(recent_24h),
            "category_counts": category_counts,
            "severity_counts": severity_counts,
            "top_errors": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "unresolved_errors": len([e for e in self.errors if not e.resolved])
        }
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene errores recientes"""
        return [
            asdict(error) for error in self.recent_errors[-limit:]
        ]
    
    def resolve_error(self, error_id: str, resolution_notes: str) -> bool:
        """Marca un error como resuelto"""
        for error in self.errors:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                logger.info(f"Error {error_id} marked as resolved: {resolution_notes}")
                return True
        return False
    
    def clear_old_errors(self, days_to_keep: int = 30):
        """Limpia errores antiguos"""
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
        
        initial_count = len(self.errors)
        self.errors = [error for error in self.errors if error.timestamp > cutoff_date]
        removed_count = initial_count - len(self.errors)
        
        logger.info(f"Cleaned {removed_count} old errors (keeping last {days_to_keep} days)")
        return removed_count

# Instancia global del tracker
error_tracker = ErrorTracker()

# Funciones de conveniencia
def track_validation_error(error: Exception, context: Optional[ErrorContext] = None, metadata: Optional[Dict[str, Any]] = None):
    """Track validation errors"""
    return error_tracker.track_error(error, ErrorCategory.VALIDATION, ErrorSeverity.LOW, context, metadata)

def track_database_error(error: Exception, context: Optional[ErrorContext] = None, metadata: Optional[Dict[str, Any]] = None):
    """Track database errors"""
    return error_tracker.track_error(error, ErrorCategory.DATABASE, ErrorSeverity.HIGH, context, metadata)

def track_api_error(error: Exception, context: Optional[ErrorContext] = None, metadata: Optional[Dict[str, Any]] = None):
    """Track API errors"""
    return error_tracker.track_error(error, ErrorCategory.API, ErrorSeverity.MEDIUM, context, metadata)

def track_processing_error(error: Exception, context: Optional[ErrorContext] = None, metadata: Optional[Dict[str, Any]] = None):
    """Track data processing errors"""
    return error_tracker.track_error(error, ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM, context, metadata)

def track_file_error(error: Exception, context: Optional[ErrorContext] = None, metadata: Optional[Dict[str, Any]] = None):
    """Track file processing errors"""
    return error_tracker.track_error(error, ErrorCategory.FILE, ErrorSeverity.MEDIUM, context, metadata)

def track_system_error(error: Exception, context: Optional[ErrorContext] = None, metadata: Optional[Dict[str, Any]] = None):
    """Track system errors"""
    return error_tracker.track_error(error, ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL, context, metadata)
