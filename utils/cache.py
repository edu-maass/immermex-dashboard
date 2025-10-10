"""
Sistema de caché para optimizar consultas frecuentes
"""

import time
import json
import hashlib
from typing import Any, Dict, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """
    Sistema de caché simple en memoria para optimizar consultas frecuentes
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutos por defecto
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Genera una clave única para el caché"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si no ha expirado"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guarda un valor en el caché"""
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        logger.debug(f"Cache set for key: {key}, TTL: {ttl}s")
    
    def delete(self, key: str) -> None:
        """Elimina una entrada del caché"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self) -> None:
        """Limpia todo el caché"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché"""
        current_time = time.time()
        active_entries = sum(1 for entry in self._cache.values() 
                           if current_time <= entry['expires_at'])
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries,
            'memory_usage': len(str(self._cache))
        }

# Instancia global del caché
cache = SimpleCache(default_ttl=300)  # 5 minutos

def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorador para cachear el resultado de funciones
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Intentar obtener del caché
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y guardar resultado
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalida entradas del caché que coincidan con un patrón
    """
    deleted_count = 0
    keys_to_delete = []
    
    for key in cache._cache.keys():
        if pattern in key:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache.delete(key)
        deleted_count += 1
    
    logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
    return deleted_count

# Funciones de utilidad para caché específico
def cache_kpis(ttl: int = 300):
    """Decorador específico para KPIs"""
    return cached("kpis", ttl)

def cache_filtros(ttl: int = 600):
    """Decorador específico para filtros (10 minutos)"""
    return cached("filtros", ttl)

def cache_graficos(ttl: int = 300):
    """Decorador específico para gráficos"""
    return cached("graficos", ttl)

def invalidate_data_cache():
    """Invalida todo el caché relacionado con datos"""
    patterns = ["kpis", "filtros", "graficos", "summary"]
    total_deleted = 0
    for pattern in patterns:
        total_deleted += invalidate_cache_pattern(pattern)
    return total_deleted
