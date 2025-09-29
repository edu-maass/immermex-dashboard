"""
Script para consultar folios de factura que tienen UUID coincidente con CFDIs Relacionados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, init_db, Pedido, Facturacion, CFDIRelacionado
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consultar_folios_con_cfdi():
    """Consulta folios de factura que tienen UUID coincidente con CFDIs Relacionados"""
    
    try:
        # Inicializar base de datos
        init_db()
        db = SessionLocal()
        
        logger.info("🔍 Consultando folios de factura con UUID coincidente en CFDIs Relacionados...")
        
        # Verificar si hay datos en las tablas
        count_facturas = db.query(Facturacion).count()
        count_cfdis = db.query(CFDIRelacionado).count()
        
        logger.info(f"📊 Estado de la base de datos:")
        logger.info(f"   Facturas: {count_facturas}")
        logger.info(f"   CFDIs Relacionados: {count_cfdis}")
        
        if count_facturas == 0:
            logger.warning("❌ No hay facturas en la base de datos")
            logger.info("💡 Necesitas subir un archivo Excel con datos")
            return []
        
        if count_cfdis == 0:
            logger.warning("❌ No hay CFDIs Relacionados en la base de datos")
            logger.info("💡 Los CFDIs Relacionados se cargan desde la hoja 'cfdi' del Excel")
            return []
        
        # Obtener todos los UUIDs de CFDIs Relacionados que no sean nulos o vacíos
        cfdi_uuids = db.query(CFDIRelacionado.uuid_factura_relacionada).filter(
            CFDIRelacionado.uuid_factura_relacionada.isnot(None),
            CFDIRelacionado.uuid_factura_relacionada != ''
        ).distinct().all()
        
        cfdi_uuids_list = [uuid[0] for uuid in cfdi_uuids]
        logger.info(f"📊 Encontrados {len(cfdi_uuids_list)} UUIDs únicos en CFDIs Relacionados")
        
        if len(cfdi_uuids_list) == 0:
            logger.warning("❌ No se encontraron CFDIs Relacionados con UUID válido")
            logger.info("💡 Verifica que los CFDIs tengan el campo 'uuid_factura_relacionada' lleno")
            return []
        
        # Buscar facturas que tengan estos UUIDs
        facturas_con_cfdi = db.query(Facturacion).filter(
            Facturacion.uuid_factura.in_(cfdi_uuids_list)
        ).all()
        
        logger.info(f"📄 Encontradas {len(facturas_con_cfdi)} facturas con UUID coincidente")
        
        # Crear lista de resultados
        folios_con_cfdi = []
        
        for factura in facturas_con_cfdi:
            # Buscar CFDIs relacionados con esta factura
            cfdis_relacionados = db.query(CFDIRelacionado).filter(
                CFDIRelacionado.uuid_factura_relacionada == factura.uuid_factura
            ).all()
            
            total_cfdi = sum(cfdi.importe_relacion for cfdi in cfdis_relacionados)
            
            folios_con_cfdi.append({
                'folio_factura': factura.folio_factura,
                'uuid_factura': factura.uuid_factura,
                'cliente': factura.cliente,
                'fecha_factura': factura.fecha_factura,
                'monto_total': factura.monto_total,
                'monto_neto': factura.monto_neto,
                'cfdis_count': len(cfdis_relacionados),
                'total_cfdi': total_cfdi
            })
        
        # Mostrar resultados
        logger.info(f"\n📋 LISTA DE FOLIOS DE FACTURA CON CFDIs RELACIONADOS:")
        logger.info("=" * 80)
        
        for i, folio in enumerate(folios_con_cfdi, 1):
            logger.info(f"{i:3d}. Folio: {folio['folio_factura']}")
            logger.info(f"     UUID: {folio['uuid_factura']}")
            logger.info(f"     Cliente: {folio['cliente']}")
            logger.info(f"     Fecha: {folio['fecha_factura']}")
            logger.info(f"     Monto Total: ${folio['monto_total']:,.2f}")
            logger.info(f"     Monto Neto: ${folio['monto_neto']:,.2f}")
            logger.info(f"     CFDIs Relacionados: {folio['cfdis_count']}")
            logger.info(f"     Total CFDIs: ${folio['total_cfdi']:,.2f}")
            logger.info("")
        
        # Mostrar resumen
        logger.info(f"📊 RESUMEN:")
        logger.info(f"   Total folios con CFDIs: {len(folios_con_cfdi)}")
        logger.info(f"   Total CFDIs relacionados: {sum(f['cfdis_count'] for f in folios_con_cfdi)}")
        logger.info(f"   Monto total CFDIs: ${sum(f['total_cfdi'] for f in folios_con_cfdi):,.2f}")
        
        # Crear lista simple de folios para fácil copia
        folios_lista = [f['folio_factura'] for f in folios_con_cfdi]
        
        logger.info(f"\n📝 LISTA SIMPLE DE FOLIOS:")
        logger.info("Folios: " + ", ".join(folios_lista))
        
        return folios_con_cfdi
        
    except Exception as e:
        logger.error(f"❌ Error consultando datos: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []
        
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    folios = consultar_folios_con_cfdi()
    if folios:
        print(f"\n✅ Se encontraron {len(folios)} folios de factura con CFDIs relacionados")
        print("📋 Lista completa mostrada arriba")
    else:
        print("\n❌ No se encontraron folios con CFDIs relacionados")
        print("💡 Asegúrate de tener datos cargados en el sistema")
