"""
Utilidades de seguridad y validación para la API
"""
import re
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import logging

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

logger = logging.getLogger(__name__)

# Configuración de seguridad
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_FILE_TYPES = ['.xlsx', '.xls']
MAX_REQUESTS_PER_MINUTE = 100
MAX_REQUESTS_PER_HOUR = 1000

# Rate limiting storage (en producción usar Redis)
rate_limit_storage: Dict[str, List[datetime]] = {}

class SecurityValidator:
    """Validador de seguridad para la API"""
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Valida que el archivo sea de tipo permitido"""
        if not filename:
            return False
        
        file_extension = filename.lower().split('.')[-1]
        return f'.{file_extension}' in ALLOWED_FILE_TYPES
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Valida que el archivo no exceda el tamaño máximo"""
        return file_size <= MAX_FILE_SIZE
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza el nombre del archivo"""
        if not filename:
            return "unknown_file"
        
        # Remover caracteres peligrosos
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Limitar longitud
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:255-len(ext)-1] + (f'.{ext}' if ext else '')
        
        return sanitized
    
    @staticmethod
    def validate_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y sanitiza datos de entrada"""
        sanitized_data = {}
        
        for key, value in data.items():
            # Validar clave
            if not isinstance(key, str) or len(key) > 100:
                raise ValueError(f"Invalid key: {key}")
            
            # Sanitizar clave
            sanitized_key = re.sub(r'[^\w\-_]', '_', key)
            
            # Validar y sanitizar valor
            if isinstance(value, str):
                # Limitar longitud de strings
                if len(value) > 10000:
                    raise ValueError(f"Value too long for key: {key}")
                # Escapar caracteres especiales
                sanitized_value = value.replace('<', '&lt;').replace('>', '&gt;')
            elif isinstance(value, (int, float)):
                # Validar números
                if isinstance(value, int) and (value < -2147483648 or value > 2147483647):
                    raise ValueError(f"Integer out of range for key: {key}")
                sanitized_value = value
            elif isinstance(value, bool):
                sanitized_value = value
            elif value is None:
                sanitized_value = None
            else:
                raise ValueError(f"Invalid value type for key: {key}")
            
            sanitized_data[sanitized_key] = sanitized_value
        
        return sanitized_data
    
    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Valida filtros de búsqueda"""
        allowed_filters = {
            'fecha_inicio', 'fecha_fin', 'cliente', 'agente', 
            'pedidos', 'material', 'mes', 'año'
        }
        
        validated_filters = {}
        
        for key, value in filters.items():
            if key not in allowed_filters:
                logger.warning(f"Unknown filter key: {key}")
                continue
            
            # Validar fechas
            if key in ['fecha_inicio', 'fecha_fin']:
                if isinstance(value, str):
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                        validated_filters[key] = value
                    except ValueError:
                        raise ValueError(f"Invalid date format for {key}")
                elif isinstance(value, datetime):
                    validated_filters[key] = value.isoformat()
            
            # Validar listas
            elif key == 'pedidos' and isinstance(value, list):
                if len(value) > 100:
                    raise ValueError("Too many pedidos in filter")
                validated_filters[key] = [str(p) for p in value if str(p)]
            
            # Validar strings
            elif key in ['cliente', 'agente', 'material']:
                if isinstance(value, str) and len(value) <= 255:
                    validated_filters[key] = value.strip()
            
            # Validar números
            elif key in ['mes', 'año']:
                if isinstance(value, int) and 1 <= value <= 12 if key == 'mes' else 1900 <= value <= 2100:
                    validated_filters[key] = value
        
        return validated_filters

class RateLimiter:
    """Rate limiter para controlar el número de requests"""
    
    @staticmethod
    def check_rate_limit(client_ip: str, endpoint: str = "general") -> bool:
        """Verifica si el cliente ha excedido el límite de rate"""
        key = f"{client_ip}:{endpoint}"
        now = datetime.utcnow()
        
        # Limpiar requests antiguos
        if key in rate_limit_storage:
            rate_limit_storage[key] = [
                req_time for req_time in rate_limit_storage[key]
                if now - req_time < timedelta(minutes=1)
            ]
        else:
            rate_limit_storage[key] = []
        
        # Verificar límite por minuto
        if len(rate_limit_storage[key]) >= MAX_REQUESTS_PER_MINUTE:
            return False
        
        # Agregar request actual
        rate_limit_storage[key].append(now)
        return True
    
    @staticmethod
    def get_remaining_requests(client_ip: str, endpoint: str = "general") -> int:
        """Obtiene el número de requests restantes"""
        key = f"{client_ip}:{endpoint}"
        
        if key not in rate_limit_storage:
            return MAX_REQUESTS_PER_MINUTE
        
        now = datetime.utcnow()
        recent_requests = [
            req_time for req_time in rate_limit_storage[key]
            if now - req_time < timedelta(minutes=1)
        ]
        
        return max(0, MAX_REQUESTS_PER_MINUTE - len(recent_requests))

class SecurityHeaders:
    """Utilidades para headers de seguridad"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Retorna headers de seguridad estándar"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        }

# Decoradores de seguridad
def require_rate_limit(endpoint: str = "general"):
    """Decorador para aplicar rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            
            if not RateLimiter.check_rate_limit(client_ip, endpoint):
                remaining = RateLimiter.get_remaining_requests(client_ip, endpoint)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60,
                        "remaining_requests": remaining
                    }
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def validate_file_upload():
    """Decorador para validar uploads de archivos"""
    def decorator(func):
        @wraps(func)
        async def wrapper(file: Any, *args, **kwargs):
            # Validar tipo de archivo
            if not SecurityValidator.validate_file_type(file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Invalid file type",
                        "message": f"Only {', '.join(ALLOWED_FILE_TYPES)} files are allowed",
                        "allowed_types": ALLOWED_FILE_TYPES
                    }
                )
            
            # Validar tamaño de archivo
            if hasattr(file, 'size') and not SecurityValidator.validate_file_size(file.size):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error": "File too large",
                        "message": f"File size must be less than {MAX_FILE_SIZE / (1024*1024):.1f}MB",
                        "max_size_mb": MAX_FILE_SIZE / (1024*1024)
                    }
                )
            
            # Sanitizar nombre del archivo
            if hasattr(file, 'filename'):
                file.filename = SecurityValidator.sanitize_filename(file.filename)
            
            return await func(file, *args, **kwargs)
        return wrapper
    return decorator

def validate_input_data():
    """Decorador para validar datos de entrada"""
    def decorator(func):
        @wraps(func)
        async def wrapper(data: Dict[str, Any], *args, **kwargs):
            try:
                validated_data = SecurityValidator.validate_input_data(data)
                return await func(validated_data, *args, **kwargs)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Invalid input data",
                        "message": str(e),
                        "type": "ValidationError"
                    }
                )
        return wrapper
    return decorator

def validate_filters():
    """Decorador para validar filtros"""
    def decorator(func):
        @wraps(func)
        async def wrapper(filters: Dict[str, Any], *args, **kwargs):
            try:
                validated_filters = SecurityValidator.validate_filters(filters)
                return await func(validated_filters, *args, **kwargs)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Invalid filters",
                        "message": str(e),
                        "type": "ValidationError"
                    }
                )
        return wrapper
    return decorator

# Middleware de seguridad
class SecurityMiddleware:
    """Middleware para agregar headers de seguridad"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Agregar headers de seguridad
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    security_headers = SecurityHeaders.get_security_headers()
                    
                    for header, value in security_headers.items():
                        headers[header.lower().encode()] = value.encode()
                    
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
