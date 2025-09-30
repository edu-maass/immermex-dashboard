"""
Middleware de manejo de errores para FastAPI
"""
import logging
import traceback
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .error_tracker import error_tracker, ErrorContext, ErrorCategory, ErrorSeverity, track_api_error

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para manejo centralizado de errores"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa requests y maneja errores"""
        
        # Crear contexto de error
        error_context = ErrorContext(
            request_id=request.headers.get("x-request-id"),
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            timestamp=None
        )
        
        try:
            response = await call_next(request)
            
            # Log de errores HTTP (4xx, 5xx)
            if response.status_code >= 400:
                await self._handle_http_error(request, response, error_context)
            
            return response
            
        except HTTPException as e:
            # Manejar excepciones HTTP de FastAPI
            return await self._handle_http_exception(e, error_context)
            
        except Exception as e:
            # Manejar excepciones no controladas
            return await self._handle_unhandled_exception(e, error_context)
    
    async def _handle_http_error(self, request: Request, response: Response, context: ErrorContext):
        """Maneja errores HTTP (4xx, 5xx)"""
        
        # Determinar severidad basada en el código de estado
        if response.status_code >= 500:
            severity = ErrorSeverity.HIGH
        elif response.status_code >= 400:
            severity = ErrorSeverity.MEDIUM
        else:
            severity = ErrorSeverity.LOW
        
        # Crear error artificial para tracking
        error = Exception(f"HTTP {response.status_code} on {request.method} {request.url.path}")
        
        # Trackear el error
        error_tracker.track_error(
            error=error,
            category=ErrorCategory.API,
            severity=severity,
            context=context,
            metadata={
                "status_code": response.status_code,
                "response_headers": dict(response.headers)
            }
        )
    
    async def _handle_http_exception(self, exc: HTTPException, context: ErrorContext) -> JSONResponse:
        """Maneja excepciones HTTP de FastAPI"""
        
        # Trackear el error
        track_api_error(
            exc,
            context=context,
            metadata={
                "status_code": exc.status_code,
                "detail": exc.detail
            }
        )
        
        # Retornar respuesta JSON estructurada
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException",
                "timestamp": context.timestamp.isoformat() if context.timestamp else None
            }
        )
    
    async def _handle_unhandled_exception(self, exc: Exception, context: ErrorContext) -> JSONResponse:
        """Maneja excepciones no controladas"""
        
        # Trackear el error como crítico
        error_tracker.track_error(
            error=exc,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            context=context,
            metadata={
                "traceback": traceback.format_exc()
            }
        )
        
        # Log del error crítico
        logger.critical(f"Unhandled exception: {exc}", exc_info=True)
        
        # Retornar respuesta de error genérica (no exponer detalles internos)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "status_code": 500,
                "message": "Error interno del servidor",
                "type": "InternalServerError",
                "timestamp": context.timestamp.isoformat() if context.timestamp else None
            }
        )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log de requests y responses"""
        
        start_time = time.time()
        
        # Log del request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        
        # Log del response
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        # Agregar header de tiempo de procesamiento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# Decorador para manejo de errores en endpoints
def handle_endpoint_errors(
    error_message: str = "Error procesando solicitud",
    log_error: bool = True,
    return_traceback: bool = False
):
    """Decorador para manejo de errores en endpoints"""
    
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-lanzar excepciones HTTP
                raise
            except Exception as e:
                # Manejar otras excepciones
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                
                # Crear contexto básico
                context = ErrorContext(
                    endpoint=func.__name__,
                    timestamp=None
                )
                
                # Trackear el error
                track_api_error(e, context=context)
                
                # Determinar si retornar traceback (solo en desarrollo)
                detail = error_message
                if return_traceback:
                    detail += f"\nTraceback: {traceback.format_exc()}"
                
                raise HTTPException(status_code=500, detail=detail)
        
        return wrapper
    return decorator

# Función para crear respuestas de error estructuradas
def create_error_response(
    message: str,
    status_code: int = 500,
    error_type: str = "InternalError",
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Crea una respuesta de error estructurada"""
    
    content = {
        "error": True,
        "status_code": status_code,
        "message": message,
        "type": error_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        content["details"] = details
    
    return JSONResponse(status_code=status_code, content=content)

# Función para validar y formatear errores de validación
def format_validation_errors(validation_errors: list) -> Dict[str, Any]:
    """Formatea errores de validación de Pydantic"""
    
    formatted_errors = {}
    for error in validation_errors:
        field = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else "unknown"
        formatted_errors[field] = {
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        }
    
    return formatted_errors
