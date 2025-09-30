"""
Sistema de monitoreo de performance compatible con Vercel
Sin dependencias de archivos locales, solo métricas en memoria
"""
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import deque, defaultdict
import json

logger = logging.getLogger(__name__)

class MetricType(Enum):
    API_RESPONSE_TIME = "api_response_time"
    DATABASE_QUERY_TIME = "database_query_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    ACTIVE_REQUESTS = "active_requests"
    MEMORY_USAGE = "memory_usage"
    REQUEST_COUNT = "request_count"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    timestamp: datetime
    metric_type: MetricType
    value: float
    unit: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "metadata": self.metadata or {}
        }

@dataclass
class Alert:
    timestamp: datetime
    level: AlertLevel
    metric_type: MetricType
    message: str
    current_value: float
    threshold_value: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "metric_type": self.metric_type.value,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "metadata": self.metadata or {}
        }

class VercelPerformanceThresholds:
    """Configuración de umbrales para alertas de performance en Vercel"""
    
    def __init__(self):
        self.thresholds = {
            MetricType.API_RESPONSE_TIME: {"warning": 2000.0, "critical": 5000.0},  # ms
            MetricType.DATABASE_QUERY_TIME: {"warning": 1000.0, "critical": 3000.0},  # ms
            MetricType.CACHE_HIT_RATE: {"warning": 70.0, "critical": 50.0},  # %
            MetricType.ERROR_RATE: {"warning": 5.0, "critical": 10.0},  # %
            MetricType.ACTIVE_REQUESTS: {"warning": 50, "critical": 100},
            MetricType.MEMORY_USAGE: {"warning": 80.0, "critical": 95.0},  # %
            MetricType.REQUEST_COUNT: {"warning": 1000, "critical": 2000}  # per minute
        }
    
    def get_threshold(self, metric_type: MetricType, level: AlertLevel) -> Optional[float]:
        """Obtiene el umbral para un tipo de métrica y nivel de alerta"""
        if metric_type in self.thresholds:
            level_key = "warning" if level == AlertLevel.WARNING else "critical"
            return self.thresholds[metric_type].get(level_key)
        return None
    
    def check_threshold(self, metric_type: MetricType, value: float) -> Optional[AlertLevel]:
        """Verifica si un valor excede algún umbral"""
        if metric_type not in self.thresholds:
            return None
        
        thresholds = self.thresholds[metric_type]
        
        if value >= thresholds.get("critical", float('inf')):
            return AlertLevel.CRITICAL
        elif value >= thresholds.get("warning", float('inf')):
            return AlertLevel.WARNING
        
        return None

