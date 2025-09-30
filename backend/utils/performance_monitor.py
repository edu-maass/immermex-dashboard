"""
Sistema de monitoreo de performance en tiempo real para Immermex Dashboard
"""
import time
import psutil
import threading
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
from collections import deque, defaultdict
import weakref

logger = logging.getLogger(__name__)

class MetricType(Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    API_RESPONSE_TIME = "api_response_time"
    DATABASE_QUERY_TIME = "database_query_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    ACTIVE_CONNECTIONS = "active_connections"

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

class PerformanceThresholds:
    """Configuración de umbrales para alertas de performance"""
    
    def __init__(self):
        self.thresholds = {
            MetricType.CPU_USAGE: {"warning": 70.0, "critical": 90.0},
            MetricType.MEMORY_USAGE: {"warning": 80.0, "critical": 95.0},
            MetricType.DISK_USAGE: {"warning": 85.0, "critical": 95.0},
            MetricType.API_RESPONSE_TIME: {"warning": 1000.0, "critical": 3000.0},  # ms
            MetricType.DATABASE_QUERY_TIME: {"warning": 500.0, "critical": 2000.0},  # ms
            MetricType.CACHE_HIT_RATE: {"warning": 70.0, "critical": 50.0},  # %
            MetricType.ERROR_RATE: {"warning": 5.0, "critical": 10.0},  # %
            MetricType.ACTIVE_CONNECTIONS: {"warning": 100, "critical": 200}
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

class PerformanceMonitor:
    """Monitor de performance en tiempo real"""
    
    def __init__(self, collection_interval: int = 30, max_metrics: int = 1000):
        self.collection_interval = collection_interval
        self.max_metrics = max_metrics
        self.thresholds = PerformanceThresholds()
        
        # Almacenamiento de métricas
        self.metrics: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self.alerts: deque = deque(maxlen=100)
        
        # Estadísticas de API
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": deque(maxlen=100),
            "endpoints": defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
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
        
        # Estado del monitor
        self.is_running = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        # Callbacks para alertas
        self.alert_callbacks: List[Callable] = []
    
    def start_monitoring(self):
        """Inicia el monitoreo en un hilo separado"""
        if self.is_running:
            return
        
        self.is_running = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while not self._stop_event.wait(self.collection_interval):
            try:
                self._collect_system_metrics()
                self._check_thresholds()
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")
    
    def _collect_system_metrics(self):
        """Recolecta métricas del sistema"""
        timestamp = datetime.now(timezone.utc)
        
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric(MetricType.CPU_USAGE, cpu_percent, "%", timestamp)
            
            # Memory Usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self._add_metric(MetricType.MEMORY_USAGE, memory_percent, "%", timestamp)
            
            # Disk Usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._add_metric(MetricType.DISK_USAGE, disk_percent, "%", timestamp)
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            self._add_metric(MetricType.NETWORK_IO, 0, "bytes", timestamp, network_io)
            
            # Active Connections (aproximado)
            connections = len(psutil.net_connections())
            self._add_metric(MetricType.ACTIVE_CONNECTIONS, connections, "connections", timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _add_metric(self, metric_type: MetricType, value: float, unit: str, timestamp: datetime, metadata: Dict[str, Any] = None):
        """Agrega una métrica al almacenamiento"""
        metric = PerformanceMetric(timestamp, metric_type, value, unit, metadata)
        self.metrics[metric_type].append(metric)
    
    def _check_thresholds(self):
        """Verifica si las métricas exceden los umbrales"""
        for metric_type, metrics in self.metrics.items():
            if not metrics:
                continue
            
            latest_metric = metrics[-1]
            alert_level = self.thresholds.check_threshold(metric_type, latest_metric.value)
            
            if alert_level:
                self._create_alert(alert_level, metric_type, latest_metric)
    
    def _create_alert(self, level: AlertLevel, metric_type: MetricType, metric: PerformanceMetric):
        """Crea una alerta"""
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
        self.api_stats["total_requests"] += 1
        
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
        timestamp = datetime.now(timezone.utc)
        self._add_metric(MetricType.API_RESPONSE_TIME, response_time, "ms", timestamp, {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        })
        
        # Verificar umbral de tiempo de respuesta
        alert_level = self.thresholds.check_threshold(MetricType.API_RESPONSE_TIME, response_time)
        if alert_level:
            self._create_alert(alert_level, MetricType.API_RESPONSE_TIME, 
                             PerformanceMetric(timestamp, MetricType.API_RESPONSE_TIME, response_time, "ms", {
                                 "endpoint": endpoint,
                                 "method": method,
                                 "status_code": status_code
                             }))
    
    def record_database_query(self, query_type: str, execution_time: float, success: bool = True):
        """Registra una query de base de datos"""
        self.db_stats["total_queries"] += 1
        self.db_stats["query_times"].append(execution_time)
        
        if not success or execution_time > 1000:  # Queries lentas o fallidas
            self.db_stats["slow_queries"].append({
                "timestamp": datetime.now(timezone.utc),
                "query_type": query_type,
                "execution_time": execution_time,
                "success": success
            })
        
        # Crear métrica de tiempo de query
        timestamp = datetime.now(timezone.utc)
        self._add_metric(MetricType.DATABASE_QUERY_TIME, execution_time, "ms", timestamp, {
            "query_type": query_type,
            "success": success
        })
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Registra una operación de cache"""
        if hit:
            self.cache_stats["hits"] += 1
        else:
            self.cache_stats["misses"] += 1
        
        self.cache_stats["operations"].append({
            "timestamp": datetime.now(timezone.utc),
            "operation": operation,
            "hit": hit
        })
        
        # Calcular hit rate
        total_operations = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_operations > 0:
            hit_rate = (self.cache_stats["hits"] / total_operations) * 100
            
            # Crear métrica de hit rate
            timestamp = datetime.now(timezone.utc)
            self._add_metric(MetricType.CACHE_HIT_RATE, hit_rate, "%", timestamp, {
                "operation": operation,
                "total_operations": total_operations
            })
    
    def get_metrics_summary(self, metric_type: Optional[MetricType] = None, hours: int = 1) -> Dict[str, Any]:
        """Obtiene un resumen de las métricas"""
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
            "top_endpoints": endpoint_stats[:10]
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de cache"""
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
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Agrega un callback para alertas"""
        self.alert_callbacks.append(callback)
    
    def clear_old_data(self, days: int = 7):
        """Limpia datos antiguos"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Limpiar métricas antiguas
        for metric_type in self.metrics:
            while self.metrics[metric_type] and self.metrics[metric_type][0].timestamp < cutoff_time:
                self.metrics[metric_type].popleft()
        
        # Limpiar alertas antiguas
        while self.alerts and self.alerts[0].timestamp < cutoff_time:
            self.alerts.popleft()
        
        logger.info(f"Cleared performance data older than {days} days")

# Instancia global del monitor
performance_monitor = PerformanceMonitor()

# Decorador para monitorear funciones
def monitor_performance(operation_name: str = None):
    """Decorador para monitorear el performance de funciones"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                operation = operation_name or func.__name__
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000  # ms
                    
                    # Registrar como operación de API si es una función de endpoint
                    if hasattr(args[0] if args else None, 'url'):
                        # Es un request de FastAPI
                        request = args[0]
                        performance_monitor.record_api_request(
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
                        performance_monitor.record_api_request(
                            str(request.url.path),
                            request.method,
                            execution_time,
                            500
                        )
                    
                    raise
            
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                operation = operation_name or func.__name__
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Registrar operación de base de datos si es relevante
                    if 'query' in operation.lower() or 'db' in operation.lower():
                        performance_monitor.record_database_query(operation, execution_time, True)
                    
                    return result
                    
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Registrar error de base de datos
                    if 'query' in operation.lower() or 'db' in operation.lower():
                        performance_monitor.record_database_query(operation, execution_time, False)
                    
                    raise
            
            return sync_wrapper
    return decorator
