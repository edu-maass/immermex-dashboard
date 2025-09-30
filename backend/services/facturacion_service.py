"""
Servicio especializado para operaciones de facturación
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from database import Facturacion
from utils.validators import DataValidator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FacturacionService:
    """Servicio para operaciones relacionadas con facturación"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_facturas(self, facturas_data: list, archivo_id: int) -> int:
        """Guarda datos de facturación"""
        count = 0
        
        for factura_data in facturas_data:
            try:
                fecha_factura = DataValidator.safe_date(factura_data.get('fecha_factura'))
                
                factura = Facturacion(
                    serie_factura=DataValidator.safe_string(factura_data.get('serie_factura', '')),
                    folio_factura=DataValidator.safe_string(factura_data.get('folio_factura', '')),
                    fecha_factura=fecha_factura,
                    cliente=DataValidator.safe_string(factura_data.get('cliente', '')),
                    agente=DataValidator.safe_string(factura_data.get('agente', '')),
                    monto_neto=DataValidator.safe_float(factura_data.get('monto_neto', 0)),
                    monto_total=DataValidator.safe_float(factura_data.get('monto_total', 0)),
                    saldo_pendiente=DataValidator.safe_float(factura_data.get('saldo_pendiente', 0)),
                    dias_credito=DataValidator.safe_int(factura_data.get('dias_credito', 30)),
                    uuid_factura=DataValidator.safe_string(factura_data.get('uuid_factura', '')),
                    archivo_id=archivo_id,
                    mes=fecha_factura.month if fecha_factura else None,
                    año=fecha_factura.year if fecha_factura else None
                )
                self.db.add(factura)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando factura: {str(e)}")
                continue
        
        self.db.commit()
        return count
    
    def get_facturas_by_filtros(self, filtros: dict = None):
        """Obtiene facturas aplicando filtros"""
        query = self.db.query(Facturacion)
        
        if filtros:
            if filtros.get('mes'):
                query = query.filter(Facturacion.mes == filtros['mes'])
            if filtros.get('año'):
                query = query.filter(Facturacion.año == filtros['año'])
            if filtros.get('pedidos'):
                folios_pedidos = filtros.get('folios_pedidos', [])
                if folios_pedidos:
                    query = query.filter(Facturacion.folio_factura.in_(folios_pedidos))
        
        return query.all()
    
    def get_facturas_validas(self, facturas: list) -> list:
        """Filtra facturas válidas (excluye totales)"""
        return [
            f for f in facturas 
            if DataValidator.validate_folio(f.folio_factura)
        ]
    
    def get_facturas_related_to_pedidos(self, pedidos_filtrados: list) -> list:
        """Obtiene facturas relacionadas con pedidos filtrados"""
        facturas_relacionadas = []
        
        for pedido in pedidos_filtrados:
            if pedido.folio_factura:
                facturas_folio = self.db.query(Facturacion).filter(
                    Facturacion.folio_factura == pedido.folio_factura
                ).all()
                facturas_relacionadas.extend(facturas_folio)
        
        # Eliminar duplicados por UUID
        facturas_unicas = {}
        for factura in facturas_relacionadas:
            if factura.uuid_factura:
                facturas_unicas[factura.uuid_factura] = factura
        
        return list(facturas_unicas.values())
    
    def calculate_aging_cartera(self, facturas: list) -> dict:
        """Calcula aging de cartera por monto pendiente"""
        aging = {"0-30 dias": 0, "31-60 dias": 0, "61-90 dias": 0, "90+ dias": 0}
        
        for factura in facturas:
            if factura.fecha_factura:
                dias_credito = factura.dias_credito or 30
                fecha_vencimiento = factura.fecha_factura + timedelta(days=dias_credito)
                dias_vencidos = (datetime.now() - fecha_vencimiento).days
                
                monto_pendiente = factura.monto_total - (getattr(factura, 'importe_cobrado', 0) or 0)
                
                if monto_pendiente > 0:
                    if dias_vencidos <= 30:
                        aging["0-30 dias"] += monto_pendiente
                    elif dias_vencidos <= 60:
                        aging["31-60 dias"] += monto_pendiente
                    elif dias_vencidos <= 90:
                        aging["61-90 dias"] += monto_pendiente
                    else:
                        aging["90+ dias"] += monto_pendiente
        
        return aging
    
    def calculate_top_clientes(self, facturas: list) -> dict:
        """Calcula top clientes por facturación"""
        clientes_facturacion = {}
        
        for factura in facturas:
            cliente = factura.cliente or "Sin cliente"
            if cliente not in clientes_facturacion:
                clientes_facturacion[cliente] = 0
            clientes_facturacion[cliente] += factura.monto_total
        
        # Ordenar y tomar top 10
        sorted_clientes = sorted(clientes_facturacion.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_clientes[:10])
