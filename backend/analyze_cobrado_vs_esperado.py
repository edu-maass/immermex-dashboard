#!/usr/bin/env python3
"""
Script para analizar qué pedidos ya están cobrados y ajustar la lógica de cobranza esperada
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cargar configuración de producción
from dotenv import load_dotenv
load_dotenv('production.env')

from database import engine, Pedido, Facturacion, Cobranza
from database_service import DatabaseService
from sqlalchemy.orm import sessionmaker
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_cobrado_vs_esperado():
    """Analiza qué pedidos ya están cobrados vs esperados"""
    
    try:
        logger.info("=== ANÁLISIS COBRADO VS ESPERADO ===")
        
        # Crear instancia del servicio de base de datos
        Session = sessionmaker(bind=engine)
        session = Session()
        db_service = DatabaseService(session)
        
        # Simular filtro por pedido 1890
        filtros = {'pedidos': ['1890']}
        
        # Obtener datos
        pedidos = db_service.db.query(Pedido).filter(Pedido.pedido == "1890").all()
        facturas_relacionadas = db_service._get_facturas_related_to_pedidos(pedidos)
        
        uuids_facturas = {f.uuid_factura for f in facturas_relacionadas if f.uuid_factura}
        cobranzas_relacionadas = db_service.db.query(Cobranza).filter(
            Cobranza.uuid_factura_relacionada.in_(uuids_facturas)
        ).all()
        
        logger.info(f"📊 Datos obtenidos:")
        logger.info(f"   - Pedidos: {len(pedidos)}")
        logger.info(f"   - Facturas: {len(facturas_relacionadas)}")
        logger.info(f"   - Cobranzas: {len(cobranzas_relacionadas)}")
        
        # Analizar cada pedido
        logger.info(f"\n📦 Análisis por pedido:")
        
        pedidos_cobrados = []
        pedidos_pendientes = []
        
        for pedido in pedidos:
            logger.info(f"\n🔍 Pedido ID {pedido.id}:")
            logger.info(f"   - Pedido: {pedido.pedido}")
            logger.info(f"   - Folio factura: {pedido.folio_factura}")
            logger.info(f"   - Importe sin IVA: ${pedido.importe_sin_iva:.2f}")
            logger.info(f"   - Fecha factura: {pedido.fecha_factura}")
            logger.info(f"   - Días crédito: {pedido.dias_credito}")
            
            # Buscar facturas relacionadas con este pedido
            facturas_pedido = [f for f in facturas_relacionadas if f.folio_factura == pedido.folio_factura]
            
            if facturas_pedido:
                factura = facturas_pedido[0]
                logger.info(f"   - Factura relacionada: {factura.folio_factura}")
                logger.info(f"   - UUID factura: {factura.uuid_factura}")
                logger.info(f"   - Monto total factura: ${factura.monto_total:.2f}")
                
                # Buscar cobranzas de esta factura
                cobranzas_factura = [c for c in cobranzas_relacionadas if c.uuid_factura_relacionada == factura.uuid_factura]
                
                if cobranzas_factura:
                    total_cobrado_factura = sum(c.importe_pagado for c in cobranzas_factura)
                    logger.info(f"   - Cobranzas encontradas: {len(cobranzas_factura)}")
                    logger.info(f"   - Total cobrado factura: ${total_cobrado_factura:.2f}")
                    
                    # Calcular proporción cobrada de este pedido
                    if factura.monto_total > 0:
                        porcentaje_cobrado_factura = total_cobrado_factura / factura.monto_total
                        monto_cobrado_pedido = pedido.importe_sin_iva * porcentaje_cobrado_factura
                        
                        logger.info(f"   - Porcentaje cobrado factura: {porcentaje_cobrado_factura:.1%}")
                        logger.info(f"   - Monto cobrado pedido: ${monto_cobrado_pedido:.2f}")
                        
                        if porcentaje_cobrado_factura >= 0.99:  # 99% o más cobrado
                            pedidos_cobrados.append({
                                'pedido': pedido,
                                'monto_cobrado': monto_cobrado_pedido,
                                'porcentaje': porcentaje_cobrado_factura
                            })
                            logger.info(f"   ✅ PEDIDO COBRADO ({porcentaje_cobrado_factura:.1%})")
                        else:
                            pedidos_pendientes.append({
                                'pedido': pedido,
                                'monto_pendiente': pedido.importe_sin_iva - monto_cobrado_pedido,
                                'porcentaje': porcentaje_cobrado_factura
                            })
                            logger.info(f"   ⏳ PEDIDO PENDIENTE ({porcentaje_cobrado_factura:.1%})")
                    else:
                        logger.warning(f"   ⚠️ Monto total de factura es 0")
                else:
                    logger.info(f"   - Sin cobranzas")
                    pedidos_pendientes.append({
                        'pedido': pedido,
                        'monto_pendiente': pedido.importe_sin_iva,
                        'porcentaje': 0
                    })
                    logger.info(f"   ⏳ PEDIDO PENDIENTE (0%)")
            else:
                logger.warning(f"   ⚠️ Sin factura relacionada")
                pedidos_pendientes.append({
                    'pedido': pedido,
                    'monto_pendiente': pedido.importe_sin_iva,
                    'porcentaje': 0
                })
        
        # Resumen
        logger.info(f"\n📊 RESUMEN:")
        logger.info(f"   - Pedidos cobrados: {len(pedidos_cobrados)}")
        logger.info(f"   - Pedidos pendientes: {len(pedidos_pendientes)}")
        
        total_cobrado = sum(p['monto_cobrado'] for p in pedidos_cobrados)
        total_pendiente = sum(p['monto_pendiente'] for p in pedidos_pendientes)
        
        logger.info(f"   - Total cobrado: ${total_cobrado:.2f}")
        logger.info(f"   - Total pendiente: ${total_pendiente:.2f}")
        logger.info(f"   - Total pedidos: ${total_cobrado + total_pendiente:.2f}")
        
        # Comparar con KPIs actuales
        logger.info(f"\n🔍 Comparación con KPIs actuales:")
        kpis = db_service.calculate_kpis(filtros)
        
        facturacion_total = kpis.get('facturacion_total', 0)
        cobranza_total = kpis.get('cobranza_total', 0)
        
        expectativa = kpis.get('expectativa_cobranza', {})
        cobranza_esperada_total = sum(datos.get('cobranza_esperada', 0) for datos in expectativa.values())
        
        logger.info(f"   - Facturación total (KPIs): ${facturacion_total:.2f}")
        logger.info(f"   - Cobranza total (KPIs): ${cobranza_total:.2f}")
        logger.info(f"   - Cobranza esperada total (KPIs): ${cobranza_esperada_total:.2f}")
        
        logger.info(f"\n   - Total cobrado (análisis): ${total_cobrado:.2f}")
        logger.info(f"   - Total pendiente (análisis): ${total_pendiente:.2f}")
        
        # Verificar si la lógica actual está correcta
        diferencia_cobrado = abs(cobranza_total - total_cobrado)
        diferencia_esperado = abs(cobranza_esperada_total - total_pendiente)
        
        logger.info(f"\n✅ VERIFICACIÓN:")
        logger.info(f"   - Diferencia cobrado: ${diferencia_cobrado:.2f}")
        logger.info(f"   - Diferencia esperado: ${diferencia_esperado:.2f}")
        
        if diferencia_esperado > 1000:
            logger.warning(f"⚠️ La cobranza esperada debería ser ${total_pendiente:.2f}, no ${cobranza_esperada_total:.2f}")
            logger.warning(f"   - Diferencia: ${diferencia_esperado:.2f}")
        
    except Exception as e:
        logger.error(f"❌ Error en análisis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db_service' in locals():
            db_service.db.close()

if __name__ == "__main__":
    analyze_cobrado_vs_esperado()
