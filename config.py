"""
Configuración centralizada para Immermex Dashboard
"""

import os
from typing import List

class Config:
    """Configuración de la aplicación"""
    
    # Base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")
    
    # Entorno
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Logging
    ENABLE_FILE_LOGGING = os.getenv("ENABLE_FILE_LOGGING", "").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://edu-maass.github.io"
    ]
    
    # Archivos
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = ['.xlsx', '.xls']
    
    # Rendimiento
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutos
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "immermex-secret-key-change-in-production")
    
    @classmethod
    def is_production(cls) -> bool:
        """Verifica si está en producción"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Verifica si está en desarrollo"""
        return cls.ENVIRONMENT.lower() == "development"
