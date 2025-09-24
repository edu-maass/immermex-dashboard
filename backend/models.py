"""
Modelos Pydantic para la API de Immermex Dashboard
"""

from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

# Modelos de respuesta para KPIs
class KPIsResponse(BaseModel):
    facturacion_total: float
    cobranza_total: float
    cobranza_general_total: float  # Todas las cobranzas sin filtro
    anticipos_total: float
    porcentaje_anticipos: float  # Porcentaje de anticipos sobre facturación
    porcentaje_cobrado: float
    porcentaje_cobrado_general: float  # Porcentaje sobre cobranza general
    rotacion_inventario: float
    total_facturas: int
    clientes_unicos: int
    aging_cartera: Dict[str, int]
    top_clientes: Dict[str, float]
    consumo_material: Dict[str, float]

class FacturacionResponse(BaseModel):
    id: int
    folio: Optional[str]
    fecha_factura: Optional[datetime]
    cliente: Optional[str]
    agente: Optional[str]
    importe_factura: Optional[float]
    uuid: Optional[str]
    numero_pedido: Optional[str]
    material: Optional[str]
    cantidad_kg: Optional[float]
    precio_unitario: Optional[float]
    subtotal: Optional[float]
    iva: Optional[float]
    total: Optional[float]
    mes: Optional[int]
    año: Optional[int]

class CobranzaResponse(BaseModel):
    id: int
    folio: Optional[str]
    fecha_cobro: Optional[datetime]
    cliente: Optional[str]
    importe_cobrado: Optional[float]
    forma_pago: Optional[str]
    referencia_pago: Optional[str]
    uuid: Optional[str]

class CFDIRelacionadoResponse(BaseModel):
    id: int
    uuid: Optional[str]
    tipo_cfdi: Optional[str]
    fecha_cfdi: Optional[datetime]
    cliente: Optional[str]
    importe_cfdi: Optional[float]
    folio_relacionado: Optional[str]
    concepto: Optional[str]

class InventarioResponse(BaseModel):
    id: int
    material: Optional[str]
    cantidad_inicial: Optional[float]
    entradas: Optional[float]
    salidas: Optional[float]
    cantidad_final: Optional[float]
    costo_unitario: Optional[float]
    valor_inventario: Optional[float]
    mes: Optional[int]
    año: Optional[int]

class ArchivoProcesadoResponse(BaseModel):
    id: int
    nombre_archivo: str
    fecha_procesamiento: datetime
    registros_procesados: int
    estado: str
    error_message: Optional[str]
    mes: Optional[int]
    año: Optional[int]

# Modelos para filtros
class FiltrosDashboard(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    cliente: Optional[str] = None
    agente: Optional[str] = None
    numero_pedido: Optional[str] = None
    material: Optional[str] = None
    mes: Optional[int] = None
    año: Optional[int] = None

class PedidoDetalleResponse(BaseModel):
    numero_pedido: str
    cliente: str
    agente: str
    fecha_factura: datetime
    materiales: List[Dict[str, Any]]
    total_pedido: float
    importe_cobrado: float
    anticipos: float
    margen: float
    estado_cobro: str
    dias_vencimiento: Optional[int]

class ClienteDetalleResponse(BaseModel):
    cliente: str
    facturacion_total: float
    cobros_total: float
    anticipos_total: float
    facturas_pendientes: int
    ticket_promedio: float
    puntualidad_pago: float  # Porcentaje de facturas cobradas a tiempo
    ultima_factura: Optional[datetime]
    ultimo_cobro: Optional[datetime]

# Modelos para respuestas de gráficos
class GraficoBarrasResponse(BaseModel):
    labels: List[str]
    data: List[float]
    titulo: str

class GraficoPieResponse(BaseModel):
    labels: List[str]
    data: List[float]
    titulo: str

class GraficoLineaResponse(BaseModel):
    labels: List[str]
    series: List[Dict[str, any]]
    titulo: str

# Modelo para subida de archivos
class ArchivoUploadResponse(BaseModel):
    mensaje: str
    archivo_id: int
    registros_procesados: int
    estado: str
