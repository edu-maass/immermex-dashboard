"""
Agregador de KPIs que coordina todos los servicios especializados
"""

from sqlalchemy.orm import Session
from .facturacion_service import FacturacionService
from .cobranza_service import CobranzaService
from .pedidos_service import PedidosService
from database import CFDIRelacionado, Cobranza
from utils.logging_config import log_performance
from utils.cache import cache_kpis, invalidate_data_cache
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
    
    @cache_kpis(ttl=300)  # Cache por 5 minutos
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
                kpis_result = self._calculate_kpis_filtered_by_pedidos(facturas, pedidos, cobranzas, anticipos, filtros)
                # Para filtros de pedidos, aplicar filtro proporcional a la expectativa de cobranza
                aplicar_filtro_proporcional = True
            else:
                kpis_result = self._calculate_kpis_general(facturas, pedidos, cobranzas, anticipos)
                # Sin filtros, mostrar todos los datos
                aplicar_filtro_proporcional = False
            
            # Calcular expectativa de cobranza
            kpis_result['expectativa_cobranza'] = self._calculate_expectativa_cobranza(
                facturas, pedidos, anticipos, cobranzas, aplicar_filtro_proporcional
            )
            
            return kpis_result
                
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
    
    def _calculate_expectativa_cobranza(self, facturas: list, pedidos: list, anticipos: list = None, cobranzas: list = None, aplicar_filtro_proporcional: bool = False) -> dict:
        """Calcula expectativa de cobranza futura basada en pedidos y sus días de crédito"""
        from datetime import datetime, timedelta
        
        expectativa = {}
        
        logger.info(f"Calculando expectativa de cobranza con {len(pedidos)} pedidos, {len(facturas)} facturas, {len(cobranzas or [])} cobranzas, aplicar_filtro_proporcional={aplicar_filtro_proporcional}")
        
        # Obtener fecha actual
        hoy = datetime.now()
        
        # Crear diccionarios para búsqueda rápida
        anticipos_por_factura = {}
        if anticipos:
            for anticipo in anticipos:
                if hasattr(anticipo, 'uuid_factura_relacionada') and anticipo.uuid_factura_relacionada:
                    anticipos_por_factura[anticipo.uuid_factura_relacionada] = anticipos_por_factura.get(anticipo.uuid_factura_relacionada, 0) + anticipo.importe_relacion
        
        cobranzas_por_factura = {}
        if cobranzas:
            for cobranza in cobranzas:
                if cobranza.uuid_factura_relacionada:
                    cobranzas_por_factura[cobranza.uuid_factura_relacionada] = cobranzas_por_factura.get(cobranza.uuid_factura_relacionada, 0) + cobranza.importe_pagado
        
        # Calcular fecha de referencia basada en los pedidos
        fechas_pedidos = [p.fecha_factura for p in pedidos if p.fecha_factura]
        if fechas_pedidos:
            fecha_referencia = min(fechas_pedidos)
            # Ajustar al lunes de esa semana
            dias_hasta_lunes = fecha_referencia.weekday()
            fecha_referencia = fecha_referencia - timedelta(days=dias_hasta_lunes)
        else:
            fecha_referencia = hoy
        
        logger.info(f"Fecha de referencia para semanas: {fecha_referencia.strftime('%Y-%m-%d')}")
        
        # Agrupar por semana (4 semanas pasadas + 18 semanas futuras para cubrir créditos de 120 días)
        for i in range(-4, 18):
            semana_inicio = fecha_referencia + timedelta(weeks=i)
            semana_fin = semana_inicio + timedelta(days=6)
            semana_key = f"Semana {i+5} ({semana_inicio.strftime('%d/%m')} - {semana_fin.strftime('%d/%m')})"
            
            cobranza_esperada = 0
            cobranza_real = 0
            pedidos_pendientes = 0
            
            # Calcular cobranza esperada basada en pedidos que vencen en esa semana
            for pedido in pedidos:
                if not pedido.fecha_factura:
                    continue
                
                try:
                    # Calcular fecha de vencimiento usando fecha_factura + dias_credito del pedido
                    dias_credito = pedido.dias_credito or 0
                    fecha_vencimiento = pedido.fecha_factura + timedelta(days=dias_credito)
                    
                    # Si el pedido vence en esta semana
                    if semana_inicio <= fecha_vencimiento <= semana_fin:
                        # Verificar si el pedido ya está cobrado
                        pedido_cobrado = False
                        if pedido.folio_factura:
                            # Buscar factura relacionada
                            factura_pedido = next((f for f in facturas if f.folio_factura == pedido.folio_factura), None)
                            if factura_pedido and factura_pedido.uuid_factura:
                                # Buscar cobranzas de esta factura
                                cobranzas_factura = [c for c in cobranzas or [] if c.uuid_factura_relacionada == factura_pedido.uuid_factura]
                                if cobranzas_factura:
                                    total_cobrado_factura = sum(c.importe_pagado for c in cobranzas_factura)
                                    if factura_pedido.monto_total > 0:
                                        porcentaje_cobrado = total_cobrado_factura / factura_pedido.monto_total
                                        if porcentaje_cobrado >= 0.99:  # 99% o más cobrado
                                            pedido_cobrado = True
                        
                        # Solo incluir en cobranza esperada si NO está cobrado
                        if not pedido_cobrado:
                            monto_pedido = getattr(pedido, 'importe_sin_iva', 0) or 0
                            
                            # Solo considerar si hay monto positivo
                            if monto_pedido > 0:
                                cobranza_esperada += monto_pedido
                                pedidos_pendientes += 1
                                
                except Exception as e:
                    logger.warning(f"Error procesando pedido {pedido.id}: {str(e)}")
                    continue
            
            # Calcular cobranza real para esta semana
            if cobranzas:
                if aplicar_filtro_proporcional:
                    # Calcular cobranza proporcional basada en la lógica: 
                    # Monto_Factura × %_Cobrado × %_Proporción_Pedido
                    for cobranza in cobranzas:
                        if cobranza.fecha_pago and semana_inicio <= cobranza.fecha_pago <= semana_fin:
                            uuid_factura = cobranza.uuid_factura_relacionada
                            if uuid_factura:
                                # Buscar la factura relacionada
                                factura_relacionada = next((f for f in facturas if f.uuid_factura == uuid_factura), None)
                                if factura_relacionada:
                                    # Calcular el porcentaje cobrado de esta factura
                                    if factura_relacionada.monto_total > 0:
                                        porcentaje_cobrado = cobranza.importe_pagado / factura_relacionada.monto_total
                                    else:
                                        porcentaje_cobrado = 0
                                    
                                    # Calcular la proporción de pedidos filtrados en esta factura
                                    # Sumar todos los pedidos filtrados que pertenecen a esta factura
                                    monto_pedidos_filtrados_factura = 0
                                    for pedido in pedidos:
                                        if pedido.folio_factura == factura_relacionada.folio_factura:
                                            monto_pedidos_filtrados_factura += pedido.importe_sin_iva or 0
                                    
                                    # Calcular la proporción del pedido en la factura
                                    if factura_relacionada.monto_total > 0:
                                        proporcion_pedido = monto_pedidos_filtrados_factura / factura_relacionada.monto_total
                                    else:
                                        proporcion_pedido = 0
                                    
                                    # Aplicar la fórmula: Monto_Factura × %_Cobrado × %_Proporción_Pedido
                                    cobranza_proporcional = factura_relacionada.monto_total * porcentaje_cobrado * proporcion_pedido
                                    cobranza_real += cobranza_proporcional
                                    
                                    logger.debug(f"Factura {factura_relacionada.folio_factura}: monto_total=${factura_relacionada.monto_total}, "
                                               f"porcentaje_cobrado={porcentaje_cobrado:.2%}, proporcion_pedido={proporcion_pedido:.2%}, "
                                               f"cobranza_proporcional=${cobranza_proporcional:.2f}")
                else:
                    # Sin filtro, considerar todas las cobranzas
                    for cobranza in cobranzas:
                        if cobranza.fecha_pago and semana_inicio <= cobranza.fecha_pago <= semana_fin:
                            cobranza_real += cobranza.importe_pagado
            
            # Solo incluir semanas con datos
            if cobranza_esperada > 0 or cobranza_real > 0:
                expectativa[semana_key] = {
                    'cobranza_esperada': cobranza_esperada,
                    'cobranza_real': cobranza_real,
                    'pedidos_pendientes': pedidos_pendientes
                }
        
        logger.info(f"Expectativa de cobranza calculada: {len(expectativa)} semanas con datos")
        return expectativa
