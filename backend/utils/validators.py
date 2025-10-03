"""
Validadores y utilidades de datos para Immermex Dashboard
Extrae funciones comunes de validación y conversión de datos
"""

import numpy as np
import logging
from datetime import datetime
from typing import Any, Union, Optional

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Clase para validación y conversión segura de datos
    """
    
    @staticmethod
    def is_nan_value(value: Any) -> bool:
        """Detecta si un valor es NaN de cualquier tipo"""
        if value is None:
            return True
        
        # Manejar pandas NaT específicamente
        if hasattr(value, '__class__') and str(value.__class__) == "<class 'pandas._libs.tslibs.nattype.NaTType'>":
            return True
        
        if isinstance(value, (int, float)):
            return np.isnan(value)
        if isinstance(value, str):
            value_lower = value.lower().strip()
            return value_lower in ['nan', 'none', 'null', 'nat', '']
        return False
    
    @staticmethod
    def safe_date(value: Any) -> Optional[datetime]:
        """Convierte valor a fecha segura, manejando NaN y NaT"""
        try:
            if DataValidator.is_nan_value(value):
                return None
            
            # Manejar pandas NaT específicamente
            if hasattr(value, '__class__') and str(value.__class__) == "<class 'pandas._libs.tslibs.nattype.NaTType'>":
                return None
            
            # Verificar si es pandas NaT usando numpy
            if isinstance(value, (int, float)) and np.isnan(value):
                return None
            
            if isinstance(value, datetime):
                return value
            if isinstance(value, (int, float)):
                return None  # Los números no son fechas válidas
            if isinstance(value, str):
                value = value.strip()
                if not value or value.lower() in ['nan', 'none', 'null', 'nat']:
                    return None
                # Intentar parsear como fecha
                try:
                    return datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    try:
                        return datetime.strptime(value, '%d/%m/%Y')
                    except ValueError:
                        return None
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Convierte valor a float seguro, manejando NaN"""
        try:
            if DataValidator.is_nan_value(value):
                return default
            if isinstance(value, str):
                value = value.strip()
                if not value or value.lower() in ['nan', 'none', 'null']:
                    return default
                # Remover caracteres no numéricos excepto punto y coma
                import re
                value = re.sub(r'[^\d.,-]', '', value)
                if not value:
                    return default
                # Reemplazar coma por punto para decimales
                value = value.replace(',', '.')
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 30) -> int:
        """Convierte valor a int seguro, manejando NaN"""
        try:
            if DataValidator.is_nan_value(value):
                return default
            if isinstance(value, str):
                value = value.strip()
                if not value or value.lower() in ['nan', 'none', 'null']:
                    return default
            return int(float(str(value).replace(',', '').strip()))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_string(value: Any, default: str = '') -> str:
        """Convierte valor a string seguro, manejando NaN"""
        try:
            if DataValidator.is_nan_value(value):
                return default
            result = str(value).strip()
            return result if result else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def validate_folio(folio: Any) -> Optional[str]:
        """Valida y limpia un folio de factura"""
        if not folio:
            return None
        
        folio_str = DataValidator.safe_string(folio)
        
        # Filtrar folios que parecen totales
        if folio_str.lower().startswith(('total', 'suma', 'subtotal')):
            return None
            
        return folio_str if folio_str else None
    
    @staticmethod
    def validate_uuid(uuid: Any) -> Optional[str]:
        """Valida y limpia un UUID"""
        if not uuid:
            return None
            
        uuid_str = DataValidator.safe_string(uuid).strip().upper()
        
        # Patrón básico de UUID
        import re
        uuid_pattern = r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$'
        
        if re.match(uuid_pattern, uuid_str):
            return uuid_str
        
        return None
