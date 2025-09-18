"""
Servicios de negocio para Immermex Dashboard
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from database import Facturacion, Cobranza, CFDIRelacionado, Inventario, KPI, ArchivoProcesado
from models import FiltrosDashboard, PedidoDetalleResponse, ClienteDetalleResponse

class DashboardService:
    """Servicio principal para operaciones del dashboard"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_kpis(self, filtros: FiltrosDashboard = None) -> Dict:
        """Obtiene KPIs principales del dashboard"""
        
        # Construir filtros base
        facturacion_query = self.db.query(Facturacion)
        cobranza_query = self.db.query(Cobranza)
        
        if filtros:
            facturacion_query = self._aplicar_filtros_facturacion(facturacion_query, filtros)
            cobranza_query = self._aplicar_filtros_cobranza(cobranza_query, filtros)
        
        # KPIs básicos
        facturacion_total = facturacion_query.with_entities(func.sum(Facturacion.total)).scalar() or 0
        cobranza_total = cobranza_query.with_entities(func.sum(Cobranza.importe_cobrado)).scalar() or 0
        
        # Anticipos
        anticipos_query = self.db.query(CFDIRelacionado).filter(
            CFDIRelacionado.tipo_cfdi.ilike('%anticipo%')
        )
        if filtros:
            anticipos_query = self._aplicar_filtros_cfdi(anticipos_query, filtros)
        anticipos_total = anticipos_query.with_entities(func.sum(CFDIRelacionado.importe_cfdi)).scalar() or 0
        
        # Porcentaje cobrado
        porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
        
        # Aging de cartera
        aging = self._calcular_aging_cartera(facturacion_query, cobranza_query)
        
        # Top clientes
        top_clientes = self._get_top_clientes(facturacion_query)
        
        # Consumo por material
        consumo_material = self._get_consumo_material(facturacion_query)
        
        # Rotación de inventario
        rotacion_inventario = self._calcular_rotacion_inventario(filtros)
        
        # Estadísticas adicionales
        total_facturas = facturacion_query.count()
        clientes_unicos = facturacion_query.with_entities(func.count(func.distinct(Facturacion.cliente))).scalar() or 0
        
        return {
            'facturacion_total': float(facturacion_total),
            'cobranza_total': float(cobranza_total),
            'anticipos_total': float(anticipos_total),
            'porcentaje_cobrado': round(porcentaje_cobrado, 2),
            'rotacion_inventario': rotacion_inventario,
            'total_facturas': total_facturas,
            'clientes_unicos': clientes_unicos,
            'aging_cartera': aging,
            'top_clientes': top_clientes,
            'consumo_material': consumo_material
        }
    
    def get_pedido_detalle(self, numero_pedido: str) -> PedidoDetalleResponse:
        """Obtiene detalles de un pedido específico"""
        
        # Obtener facturas del pedido
        facturas = self.db.query(Facturacion).filter(
            Facturacion.numero_pedido == numero_pedido
        ).all()
        
        if not facturas:
            raise ValueError(f"No se encontró el pedido {numero_pedido}")
        
        # Agrupar materiales
        materiales = []
        total_pedido = 0
        cliente = facturas[0].cliente
        agente = facturas[0].agente
        fecha_factura = facturas[0].fecha_factura
        
        for factura in facturas:
            materiales.append({
                'material': factura.material,
                'cantidad_kg': factura.cantidad_kg,
                'precio_unitario': factura.precio_unitario,
                'subtotal': factura.subtotal
            })
            total_pedido += factura.total or 0
        
        # Obtener cobros
        folios = [f.folio for f in facturas if f.folio]
        importe_cobrado = self.db.query(func.sum(Cobranza.importe_cobrado)).filter(
            Cobranza.folio.in_(folios)
        ).scalar() or 0
        
        # Obtener anticipos
        uuids = [f.uuid for f in facturas if f.uuid]
        anticipos = self.db.query(func.sum(CFDIRelacionado.importe_cfdi)).filter(
            and_(
                CFDIRelacionado.uuid.in_(uuids),
                CFDIRelacionado.tipo_cfdi.ilike('%anticipo%')
            )
        ).scalar() or 0
        
        # Calcular estado de cobro
        margen = total_pedido - anticipos
        estado_cobro = "Cobrado" if importe_cobrado >= total_pedido else "Pendiente"
        
        # Calcular días de vencimiento
        dias_vencimiento = None
        if fecha_factura:
            dias_vencimiento = (datetime.now() - fecha_factura).days
        
        return PedidoDetalleResponse(
            numero_pedido=numero_pedido,
            cliente=cliente,
            agente=agente,
            fecha_factura=fecha_factura,
            materiales=materiales,
            total_pedido=total_pedido,
            importe_cobrado=importe_cobrado,
            anticipos=anticipos,
            margen=margen,
            estado_cobro=estado_cobro,
            dias_vencimiento=dias_vencimiento
        )
    
    def get_cliente_detalle(self, cliente: str) -> ClienteDetalleResponse:
        """Obtiene detalles de un cliente específico"""
        
        # Facturación total
        facturacion_total = self.db.query(func.sum(Facturacion.total)).filter(
            Facturacion.cliente == cliente
        ).scalar() or 0
        
        # Cobros totales
        cobros_total = self.db.query(func.sum(Cobranza.importe_cobrado)).filter(
            Cobranza.cliente == cliente
        ).scalar() or 0
        
        # Anticipos
        anticipos_total = self.db.query(func.sum(CFDIRelacionado.importe_cfdi)).filter(
            and_(
                CFDIRelacionado.cliente == cliente,
                CFDIRelacionado.tipo_cfdi.ilike('%anticipo%')
            )
        ).scalar() or 0
        
        # Facturas pendientes
        facturas_pendientes = self.db.query(Facturacion).filter(
            and_(
                Facturacion.cliente == cliente,
                Facturacion.folio.notin_(
                    self.db.query(Cobranza.folio).filter(Cobranza.folio.isnot(None))
                )
            )
        ).count()
        
        # Ticket promedio
        total_facturas = self.db.query(Facturacion).filter(
            Facturacion.cliente == cliente
        ).count()
        ticket_promedio = facturacion_total / total_facturas if total_facturas > 0 else 0
        
        # Puntualidad de pago (simplificada)
        facturas_cobradas = self.db.query(Facturacion).join(Cobranza, Facturacion.folio == Cobranza.folio).filter(
            Facturacion.cliente == cliente
        ).count()
        puntualidad_pago = (facturas_cobradas / total_facturas * 100) if total_facturas > 0 else 0
        
        # Última factura y último cobro
        ultima_factura = self.db.query(func.max(Facturacion.fecha_factura)).filter(
            Facturacion.cliente == cliente
        ).scalar()
        
        ultimo_cobro = self.db.query(func.max(Cobranza.fecha_cobro)).filter(
            Cobranza.cliente == cliente
        ).scalar()
        
        return ClienteDetalleResponse(
            cliente=cliente,
            facturacion_total=facturacion_total,
            cobros_total=cobros_total,
            anticipos_total=anticipos_total,
            facturas_pendientes=facturas_pendientes,
            ticket_promedio=ticket_promedio,
            puntualidad_pago=puntualidad_pago,
            ultima_factura=ultima_factura,
            ultimo_cobro=ultimo_cobro
        )
    
    def get_grafico_aging(self, filtros: FiltrosDashboard = None) -> Dict:
        """Obtiene datos para gráfico de aging de cartera"""
        aging = self._calcular_aging_cartera_detallado(filtros)
        
        return {
            'labels': list(aging.keys()),
            'data': list(aging.values()),
            'titulo': 'Aging de Cartera'
        }
    
    def get_grafico_top_clientes(self, filtros: FiltrosDashboard = None, limite: int = 10) -> Dict:
        """Obtiene datos para gráfico de top clientes"""
        top_clientes = self._get_top_clientes_detallado(filtros, limite)
        
        return {
            'labels': list(top_clientes.keys()),
            'data': list(top_clientes.values()),
            'titulo': f'Top {limite} Clientes por Facturación'
        }
    
    def get_grafico_consumo_material(self, filtros: FiltrosDashboard = None, limite: int = 10) -> Dict:
        """Obtiene datos para gráfico de consumo por material"""
        consumo = self._get_consumo_material_detallado(filtros, limite)
        
        return {
            'labels': list(consumo.keys()),
            'data': list(consumo.values()),
            'titulo': f'Top {limite} Materiales por Consumo'
        }
    
    def _aplicar_filtros_facturacion(self, query, filtros: FiltrosDashboard):
        """Aplica filtros a la consulta de facturación"""
        if filtros.fecha_inicio:
            query = query.filter(Facturacion.fecha_factura >= filtros.fecha_inicio)
        if filtros.fecha_fin:
            query = query.filter(Facturacion.fecha_factura <= filtros.fecha_fin)
        if filtros.cliente:
            query = query.filter(Facturacion.cliente.ilike(f"%{filtros.cliente}%"))
        if filtros.agente:
            query = query.filter(Facturacion.agente.ilike(f"%{filtros.agente}%"))
        if filtros.numero_pedido:
            query = query.filter(Facturacion.numero_pedido.ilike(f"%{filtros.numero_pedido}%"))
        if filtros.material:
            query = query.filter(Facturacion.material.ilike(f"%{filtros.material}%"))
        if filtros.mes:
            query = query.filter(Facturacion.mes == filtros.mes)
        if filtros.año:
            query = query.filter(Facturacion.año == filtros.año)
        
        return query
    
    def _aplicar_filtros_cobranza(self, query, filtros: FiltrosDashboard):
        """Aplica filtros a la consulta de cobranza"""
        if filtros.fecha_inicio:
            query = query.filter(Cobranza.fecha_cobro >= filtros.fecha_inicio)
        if filtros.fecha_fin:
            query = query.filter(Cobranza.fecha_cobro <= filtros.fecha_fin)
        if filtros.cliente:
            query = query.filter(Cobranza.cliente.ilike(f"%{filtros.cliente}%"))
        
        return query
    
    def _aplicar_filtros_cfdi(self, query, filtros: FiltrosDashboard):
        """Aplica filtros a la consulta de CFDIs relacionados"""
        if filtros.fecha_inicio:
            query = query.filter(CFDIRelacionado.fecha_cfdi >= filtros.fecha_inicio)
        if filtros.fecha_fin:
            query = query.filter(CFDIRelacionado.fecha_cfdi <= filtros.fecha_fin)
        if filtros.cliente:
            query = query.filter(CFDIRelacionado.cliente.ilike(f"%{filtros.cliente}%"))
        
        return query
    
    def _calcular_aging_cartera(self, facturacion_query, cobranza_query) -> Dict[str, int]:
        """Calcula aging de cartera"""
        # Obtener facturas no cobradas
        facturas_no_cobradas = facturacion_query.filter(
            Facturacion.folio.notin_(
                self.db.query(Cobranza.folio).filter(Cobranza.folio.isnot(None))
            )
        ).all()
        
        aging = {'0-30 días': 0, '31-60 días': 0, '61-90 días': 0, '90+ días': 0}
        
        for factura in facturas_no_cobradas:
            if factura.fecha_factura:
                dias_vencido = (datetime.now() - factura.fecha_factura).days
                if dias_vencido <= 30:
                    aging['0-30 días'] += 1
                elif dias_vencido <= 60:
                    aging['31-60 días'] += 1
                elif dias_vencido <= 90:
                    aging['61-90 días'] += 1
                else:
                    aging['90+ días'] += 1
        
        return aging
    
    def _calcular_aging_cartera_detallado(self, filtros: FiltrosDashboard = None) -> Dict[str, int]:
        """Calcula aging de cartera con filtros"""
        facturacion_query = self.db.query(Facturacion)
        if filtros:
            facturacion_query = self._aplicar_filtros_facturacion(facturacion_query, filtros)
        
        return self._calcular_aging_cartera(facturacion_query, None)
    
    def _get_top_clientes(self, facturacion_query) -> Dict[str, float]:
        """Obtiene top clientes por facturación"""
        top_clientes = facturacion_query.with_entities(
            Facturacion.cliente,
            func.sum(Facturacion.total).label('total')
        ).group_by(Facturacion.cliente).order_by(
            func.sum(Facturacion.total).desc()
        ).limit(10).all()
        
        return {cliente: float(total) for cliente, total in top_clientes}
    
    def _get_top_clientes_detallado(self, filtros: FiltrosDashboard = None, limite: int = 10) -> Dict[str, float]:
        """Obtiene top clientes con filtros"""
        facturacion_query = self.db.query(Facturacion)
        if filtros:
            facturacion_query = self._aplicar_filtros_facturacion(facturacion_query, filtros)
        
        return self._get_top_clientes(facturacion_query)
    
    def _get_consumo_material(self, facturacion_query) -> Dict[str, float]:
        """Obtiene consumo por material"""
        consumo = facturacion_query.with_entities(
            Facturacion.material,
            func.sum(Facturacion.cantidad_kg).label('total_kg')
        ).group_by(Facturacion.material).order_by(
            func.sum(Facturacion.cantidad_kg).desc()
        ).limit(10).all()
        
        return {material: float(total_kg) for material, total_kg in consumo if material}
    
    def _get_consumo_material_detallado(self, filtros: FiltrosDashboard = None, limite: int = 10) -> Dict[str, float]:
        """Obtiene consumo por material con filtros"""
        facturacion_query = self.db.query(Facturacion)
        if filtros:
            facturacion_query = self._aplicar_filtros_facturacion(facturacion_query, filtros)
        
        return self._get_consumo_material(facturacion_query)
    
    def _calcular_rotacion_inventario(self, filtros: FiltrosDashboard = None) -> float:
        """Calcula rotación de inventario"""
        inventario_query = self.db.query(Inventario)
        
        if filtros and filtros.mes:
            inventario_query = inventario_query.filter(Inventario.mes == filtros.mes)
        if filtros and filtros.año:
            inventario_query = inventario_query.filter(Inventario.año == filtros.año)
        
        total_salidas = inventario_query.with_entities(func.sum(Inventario.salidas)).scalar() or 0
        total_inicial = inventario_query.with_entities(func.sum(Inventario.cantidad_inicial)).scalar() or 0
        
        return round(total_salidas / total_inicial, 2) if total_inicial > 0 else 0
