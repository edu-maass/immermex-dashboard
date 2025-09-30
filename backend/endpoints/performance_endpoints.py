"""
Endpoints para monitoreo de performance en tiempo real
Compatible con Vercel (sin archivos locales)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone

from utils.vercel_performance_monitor import (
    vercel_performance_monitor, 
    monitor_performance_vercel,
    MetricType
)

logger = logging.getLogger(__name__)

# Crear router para endpoints de performance
performance_router = APIRouter(prefix="/api/performance", tags=["Performance Monitoring"])

@performance_router.get("/health")
@monitor_performance_vercel("system_health_check")
async def get_system_health():
    """Obtiene el estado general del sistema"""
    try:
        health_data = vercel_performance_monitor.get_system_health()
        return {
            "success": True,
            "data": health_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")

@performance_router.get("/metrics")
@monitor_performance_vercel("get_metrics")
async def get_performance_metrics(
    metric_type: Optional[str] = Query(None, description="Tipo de métrica específica"),
    hours: int = Query(1, description="Horas de datos a incluir", ge=1, le=24)
):
    """Obtiene métricas de performance"""
    try:
        # Convertir string a MetricType si se proporciona
        mtype = None
        if metric_type:
            try:
                mtype = MetricType(metric_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
        
        metrics_data = vercel_performance_monitor.get_metrics_summary(mtype, hours)
        
        return {
            "success": True,
            "data": {
                "metrics": metrics_data,
                "period_hours": hours,
                "metric_type": metric_type
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")

@performance_router.get("/alerts")
@monitor_performance_vercel("get_alerts")
async def get_performance_alerts(
    hours: int = Query(24, description="Horas de alertas a incluir", ge=1, le=168)
):
    """Obtiene alertas de performance"""
    try:
        alerts_data = vercel_performance_monitor.get_alerts_summary(hours)
        
        return {
            "success": True,
            "data": {
                "alerts": alerts_data,
                "period_hours": hours
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance alerts: {str(e)}")

@performance_router.get("/api-stats")
@monitor_performance_vercel("get_api_stats")
async def get_api_statistics():
    """Obtiene estadísticas detalladas de API"""
    try:
        api_stats = vercel_performance_monitor.get_api_stats()
        
        return {
            "success": True,
            "data": api_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting API statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting API statistics: {str(e)}")

@performance_router.get("/cache-stats")
@monitor_performance_vercel("get_cache_stats")
async def get_cache_statistics():
    """Obtiene estadísticas de cache"""
    try:
        cache_stats = vercel_performance_monitor.get_cache_stats()
        
        return {
            "success": True,
            "data": cache_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting cache statistics: {str(e)}")

@performance_router.get("/dashboard")
@monitor_performance_vercel("get_performance_dashboard")
async def get_performance_dashboard():
    """Obtiene datos completos para el dashboard de performance"""
    try:
        # Recopilar todos los datos de performance
        health_data = vercel_performance_monitor.get_system_health()
        api_stats = vercel_performance_monitor.get_api_stats()
        cache_stats = vercel_performance_monitor.get_cache_stats()
        recent_alerts = vercel_performance_monitor.get_alerts_summary(hours=1)
        
        # Actualizar métricas del sistema
        vercel_performance_monitor.update_system_metrics()
        
        dashboard_data = {
            "system_health": health_data,
            "api_statistics": api_stats,
            "cache_statistics": cache_stats,
            "recent_alerts": recent_alerts,
            "available_metrics": [metric.value for metric in MetricType],
            "thresholds": {
                "api_response_time": {"warning": 2000, "critical": 5000},
                "database_query_time": {"warning": 1000, "critical": 3000},
                "cache_hit_rate": {"warning": 70, "critical": 50},
                "error_rate": {"warning": 5, "critical": 10},
                "active_requests": {"warning": 50, "critical": 100},
                "memory_usage": {"warning": 80, "critical": 95}
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance dashboard: {str(e)}")

@performance_router.post("/clear-data")
@monitor_performance_vercel("clear_performance_data")
async def clear_old_performance_data(
    hours: int = Query(24, description="Datos más antiguos que estas horas serán eliminados", ge=1, le=168)
):
    """Limpia datos antiguos de performance"""
    try:
        vercel_performance_monitor.clear_old_data(hours)
        
        return {
            "success": True,
            "message": f"Performance data older than {hours} hours has been cleared",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing performance data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing performance data: {str(e)}")

@performance_router.get("/status")
@monitor_performance_vercel("performance_status")
async def get_performance_monitor_status():
    """Obtiene el estado del monitor de performance"""
    try:
        # Obtener información básica del monitor
        api_stats = vercel_performance_monitor.get_api_stats()
        cache_stats = vercel_performance_monitor.get_cache_stats()
        
        status_data = {
            "monitor_active": True,
            "total_requests_tracked": api_stats["total_requests"],
            "total_cache_operations": cache_stats["total_operations"],
            "memory_usage": "In-memory only (Vercel compatible)",
            "data_retention": "24 hours (configurable)",
            "alert_callbacks": len(vercel_performance_monitor.alert_callbacks),
            "available_endpoints": [
                "/api/performance/health",
                "/api/performance/metrics",
                "/api/performance/alerts",
                "/api/performance/api-stats",
                "/api/performance/cache-stats",
                "/api/performance/dashboard",
                "/api/performance/clear-data",
                "/api/performance/status"
            ]
        }
        
        return {
            "success": True,
            "data": status_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance monitor status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance monitor status: {str(e)}")

# Endpoint para simular carga y probar el sistema de monitoreo
@performance_router.post("/test-load")
@monitor_performance_vercel("test_load_simulation")
async def simulate_load_test():
    """Simula una carga de trabajo para probar el sistema de monitoreo"""
    try:
        import time
        import random
        
        # Simular varias operaciones
        operations = []
        
        # Simular requests de API
        for i in range(5):
            response_time = random.uniform(100, 2000)  # 100ms a 2s
            status_code = 200 if random.random() > 0.1 else 500  # 90% éxito
            endpoint = f"/api/test/{i}"
            
            vercel_performance_monitor.record_api_request(endpoint, "GET", response_time, status_code)
            operations.append(f"API request to {endpoint}: {response_time:.1f}ms, status {status_code}")
        
        # Simular queries de base de datos
        for i in range(3):
            query_time = random.uniform(50, 1500)  # 50ms a 1.5s
            success = random.random() > 0.05  # 95% éxito
            
            vercel_performance_monitor.record_database_query(f"test_query_{i}", query_time, success)
            operations.append(f"Database query {i}: {query_time:.1f}ms, success: {success}")
        
        # Simular operaciones de cache
        for i in range(10):
            hit = random.random() > 0.3  # 70% hit rate
            vercel_performance_monitor.record_cache_operation(f"cache_op_{i}", hit)
        
        operations.append("10 cache operations simulated")
        
        # Actualizar métricas del sistema
        vercel_performance_monitor.update_system_metrics()
        
        return {
            "success": True,
            "message": "Load test simulation completed",
            "operations_performed": operations,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error in load test simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in load test simulation: {str(e)}")
