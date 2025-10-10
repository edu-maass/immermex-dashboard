"""
Middleware avanzado de logging para FastAPI
"""
import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from .advanced_logging import api_logger, LogCategory, LogLevel

class AdvancedLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware avanzado de logging para requests y responses"""
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/favicon.ico", "/docs", "/openapi.json", "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa requests con logging detallado"""
        
        # Generar ID único para el request
        request_id = str(uuid.uuid4())
        
        # Agregar request_id al request para uso posterior
        request.state.request_id = request_id
        
        # Verificar si el path debe ser excluido del logging detallado
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Información del request
        start_time = time.time()
        
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Log del request
        api_logger.info(
            f"Request started: {request.method} {request.url.path}",
            LogCategory.API,
            **request_info
        )
        
        # Procesar el request
        try:
            response = await call_next(request)
            
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Información del response
            response_info = {
                **request_info,
                "status_code": response.status_code,
                "response_headers": self._sanitize_headers(dict(response.headers)),
                "execution_time": process_time * 1000,  # Convertir a ms
                "success": 200 <= response.status_code < 400
            }
            
            # Log del response según el status code
            if response.status_code >= 500:
                api_logger.error(
                    f"Request completed with server error: {request.method} {request.url.path}",
                    LogCategory.API,
                    **response_info
                )
            elif response.status_code >= 400:
                api_logger.warning(
                    f"Request completed with client error: {request.method} {request.url.path}",
                    LogCategory.API,
                    **response_info
                )
            else:
                api_logger.info(
                    f"Request completed successfully: {request.method} {request.url.path}",
                    LogCategory.API,
                    **response_info
                )
            
            # Agregar headers de respuesta con información de logging
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Información del error
            error_info = {
                **request_info,
                "execution_time": process_time * 1000,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "success": False
            }
            
            # Log del error
            api_logger.error(
                f"Request failed with exception: {request.method} {request.url.path}",
                LogCategory.API,
                exc_info=True,
                **error_info
            )
            
            raise
    
    def _should_exclude_path(self, path: str) -> bool:
        """Verifica si el path debe ser excluido del logging detallado"""
        return any(path.startswith(exclude_path) for exclude_path in self.exclude_paths)
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitiza headers sensibles"""
        sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token",
            "x-access-token", "x-refresh-token", "x-csrf-token"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de performance específico"""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Loggea performance de requests"""
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            
            # Log de performance si el request es lento
            if process_time > self.slow_request_threshold:
                api_logger.performance(
                    f"Slow request: {request.method} {request.url.path}",
                    process_time,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    client_ip=request.client.host if request.client else None
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log de performance para requests que fallan
            api_logger.performance(
                f"Failed request: {request.method} {request.url.path}",
                process_time,
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                client_ip=request.client.host if request.client else None
            )
            
            raise

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de auditoría"""
    
    def __init__(self, app: ASGIApp, audit_paths: list = None):
        super().__init__(app)
        self.audit_paths = audit_paths or [
            "/api/upload", "/api/filtros/pedidos/aplicar", 
            "/api/system/cache/clear", "/api/system/errors/cleanup"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Loggea operaciones que requieren auditoría"""
        
        # Verificar si el path requiere auditoría
        if not self._should_audit_path(request.url.path):
            return await call_next(request)
        
        # Información de auditoría
        audit_info = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "query_params": dict(request.query_params),
        }
        
        # Agregar información del body si es relevante (solo para POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Leer el body del request
                body = await request.body()
                if body:
                    # Solo loggear el tamaño del body, no el contenido completo
                    audit_info["body_size"] = len(body)
                    
                    # Para uploads, agregar información específica
                    if "/upload" in request.url.path:
                        audit_info["upload_operation"] = True
                        # Extraer información del filename si está disponible
                        content_disposition = request.headers.get("content-disposition", "")
                        if "filename=" in content_disposition:
                            filename = content_disposition.split("filename=")[1].strip('"')
                            audit_info["filename"] = filename
                
                # Recrear el request con el body para que pueda ser procesado
                from starlette.requests import Request as StarletteRequest
                scope = request.scope.copy()
                scope["body"] = body
                request = StarletteRequest(scope)
                
            except Exception as e:
                audit_info["body_read_error"] = str(e)
        
        # Log de auditoría del request
        api_logger.audit(
            action=f"API_REQUEST_{request.method}",
            resource=request.url.path,
            **audit_info
        )
        
        try:
            response = await call_next(request)
            
            # Log de auditoría del response
            api_logger.audit(
                action=f"API_RESPONSE_{response.status_code}",
                resource=request.url.path,
                request_id=getattr(request.state, "request_id", None),
                status_code=response.status_code,
                success=200 <= response.status_code < 400
            )
            
            return response
            
        except Exception as e:
            # Log de auditoría del error
            api_logger.audit(
                action="API_ERROR",
                resource=request.url.path,
                request_id=getattr(request.state, "request_id", None),
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            raise
    
    def _should_audit_path(self, path: str) -> bool:
        """Verifica si el path requiere auditoría"""
        return any(path.startswith(audit_path) for audit_path in self.audit_paths)

# Decorador para logging de endpoints específicos
def log_endpoint(operation_name: str = None, include_request_body: bool = False):
    """Decorador para logging detallado de endpoints"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extraer información del request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            operation = operation_name or func.__name__
            request_id = getattr(request.state, "request_id", None) if request else None
            
            # Log de inicio
            api_logger.info(
                f"Endpoint called: {operation}",
                LogCategory.API,
                operation=operation,
                request_id=request_id,
                endpoint=request.url.path if request else None
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # Log de éxito
                api_logger.info(
                    f"Endpoint completed: {operation}",
                    LogCategory.API,
                    operation=operation,
                    request_id=request_id,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Log de error
                api_logger.error(
                    f"Endpoint failed: {operation}",
                    LogCategory.API,
                    operation=operation,
                    request_id=request_id,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator
