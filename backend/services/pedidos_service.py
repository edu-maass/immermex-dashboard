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

    def get_top_proveedores(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene top proveedores por monto de compras"""
        from database import Compras
        from sqlalchemy import func

        query = self.db.query(
            Compras.proveedor,
            func.sum(Compras.subtotal).label('total_compras')
        ).filter(
            Compras.proveedor.isnot(None),
            Compras.proveedor != ''
        ).group_by(Compras.proveedor)

        # Aplicar filtros
        if filtros:
            if filtros.get('mes'):
                query = query.filter(func.extract('month', Compras.fecha_compra) == filtros['mes'])
            if filtros.get('año'):
                query = query.filter(func.extract('year', Compras.fecha_compra) == filtros['año'])

        # Ordenar por total y limitar
        result = query.order_by(func.sum(Compras.subtotal).desc()).limit(limite).all()

        return {proveedor: float(total) for proveedor, total in result}

    def get_compras_por_material(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene compras agrupadas por material"""
        from database import Compras
        from sqlalchemy import func

        query = self.db.query(
            Compras.concepto,
            func.sum(Compras.subtotal).label('total_compras')
        ).filter(
            Compras.concepto.isnot(None),
            Compras.concepto != ''
        ).group_by(Compras.concepto)

        # Aplicar filtros
        if filtros:
            if filtros.get('mes'):
                query = query.filter(func.extract('month', Compras.fecha_compra) == filtros['mes'])
            if filtros.get('año'):
                query = query.filter(func.extract('year', Compras.fecha_compra) == filtros['año'])

        # Ordenar por total y limitar
        result = query.order_by(func.sum(Compras.subtotal).desc()).limit(limite).all()

        return {concepto: float(total) for concepto, total in result}

    def get_evolucion_precios(self, filtros: dict = None) -> list:
        """Obtiene evolución de precios por período"""
        from database import Compras
        from sqlalchemy import func, extract

        # Agrupar por mes y año
        query = self.db.query(
            func.extract('year', Compras.fecha_compra).label('año'),
            func.extract('month', Compras.fecha_compra).label('mes'),
            func.avg(Compras.precio_unitario).label('precio_promedio'),
            func.min(Compras.precio_unitario).label('precio_min'),
            func.max(Compras.precio_unitario).label('precio_max')
        ).filter(
            Compras.precio_unitario > 0
        ).group_by(
            func.extract('year', Compras.fecha_compra),
            func.extract('month', Compras.fecha_compra)
        )

        # Aplicar filtros
        if filtros:
            if filtros.get('mes'):
                query = query.having(func.extract('month', Compras.fecha_compra) == filtros['mes'])
            if filtros.get('año'):
                query = query.having(func.extract('year', Compras.fecha_compra) == filtros['año'])

        # Ordenar por fecha
        result = query.order_by(
            func.extract('year', Compras.fecha_compra),
            func.extract('month', Compras.fecha_compra)
        ).all()

        # Formatear resultado
        evolucion = []
        for row in result:
            fecha = f"{int(row.año)}-{int(row.mes):02d}"
            evolucion.append({
                'fecha': fecha,
                'precio_promedio': float(row.precio_promedio or 0),
                'precio_min': float(row.precio_min or 0),
                'precio_max': float(row.precio_max or 0)
            })

        return evolucion

    def get_flujo_pagos_semanal(self, filtros: dict = None) -> list:
        """Obtiene flujo de pagos semanal"""
        from database import Compras
        from sqlalchemy import func, extract

        # Agrupar por semana
        query = self.db.query(
            func.extract('year', Compras.fecha_compra).label('año'),
            func.extract('week', Compras.fecha_compra).label('semana'),
            func.sum(Compras.subtotal).label('total_compras'),
            func.sum(
                func.case(
                    [(Compras.estado_pago == 'pagado', Compras.subtotal)],
                    else_=0
                )
            ).label('pagos_realizados'),
            func.sum(
                func.case(
                    [(Compras.estado_pago != 'pagado', Compras.subtotal)],
                    else_=0
                )
            ).label('pendiente')
        ).group_by(
            func.extract('year', Compras.fecha_compra),
            func.extract('week', Compras.fecha_compra)
        )

        # Aplicar filtros
        if filtros:
            if filtros.get('mes'):
                query = query.having(func.extract('month', Compras.fecha_compra) == filtros['mes'])
            if filtros.get('año'):
                query = query.having(func.extract('year', Compras.fecha_compra) == filtros['año'])

        # Ordenar por fecha
        result = query.order_by(
            func.extract('year', Compras.fecha_compra),
            func.extract('week', Compras.fecha_compra)
        ).all()

        # Formatear resultado
        flujo = []
        for row in result:
            semana = f"Semana {int(row.semana)}"
            flujo.append({
                'semana': semana,
                'pagos': float(row.pagos_realizados or 0),
                'pendiente': float(row.pendiente or 0)
            })

        return flujo

    def get_datos_filtrados(self, filtros: dict = None) -> list:
        """Obtiene datos filtrados para tabla"""
        from database import Compras

        query = self.db.query(Compras).filter(
            Compras.fecha_compra.isnot(None)
        )

        # Aplicar filtros
        if filtros:
            if filtros.get('mes'):
                query = query.filter(func.extract('month', Compras.fecha_compra) == filtros['mes'])
            if filtros.get('año'):
                query = query.filter(func.extract('year', Compras.fecha_compra) == filtros['año'])

        # Ordenar por fecha descendente
        result = query.order_by(Compras.fecha_compra.desc()).all()

        # Formatear resultado
        datos = []
        for compra in result:
            datos.append({
                'id': str(compra.id),
                'fecha_compra': compra.fecha_compra.isoformat() if compra.fecha_compra else '',
                'proveedor': compra.proveedor or '',
                'concepto': compra.concepto or '',  # Este será el material
                'cantidad_kg': float(compra.cantidad or 0),
                'precio_unitario': float(compra.precio_unitario or 0),
                'subtotal': float(compra.subtotal or 0),
                'anticipo': 0.0  # Por ahora, asumimos 0 ya que no hay campo específico para anticipo en Compras
            })

        return datos