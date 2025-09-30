"""
Servicio especializado para operaciones de cobranza
"""

from sqlalchemy.orm import Session
from database import Cobranza
from utils.validators import DataValidator
import logging

logger = logging.getLogger(__name__)

class CobranzaService:
    """Servicio para operaciones relacionadas con cobranza"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_cobranzas(self, cobranzas_data: list, archivo_id: int) -> int:
        """Guarda datos de cobranza"""
        count = 0
        
        for cobranza_data in cobranzas_data:
            try:
                fecha_pago = DataValidator.safe_date(cobranza_data.get('fecha_pago'))
                
                cobranza = Cobranza(
                    fecha_pago=fecha_pago,
                    serie_pago=DataValidator.safe_string(cobranza_data.get('serie_pago', '')),
                    folio_pago=DataValidator.safe_string(cobranza_data.get('folio_pago', '')),
                    cliente=DataValidator.safe_string(cobranza_data.get('cliente', '')),
                    moneda=DataValidator.safe_string(cobranza_data.get('moneda', 'MXN')),
                    tipo_cambio=DataValidator.safe_float(cobranza_data.get('tipo_cambio', 1.0)),
                    forma_pago=DataValidator.safe_string(cobranza_data.get('forma_pago', '')),
                    parcialidad=DataValidator.safe_int(cobranza_data.get('numero_parcialidades', cobranza_data.get('parcialidad', 1))),
                    importe_pagado=DataValidator.safe_float(cobranza_data.get('importe_pagado', 0)),
                    uuid_factura_relacionada=DataValidator.safe_string(cobranza_data.get('uuid_relacionado', cobranza_data.get('uuid_factura_relacionada', ''))),
                    archivo_id=archivo_id
                )
                self.db.add(cobranza)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando cobranza: {str(e)}")
                continue
        
        self.db.commit()
        return count
    
    def get_cobranzas_validas(self, cobranzas: list) -> list:
        """Filtra cobranzas válidas (excluye totales)"""
        return [
            c for c in cobranzas 
            if DataValidator.validate_folio(c.folio_pago)
        ]
    
    def get_cobranzas_relacionadas(self, facturas: list, cobranzas: list) -> list:
        """Obtiene cobranzas relacionadas con facturas"""
        facturas_uuids = {f.uuid_factura for f in facturas if f.uuid_factura}
        cobranzas_validas = self.get_cobranzas_validas(cobranzas)
        
        return [
            c for c in cobranzas_validas 
            if c.uuid_factura_relacionada in facturas_uuids
        ]
    
    def calculate_cobranza_proporcional(self, facturas: list, pedidos: list, cobranzas: list) -> float:
        """Calcula cobranza proporcional para pedidos filtrados"""
        cobranza_total = 0
        
        # Obtener UUIDs de facturas
        uuids_facturas = {f.uuid_factura for f in facturas if f.uuid_factura and f.uuid_factura.strip()}
        
        # Filtrar cobranzas relacionadas
        cobranzas_relacionadas = [
            c for c in cobranzas 
            if c.uuid_factura_relacionada in uuids_facturas
            and DataValidator.validate_folio(c.folio_pago)
        ]
        
        # Agrupar cobranzas por factura
        cobranza_por_factura = {}
        for cobranza in cobranzas_relacionadas:
            uuid_factura = cobranza.uuid_factura_relacionada
            if uuid_factura not in cobranza_por_factura:
                cobranza_por_factura[uuid_factura] = 0
            cobranza_por_factura[uuid_factura] += cobranza.importe_pagado
        
        # Calcular cobranza proporcional para cada factura
        for factura in facturas:
            if not factura.uuid_factura:
                continue
            
            uuid_factura = factura.uuid_factura
            cobranza_factura = cobranza_por_factura.get(uuid_factura, 0)
            
            if cobranza_factura > 0 and factura.monto_total > 0:
                # Buscar todos los pedidos de esta factura
                pedidos_factura = [p for p in pedidos if p.folio_factura == factura.folio_factura]
                
                if pedidos_factura:
                    # Calcular monto total de todos los pedidos de esta factura
                    monto_total_pedidos_factura = sum(p.importe_sin_iva for p in pedidos_factura if p.importe_sin_iva)
                    
                    # Calcular monto de los pedidos filtrados de esta factura
                    pedidos_filtrados_factura = [p for p in pedidos if p.folio_factura == factura.folio_factura]
                    monto_pedidos_filtrados_factura = sum(p.importe_sin_iva for p in pedidos_filtrados_factura if p.importe_sin_iva)
                    
                    if monto_total_pedidos_factura > 0:
                        # Calcular cobranza proporcional basada en monto
                        porcentaje_monto_pedidos_filtrados = monto_pedidos_filtrados_factura / monto_total_pedidos_factura
                        cobranza_proporcional = cobranza_factura * porcentaje_monto_pedidos_filtrados
                        cobranza_total += cobranza_proporcional
        
        return cobranza_total
