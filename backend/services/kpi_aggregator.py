"""
Agregador de KPIs que coordina todos los servicios especializados
"""

from sqlalchemy.orm import Session
from .facturacion_service import FacturacionService
from .cobranza_service import CobranzaService
from .pedidos_service import PedidosService
from database import CFDIRelacionado, Cobranza
from utils.logging_config import log_performance
import time
import logging

logger = logging.getLogger(__name__)

class KPIAggregator:
    """Agregador principal que coordina el cálculo de KPIs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.facturacion_service = FacturacionService(db)
        self.cobranza_service = CobranzaService(db)
        self.pedidos_service = PedidosService(db)
    
    def calculate_kpis(self, filtros: dict = None) -> dict:
        """
        Calcula KPIs principales coordinando todos los servicios
        """
        start_time = time.time()
        
        try:
            # Obtener datos base
            facturas = self.facturacion_service.get_facturas_by_filtros(filtros)
            cobranzas = self.db.query(Cobranza).all()
            anticipos = self.db.query(CFDIRelacionado).all()
            pedidos = self.pedidos_service.get_pedidos_by_filtros(filtros)
            
            logger.info(f"Datos obtenidos - Facturas: {len(facturas)}, Pedidos: {len(pedidos)}, Cobranzas: {len(cobranzas)}")
            
            # Si no hay facturas, retornar KPIs por defecto
            if not facturas:
                logger.warning("No se encontraron facturas, retornando KPIs por defecto")
                return self._get_default_kpis()
            
            # Calcular KPIs según el tipo de filtro
            if filtros and filtros.get('pedidos'):
                return self._calculate_kpis_filtered_by_pedidos(facturas, pedidos, cobranzas, anticipos, filtros)
            else:
                return self._calculate_kpis_general(facturas, pedidos, cobranzas, anticipos)
                
        except Exception as e:
            logger.error(f"Error calculando KPIs: {str(e)}")
            return self._get_default_kpis()
        finally:
            duration = time.time() - start_time
            log_performance("calculate_kpis", duration, f"filtros={filtros}")
    
    def _calculate_kpis_filtered_by_pedidos(self, facturas: list, pedidos: list, cobranzas: list, anticipos: list, filtros: dict) -> dict:
        """Calcula KPIs cuando se filtra por pedidos específicos"""
        
        # Obtener facturas relacionadas con pedidos
        facturas_pedidos = self.facturacion_service.get_facturas_related_to_pedidos(pedidos)
        
        # Calcular facturación desde pedidos
        facturacion_total = sum(p.importe_sin_iva * 1.16 for p in pedidos if p.importe_sin_iva)
        facturacion_sin_iva = sum(p.importe_sin_iva for p in pedidos if p.importe_sin_iva)
        
        # Contar facturas únicas
        folios_unicos = len(set(p.folio_factura for p in pedidos if p.folio_factura))
        total_facturas = folios_unicos
        
        # Calcular cobranza proporcional
        cobranza_total = self.cobranza_service.calculate_cobranza_proporcional(
            facturas_pedidos, pedidos, cobranzas
        )
        
        # Calcular anticipos relacionados
        uuids_facturas = {f.uuid_factura for f in facturas_pedidos if f.uuid_factura and f.uuid_factura.strip()}
        anticipos_relacionados = [
            a for a in anticipos 
            if a.uuid_factura_relacionada in uuids_facturas 
            and a.uuid_factura_relacionada and a.uuid_factura_relacionada.strip()
        ]
        anticipos_total = sum(a.importe_relacion for a in anticipos_relacionados)
        
        # Calcular porcentajes
        porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
        porcentaje_anticipos = (anticipos_total / facturacion_sin_iva * 100) if facturacion_sin_iva > 0 else 0
        
        # Calcular métricas adicionales
        clientes_unicos = len(set(f.cliente for f in facturas_pedidos if f.cliente))
        pedidos_unicos = len(set(p.pedido for p in pedidos if p.pedido))
        toneladas_total = sum(p.kg for p in pedidos)
        
        # Calcular cobranza sin IVA
        cobranza_sin_iva = cobranza_total / 1.16 if cobranza_total > 0 else 0
        
        # Calcular gráficos
        aging_cartera = self.facturacion_service.calculate_aging_cartera(facturas_pedidos)
        top_clientes = self.facturacion_service.calculate_top_clientes(facturas_pedidos)
        consumo_material = self.pedidos_service.calculate_consumo_material(pedidos)
        
        return {
            "facturacion_total": round(facturacion_total, 2),
            "facturacion_sin_iva": round(facturacion_sin_iva, 2),
            "cobranza_total": round(cobranza_total, 2),
            "cobranza_general_total": round(cobranza_total, 2),  # Mismo valor para filtros por pedidos
            "cobranza_sin_iva": round(cobranza_sin_iva, 2),
            "anticipos_total": round(anticipos_total, 2),
            "porcentaje_anticipos": round(porcentaje_anticipos, 2),
            "porcentaje_cobrado": round(porcentaje_cobrado, 2),
            "porcentaje_cobrado_general": round(porcentaje_cobrado, 2),
            "total_facturas": total_facturas,
            "clientes_unicos": clientes_unicos,
            "pedidos_unicos": pedidos_unicos,
            "toneladas_total": round(toneladas_total / 1000, 2),
            "aging_cartera": aging_cartera,
            "top_clientes": top_clientes,
            "consumo_material": consumo_material,
            "expectativa_cobranza": {},  # Se calculará por separado si es necesario
            "rotacion_inventario": 0,
            "dias_cxc_ajustado": 0,
            "ciclo_efectivo": 0
        }
    
    def _calculate_kpis_general(self, facturas: list, pedidos: list, cobranzas: list, anticipos: list) -> dict:
        """Calcula KPIs generales (sin filtros por pedidos)"""
        
        # Filtrar facturas válidas
        facturas_validas = self.facturacion_service.get_facturas_validas(facturas)
        
        # Calcular facturación
        facturacion_total = sum(f.monto_total for f in facturas_validas)
        facturacion_sin_iva = sum(f.monto_neto for f in facturas_validas)
        
        # Calcular cobranza
        cobranzas_validas = self.cobranza_service.get_cobranzas_validas(cobranzas)
        cobranzas_relacionadas = self.cobranza_service.get_cobranzas_relacionadas(facturas_validas, cobranzas_validas)
        
        cobranza_total = sum(c.importe_pagado for c in cobranzas_relacionadas)
        cobranza_general_total = sum(c.importe_pagado for c in cobranzas_validas)
        
        # Calcular anticipos
        anticipos_total = sum(a.importe_relacion for a in anticipos)
        
        # Calcular porcentajes
        porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
        porcentaje_cobrado_general = (cobranza_general_total / facturacion_total * 100) if facturacion_total > 0 else 0
        porcentaje_anticipos = (anticipos_total / facturacion_sin_iva * 100) if facturacion_sin_iva > 0 else 0
        
        # Calcular métricas adicionales
        total_facturas = len(facturas_validas)
        clientes_unicos = len(set(f.cliente for f in facturas_validas if f.cliente))
        pedidos_unicos = len(set(p.pedido for p in pedidos if p.pedido))
        toneladas_total = sum(p.kg for p in pedidos)
        
        # Calcular cobranza sin IVA
        cobranza_sin_iva = sum(c.importe_pagado / 1.16 for c in cobranzas_relacionadas if c.importe_pagado > 0)
        
        # Calcular gráficos
        aging_cartera = self.facturacion_service.calculate_aging_cartera(facturas_validas)
        top_clientes = self.facturacion_service.calculate_top_clientes(facturas_validas)
        consumo_material = self.pedidos_service.calculate_consumo_material(pedidos)
        
        return {
            "facturacion_total": round(facturacion_total, 2),
            "facturacion_sin_iva": round(facturacion_sin_iva, 2),
            "cobranza_total": round(cobranza_total, 2),
            "cobranza_general_total": round(cobranza_general_total, 2),
            "cobranza_sin_iva": round(cobranza_sin_iva, 2),
            "anticipos_total": round(anticipos_total, 2),
            "porcentaje_anticipos": round(porcentaje_anticipos, 2),
            "porcentaje_cobrado": round(porcentaje_cobrado, 2),
            "porcentaje_cobrado_general": round(porcentaje_cobrado_general, 2),
            "total_facturas": total_facturas,
            "clientes_unicos": clientes_unicos,
            "pedidos_unicos": pedidos_unicos,
            "toneladas_total": round(toneladas_total / 1000, 2),
            "aging_cartera": aging_cartera,
            "top_clientes": top_clientes,
            "consumo_material": consumo_material,
            "expectativa_cobranza": {},
            "rotacion_inventario": 0,
            "dias_cxc_ajustado": 0,
            "ciclo_efectivo": 0
        }
    
    def _get_default_kpis(self) -> dict:
        """Retorna KPIs por defecto cuando no hay datos"""
        return {
            "facturacion_total": 0.0,
            "facturacion_sin_iva": 0.0,
            "cobranza_total": 0.0,
            "cobranza_general_total": 0.0,
            "cobranza_sin_iva": 0.0,
            "anticipos_total": 0.0,
            "porcentaje_anticipos": 0.0,
            "porcentaje_cobrado": 0.0,
            "porcentaje_cobrado_general": 0.0,
            "total_facturas": 0,
            "clientes_unicos": 0,
            "pedidos_unicos": 0,
            "toneladas_total": 0.0,
            "aging_cartera": {},
            "top_clientes": {},
            "consumo_material": {},
            "expectativa_cobranza": {},
            "rotacion_inventario": 0.0,
            "dias_cxc_ajustado": 0.0,
            "ciclo_efectivo": 0.0
        }
