"""
Utilidades para el sistema Immermex Dashboard
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

def setup_logging() -> logging.Logger:
    """Configura el sistema de logging"""
    logger = logging.getLogger(__name__)
    
    if not logger.handlers:
        # Configurar nivel de logging
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Crear handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger.level)
        
        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Agregar handler al logger
        logger.addHandler(console_handler)
    
    return logger

def handle_api_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Maneja errores de API de forma consistente"""
    logger = logging.getLogger(__name__)
    
    error_message = str(error)
    logger.error(f"API Error {context}: {error_message}")
    
    return {
        "error": True,
        "message": error_message,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }

class FileProcessingError(Exception):
    """Excepción específica para errores de procesamiento de archivos"""
    pass

class DatabaseError(Exception):
    """Excepción específica para errores de base de datos"""
    pass

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convierte un valor a float de forma segura"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Convierte un valor a int de forma segura"""
    if value is None or value == '':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_string(value: Any, default: str = '') -> str:
    """Convierte un valor a string de forma segura"""
    if value is None:
        return default
    return str(value).strip() if str(value).strip() != 'nan' else default

def format_currency(amount: float, currency: str = 'MXN') -> str:
    """Formatea un monto como moneda"""
    if currency == 'USD':
        return f"${amount:,.2f} USD"
    else:
        return f"${amount:,.2f} MXN"

def format_number(number: float, decimals: int = 2) -> str:
    """Formatea un número con separadores de miles"""
    return f"{number:,.{decimals}f}"

def validate_email(email: str) -> bool:
    """Valida un email de forma básica"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_file_extension(filename: str) -> str:
    """Obtiene la extensión de un archivo"""
    return os.path.splitext(filename)[1].lower()

def is_excel_file(filename: str) -> bool:
    """Verifica si un archivo es Excel"""
    excel_extensions = ['.xlsx', '.xls']
    return get_file_extension(filename) in excel_extensions

def format_file_size(size_bytes: int) -> str:
    """Formatea el tamaño de un archivo en formato legible"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """Limpia un nombre de archivo removiendo caracteres no válidos"""
    import re
    # Remover caracteres no válidos para nombres de archivo
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remover espacios múltiples
    cleaned = re.sub(r'\s+', '_', cleaned)
    return cleaned.strip('_')

def get_current_timestamp() -> str:
    """Obtiene el timestamp actual en formato ISO"""
    return datetime.now().isoformat()

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parsea una cadena de fecha en diferentes formatos"""
    if not date_str or date_str.strip() == '':
        return None
    
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None

def calculate_percentage(part: float, total: float) -> float:
    """Calcula el porcentaje de una parte sobre el total"""
    if total == 0:
        return 0.0
    return (part / total) * 100

def round_to_decimals(value: float, decimals: int = 2) -> float:
    """Redondea un valor a un número específico de decimales"""
    return round(value, decimals)

def is_valid_currency_code(currency: str) -> bool:
    """Valida si un código de moneda es válido"""
    valid_currencies = ['USD', 'MXN', 'EUR', 'CAD', 'GBP']
    return currency.upper() in valid_currencies

def generate_unique_id() -> str:
    """Genera un ID único basado en timestamp"""
    import uuid
    return str(uuid.uuid4())

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Enmascara datos sensibles mostrando solo algunos caracteres"""
    if len(data) <= visible_chars:
        return '*' * len(data)
    
    return data[:visible_chars] + '*' * (len(data) - visible_chars)