class VercelPerformanceMonitor:
    """Monitor de performance compatible con Vercel (solo memoria)"""
    
    def __init__(self, max_metrics: int = 500, max_alerts: int = 50):
        self.max_metrics = max_metrics
        self.max_alerts = max_alerts
        self.thresholds = VercelPerformanceThresholds()
        
        # Almacenamiento en memoria
        self.metrics: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self.alerts: deque = deque(maxlen=max_alerts)
        
        # Estadísticas de API
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": deque(maxlen=100),
            "endpoints": defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0}),
            "active_requests": 0
        }
        
        # Estadísticas de base de datos
        self.db_stats = {
            "total_queries": 0,
            "query_times": deque(maxlen=100),
            "slow_queries": deque(maxlen=50)
        }
        
        # Estadísticas de cache
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "operations": deque(maxlen=100)
        }
        
        # Métricas del sistema (simuladas para Vercel)
        self.system_stats = {
            "memory_usage": deque(maxlen=50),
            "request_count_per_minute": deque(maxlen=10)
        }
        
        # Callbacks para alertas
        self.alert_callbacks: List[Callable] = []
        
        # Lock para thread safety
        self._lock = threading.Lock()
        
        # Inicializar métricas del sistema
        self._initialize_system_metrics()
    
    def _initialize_system_metrics(self):
        """Inicializa métricas básicas del sistema"""
        timestamp = datetime.now(timezone.utc)
        
        # Métrica inicial de memoria (simulada para Vercel)
        initial_memory = 50.0  # 50% de uso simulado
        self._add_metric(MetricType.MEMORY_USAGE, initial_memory, "%", timestamp)
        
        # Métrica inicial de requests
        self._add_metric(MetricType.REQUEST_COUNT, 0, "requests/min", timestamp)
    
    def _add_metric(self, metric_type: MetricType, value: float, unit: str, timestamp: datetime, metadata: Dict[str, Any] = None):
        """Agrega una métrica al almacenamiento"""
        with self._lock:
            metric = PerformanceMetric(timestamp, metric_type, value, unit, metadata)
            self.metrics[metric_type].append(metric)
            
            # Verificar umbrales
            alert_level = self.thresholds.check_threshold(metric_type, value)
            if alert_level:
                self._create_alert(alert_level, metric_type, metric)
    
    def _create_alert(self, level: AlertLevel, metric_type: MetricType, metric: PerformanceMetric):
        """Crea una alerta"""
        with self._lock:
            threshold_value = self.thresholds.get_threshold(metric_type, level)
            
            alert = Alert(
                timestamp=metric.timestamp,
                level=level,
                metric_type=metric_type,
                message=f"{metric_type.value} is {level.value}: {metric.value}{metric.unit} (threshold: {threshold_value})",
                current_value=metric.value,
                threshold_value=threshold_value,
                metadata=metric.metadata
            )
            
            self.alerts.append(alert)
            
            # Ejecutar callbacks de alerta
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
            
            logger.warning(f"Performance alert: {alert.message}")
    
    def record_api_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Registra una request de API"""
        with self._lock:
            timestamp = datetime.now(timezone.utc)
            
            self.api_stats["total_requests"] += 1
            self.api_stats["active_requests"] = max(0, self.api_stats["active_requests"] - 1)
            
            if 200 <= status_code < 400:
                self.api_stats["successful_requests"] += 1
            else:
                self.api_stats["failed_requests"] += 1
            
            self.api_stats["response_times"].append(response_time)
            
            # Estadísticas por endpoint
            endpoint_key = f"{method} {endpoint}"
            self.api_stats["endpoints"][endpoint_key]["count"] += 1
            self.api_stats["endpoints"][endpoint_key]["total_time"] += response_time
            
            if status_code >= 400:
                self.api_stats["endpoints"][endpoint_key]["errors"] += 1
            
            # Crear métrica de tiempo de respuesta
            self._add_metric(MetricType.API_RESPONSE_TIME, response_time, "ms", timestamp, {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code
            })
    
    def start_request(self, endpoint: str, method: str):
        """Inicia el tracking de una request"""
        with self._lock:
            self.api_stats["active_requests"] += 1
            
            # Crear métrica de requests activos
            timestamp = datetime.now(timezone.utc)
            self._add_metric(MetricType.ACTIVE_REQUESTS, self.api_stats["active_requests"], "requests", timestamp, {
                "endpoint": endpoint,
                "method": method
            })
    
    def record_database_query(self, query_type: str, execution_time: float, success: bool = True):
        """Registra una query de base de datos"""
        with self._lock:
            timestamp = datetime.now(timezone.utc)
            
            self.db_stats["total_queries"] += 1
            self.db_stats["query_times"].append(execution_time)
            
            if not success or execution_time > 1000:  # Queries lentas o fallidas
                self.db_stats["slow_queries"].append({
                    "timestamp": timestamp,
                    "query_type": query_type,
                    "execution_time": execution_time,
                    "success": success
                })
            
            # Crear métrica de tiempo de query
            self._add_metric(MetricType.DATABASE_QUERY_TIME, execution_time, "ms", timestamp, {
                "query_type": query_type,
                "success": success
            })
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Registra una operación de cache"""
        with self._lock:
            timestamp = datetime.now(timezone.utc)
            
            if hit:
                self.cache_stats["hits"] += 1
            else:
                self.cache_stats["misses"] += 1
            
            self.cache_stats["operations"].append({
                "timestamp": timestamp,
                "operation": operation,
                "hit": hit
            })
            
            # Calcular hit rate
            total_operations = self.cache_stats["hits"] + self.cache_stats["misses"]
            if total_operations > 0:
                hit_rate = (self.cache_stats["hits"] / total_operations) * 100
                
                # Crear métrica de hit rate
                self._add_metric(MetricType.CACHE_HIT_RATE, hit_rate, "%", timestamp, {
                    "operation": operation,
                    "total_operations": total_operations
                })
    
    def update_system_metrics(self):
        """Actualiza métricas del sistema (simuladas para Vercel)"""
        with self._lock:
            timestamp = datetime.now(timezone.utc)
            
            # Simular uso de memoria (en Vercel no tenemos acceso a psutil)
            import random
            memory_usage = 40 + random.random() * 40  # Entre 40% y 80%
            self._add_metric(MetricType.MEMORY_USAGE, memory_usage, "%", timestamp)
            
            # Calcular requests por minuto
            current_minute = timestamp.replace(second=0, microsecond=0)
            recent_requests = [req for req in self.api_stats["response_times"] 
                             if datetime.fromtimestamp(time.time() - (time.time() % 60), tz=timezone.utc) <= current_minute]
            requests_per_minute = len(recent_requests)
            
            self._add_metric(MetricType.REQUEST_COUNT, requests_per_minute, "requests/min", timestamp)
    
    def get_metrics_summary(self, metric_type: Optional[MetricType] = None, hours: int = 1) -> Dict[str, Any]:
        """Obtiene un resumen de las métricas"""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            if metric_type:
                metrics_to_check = [metric_type]
            else:
                metrics_to_check = list(MetricType)
            
            summary = {}
            
            for mtype in metrics_to_check:
                if mtype not in self.metrics:
                    continue
                
                recent_metrics = [m for m in self.metrics[mtype] if m.timestamp >= cutoff_time]
                
                if not recent_metrics:
                    continue
                
                values = [m.value for m in recent_metrics]
                
                summary[mtype.value] = {
                    "count": len(values),
                    "latest": values[-1] if values else None,
                    "average": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                    "unit": recent_metrics[0].unit if recent_metrics else None
                }
            
            return summary
    
    def get_alerts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene un resumen de las alertas"""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
            
            alert_counts = defaultdict(int)
            for alert in recent_alerts:
                alert_counts[f"{alert.level.value}_{alert.metric_type.value}"] += 1
            
            return {
                "total_alerts": len(recent_alerts),
                "alert_counts": dict(alert_counts),
                "recent_alerts": [a.to_dict() for a in recent_alerts[-10:]]  # Últimas 10 alertas
            }
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de API"""
        with self._lock:
            total_requests = self.api_stats["total_requests"]
            error_rate = 0
            
            if total_requests > 0:
                error_rate = (self.api_stats["failed_requests"] / total_requests) * 100
            
            avg_response_time = 0
            if self.api_stats["response_times"]:
                avg_response_time = sum(self.api_stats["response_times"]) / len(self.api_stats["response_times"])
            
            # Top endpoints por tiempo total
            endpoint_stats = []
            for endpoint, stats in self.api_stats["endpoints"].items():
                avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
                endpoint_stats.append({
                    "endpoint": endpoint,
                    "count": stats["count"],
                    "total_time": stats["total_time"],
                    "avg_time": avg_time,
                    "errors": stats["errors"],
                    "error_rate": (stats["errors"] / stats["count"] * 100) if stats["count"] > 0 else 0
                })
            
            endpoint_stats.sort(key=lambda x: x["total_time"], reverse=True)
            
            return {
                "total_requests": total_requests,
                "successful_requests": self.api_stats["successful_requests"],
                "failed_requests": self.api_stats["failed_requests"],
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "active_requests": self.api_stats["active_requests"],
                "top_endpoints": endpoint_stats[:10]
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de cache"""
        with self._lock:
            total_operations = self.cache_stats["hits"] + self.cache_stats["misses"]
            hit_rate = 0
            
            if total_operations > 0:
                hit_rate = (self.cache_stats["hits"] / total_operations) * 100
            
            return {
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "total_operations": total_operations,
                "hit_rate": hit_rate
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtiene el estado general del sistema"""
        with self._lock:
            # Obtener métricas recientes
            recent_metrics = self.get_metrics_summary(hours=1)
            recent_alerts = self.get_alerts_summary(hours=1)
            
            # Calcular health score (0-100)
            health_score = 100
            
            # Penalizar por alertas críticas
            critical_alerts = len([a for a in self.alerts 
                                 if a.level == AlertLevel.CRITICAL and 
                                 a.timestamp >= datetime.now(timezone.utc) - timedelta(hours=1)])
            health_score -= critical_alerts * 20
            
            # Penalizar por alertas de warning
            warning_alerts = len([a for a in self.alerts 
                                if a.level == AlertLevel.WARNING and 
                                a.timestamp >= datetime.now(timezone.utc) - timedelta(hours=1)])
            health_score -= warning_alerts * 5
            
            # Penalizar por alta tasa de error
            api_stats = self.get_api_stats()
            if api_stats["error_rate"] > 5:
                health_score -= (api_stats["error_rate"] - 5) * 2
            
            # Penalizar por tiempos de respuesta altos
            if "api_response_time" in recent_metrics:
                avg_response_time = recent_metrics["api_response_time"]["average"]
                if avg_response_time > 2000:
                    health_score -= min(20, (avg_response_time - 2000) / 100)
            
            health_score = max(0, min(100, health_score))
            
            # Determinar estado general
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 70:
                status = "good"
            elif health_score >= 50:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "health_score": round(health_score, 1),
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics_summary": recent_metrics,
                "alerts_summary": recent_alerts,
                "api_stats": api_stats,
                "cache_stats": self.get_cache_stats()
            }
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Agrega un callback para alertas"""
        self.alert_callbacks.append(callback)
    
    def clear_old_data(self, hours: int = 24):
        """Limpia datos antiguos (más de X horas)"""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Limpiar métricas antiguas
            for metric_type in self.metrics:
                while self.metrics[metric_type] and self.metrics[metric_type][0].timestamp < cutoff_time:
                    self.metrics[metric_type].popleft()
            
            # Limpiar alertas antiguas
            while self.alerts and self.alerts[0].timestamp < cutoff_time:
                self.alerts.popleft()
            
            logger.info(f"Cleared performance data older than {hours} hours")

# Instancia global del monitor
vercel_performance_monitor = VercelPerformanceMonitor()

# Decorador para monitorear funciones
def monitor_performance_vercel(operation_name: str = None):
    """Decorador para monitorear el performance de funciones en Vercel"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            start_time = time.time()
            
            try:
                # Si es un request de FastAPI, registrar inicio
                if hasattr(args[0] if args else None, 'url'):
                    request = args[0]
                    vercel_performance_monitor.start_request(
                        str(request.url.path),
                        request.method
                    )
                
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # ms
                
                # Registrar como operación de API si es una función de endpoint
                if hasattr(args[0] if args else None, 'url'):
                    request = args[0]
                    vercel_performance_monitor.record_api_request(
                        str(request.url.path),
                        request.method,
                        execution_time,
                        200
                    )
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                # Registrar error
                if hasattr(args[0] if args else None, 'url'):
                    request = args[0]
                    vercel_performance_monitor.record_api_request(
                        str(request.url.path),
                        request.method,
                        execution_time,
                        500
                    )
                
                raise
        
        def sync_wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                # Registrar operación de base de datos si es relevante
                if 'query' in operation.lower() or 'db' in operation.lower():
                    vercel_performance_monitor.record_database_query(operation, execution_time, True)
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                # Registrar error de base de datos
                if 'query' in operation.lower() or 'db' in operation.lower():
                    vercel_performance_monitor.record_database_query(operation, execution_time, False)
                
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator
