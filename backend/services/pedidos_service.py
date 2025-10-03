"""
Servicio especializado para operaciones de pedidos
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from database import Pedido, Facturacion
from utils.validators import DataValidator
import logging

logger = logging.getLogger(__name__)

class PedidosService:
    """Servicio para operaciones relacionadas con pedidos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_pedidos(self, pedidos_data: list, archivo_id: int) -> int:
        """Guarda datos de pedidos con asignación automática de fechas y días de crédito"""
        count = 0
        
        # Obtener facturas para asignar fechas y días de crédito automáticamente
        facturas = self.db.query(Facturacion).all()
        fechas_por_folio = {}
        dias_credito_por_folio = {}
        
        for factura in facturas:
            if factura.folio_factura:
                folio_limpio = str(factura.folio_factura).strip()
                
                if factura.fecha_factura:
                    fechas_por_folio[folio_limpio] = factura.fecha_factura
                
                if factura.dias_credito is not None:
                    dias_credito_por_folio[folio_limpio] = factura.dias_credito
        
        fechas_asignadas = 0
        dias_credito_asignados = 0
        
        for pedido_data in pedidos_data:
            try:
                # Convertir fechas de forma segura
                fecha_factura = DataValidator.safe_date(pedido_data.get('fecha_factura'))
                fecha_pago = DataValidator.safe_date(pedido_data.get('fecha_pago'))
                
                # Asignar fecha_factura automáticamente si no existe
                if not fecha_factura:
                    folio_factura = pedido_data.get('folio_factura', '')
                    if folio_factura:
                        folio_limpio = str(folio_factura).strip()
                        if folio_limpio in fechas_por_folio:
                            fecha_factura = fechas_por_folio[folio_limpio]
                            fechas_asignadas += 1
                
                # Asignar días de crédito automáticamente
                dias_credito_pedido = DataValidator.safe_int(pedido_data.get('dias_credito', 30))
                folio_factura = pedido_data.get('folio_factura', '')
                
                if folio_factura:
                    folio_limpio = str(folio_factura).strip()
                    if folio_limpio in dias_credito_por_folio:
                        dias_credito_pedido = dias_credito_por_folio[folio_limpio]
                        dias_credito_asignados += 1
                
                pedido = Pedido(
                    folio_factura=DataValidator.safe_string(pedido_data.get('folio_factura', '')),
                    pedido=DataValidator.safe_string(pedido_data.get('pedido', '')),
                    kg=DataValidator.safe_float(pedido_data.get('kg', 0)),
                    precio_unitario=DataValidator.safe_float(pedido_data.get('precio_unitario', 0)),
                    importe_sin_iva=DataValidator.safe_float(pedido_data.get('importe_sin_iva', 0)),
                    material=DataValidator.safe_string(pedido_data.get('material', '')),
                    dias_credito=dias_credito_pedido,
                    fecha_factura=fecha_factura,
                    fecha_pago=fecha_pago,
                    archivo_id=archivo_id
                )
                self.db.add(pedido)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando pedido: {str(e)}")
                continue
        
        # No hacer commit aquí - dejar que el método principal maneje la transacción
        
        if fechas_asignadas > 0:
            logger.info(f"Se asignaron automáticamente {fechas_asignadas} fechas de factura a pedidos")
        if dias_credito_asignados > 0:
            logger.info(f"Se asignaron automáticamente {dias_credito_asignados} días de crédito a pedidos")
        
        return count
    
    def get_pedidos_by_filtros(self, filtros: dict = None):
        """Obtiene pedidos aplicando filtros"""
        query = self.db.query(Pedido)
        
        if filtros:
            # Solo aplicar filtro de mes si también hay año seleccionado
            if filtros.get('mes') and filtros.get('año'):
                query = query.filter(func.extract('month', Pedido.fecha_factura) == filtros['mes'])
            elif filtros.get('mes') and not filtros.get('año'):
                # Si hay mes pero no año, ignorar el filtro de mes
                logger.warning("Filtro de mes ignorado porque no hay año seleccionado")
            
            if filtros.get('año'):
                query = query.filter(func.extract('year', Pedido.fecha_factura) == filtros['año'])
            if filtros.get('pedidos'):
                pedidos_list = filtros['pedidos']
                query = query.filter(Pedido.pedido.in_(pedidos_list))
        
        return query.all()
    
    def calculate_consumo_material(self, pedidos: list) -> dict:
        """Calcula consumo por material"""
        materiales_consumo = {}
        pedidos_omitidos = 0
        
        for pedido in pedidos:
            if not pedido.material or pedido.material.strip() == "":
                pedidos_omitidos += 1
                continue
            
            material = pedido.material.strip()
            # Truncar código de material a primeros 7 dígitos para agrupación útil
            if len(material) > 7:
                material = material[:7]
            
            if material not in materiales_consumo:
                materiales_consumo[material] = 0
            materiales_consumo[material] += pedido.kg
        
        # Ordenar y tomar top 10
        sorted_materiales = sorted(materiales_consumo.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_materiales[:10])
    
    def get_folios_pedidos(self, pedidos: list) -> list:
        """Obtiene folios únicos de pedidos"""
        return list(set(p.folio_factura for p in pedidos if p.folio_factura))
