"""
Utilidades de paginación para optimizar consultas grandes
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Query
from sqlalchemy import func
import math

class PaginationResult:
    """Resultado de una consulta paginada"""
    
    def __init__(self, items: List[Any], page: int, per_page: int, total: int):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = math.ceil(total / per_page) if per_page > 0 else 0
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

def paginate(query: Query, page: int = 1, per_page: int = 50, max_per_page: int = 100) -> PaginationResult:
    """
    Pagina una consulta SQLAlchemy
    
    Args:
        query: Consulta SQLAlchemy
        page: Número de página (empezando en 1)
        per_page: Elementos por página
        max_per_page: Máximo elementos por página permitidos
    
    Returns:
        PaginationResult con los elementos paginados
    """
    # Validar parámetros
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 50
    if per_page > max_per_page:
        per_page = max_per_page
    
    # Contar total de elementos
    total = query.count()
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Obtener elementos de la página
    items = query.offset(offset).limit(per_page).all()
    
    return PaginationResult(
        items=items,
        page=page,
        per_page=per_page,
        total=total
    )

def paginate_dict(data: List[Dict[str, Any]], page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """
    Pagina una lista de diccionarios en memoria
    
    Args:
        data: Lista de diccionarios
        page: Número de página (empezando en 1)
        per_page: Elementos por página
    
    Returns:
        Diccionario con datos paginados
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 50
    
    total = len(data)
    pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    items = data[start_idx:end_idx]
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_prev": page > 1,
            "has_next": page < pages,
            "prev_num": page - 1 if page > 1 else None,
            "next_num": page + 1 if page < pages else None
        }
    }

def get_pagination_params(page: Optional[int] = None, per_page: Optional[int] = None) -> tuple:
    """
    Obtiene parámetros de paginación validados
    
    Returns:
        Tupla con (page, per_page) validados
    """
    page = max(1, page or 1)
    per_page = max(1, min(100, per_page or 50))  # Entre 1 y 100
    
    return page, per_page
