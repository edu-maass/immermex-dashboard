"""
Script de migración de datos de tabla 'pedidos' a 'pedidos_compras' en PostgreSQL
Migra datos existentes a la estructura optimizada
"""

from database import SessionLocal, Pedido, PedidosCompras, Facturacion
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_pedidos_to_pedidos_compras():
    """Migra todos los datos de pedidos a pedidos_compras"""
    
    logger.info("Iniciando migración de pedidos a pedidos_compras...")
    
    db = SessionLocal()
    
    try:
        # Obtener todos los pedidos existentes
        pedidos_existentes = db.query(Pedido).all()
        logger.info(f"Encontrados {len(pedidos_existentes)} pedidos para migrar")
        
        if not pedidos_existentes:
            logger.info("No hay pedidos para migrar")
            return
        
        # Obtener información de facturación para enriquecer datos
        facturas = db.query(Facturacion).all()
        facturas_por_folio = {}
        
        for factura in facturas:
            if factura.folio_factura:
                folio_limpio = str(factura.folio_factura).strip()
                facturas_por_folio[folio_limpio] = factura
        
        # Contadores para estadísticas
        migrados_exitosos = 0
        migrados_con_errores = 0
        
        # Migrar cada pedido
        for pedido in pedidos_existentes:
            try:
                # Buscar factura relacionada
                factura_relacionada = None
                if pedido.folio_factura:
                    folio_limpio = str(pedido.folio_factura).strip()
                    factura_relacionada = facturas_por_folio.get(folio_limpio)
                
                # Calcular importe con IVA (asumiendo 16% de IVA)
                importe_con_iva = pedido.importe_sin_iva * 1.16 if pedido.importe_sin_iva else 0.0
                
                # Crear registro en pedidos_compras con la estructura real de PostgreSQL
                pedido_compras = PedidosCompras(
                    compra_imi=0,  # Campo específico de compras, inicializar en 0
                    folio_factura=pedido.folio_factura,
                    material_codigo=pedido.material,  # Mapear material a material_codigo
                    kg=pedido.kg,
                    precio_unitario=pedido.precio_unitario,
                    importe_sin_iva=pedido.importe_sin_iva,
                    importe_con_iva=importe_con_iva,
                    dias_credito=pedido.dias_credito,
                    fecha_factura=pedido.fecha_factura,
                    fecha_pago=pedido.fecha_pago,
                    archivo_id=pedido.archivo_id,
                    created_at=pedido.created_at,
                    updated_at=pedido.updated_at
                )
                
                db.add(pedido_compras)
                migrados_exitosos += 1
                
                # Log de progreso cada 100 registros
                if migrados_exitosos % 100 == 0:
                    logger.info(f"Progreso: {migrados_exitosos} pedidos migrados...")
                
            except Exception as e:
                migrados_con_errores += 1
                logger.error(f"Error migrando pedido {pedido.id}: {str(e)}")
                continue
        
        # Confirmar cambios
        db.commit()
        
        # Estadísticas finales
        logger.info("Migración completada!")
        logger.info(f"Pedidos migrados exitosamente: {migrados_exitosos}")
        logger.info(f"Pedidos con errores: {migrados_con_errores}")
        
        # Verificar migración
        total_pedidos_compras = db.query(PedidosCompras).count()
        logger.info(f"Total de registros en pedidos_compras: {total_pedidos_compras}")
        
        return {
            'migrados_exitosos': migrados_exitosos,
            'migrados_con_errores': migrados_con_errores,
            'total_pedidos_compras': total_pedidos_compras
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error crítico en la migración: {str(e)}")
        raise
    finally:
        db.close()

def verify_migration():
    """Verifica que la migración se completó correctamente"""
    
    logger.info("Verificando migración...")
    
    db = SessionLocal()
    
    try:
        # Contar registros en ambas tablas
        total_pedidos = db.query(Pedido).count()
        total_pedidos_compras = db.query(PedidosCompras).count()
        
        logger.info(f"Registros en tabla 'pedidos': {total_pedidos}")
        logger.info(f"Registros en tabla 'pedidos_compras': {total_pedidos_compras}")
        
        # Verificar algunos registros específicos
        sample_pedidos = db.query(Pedido).limit(5).all()
        
        for pedido in sample_pedidos:
            pedido_compras = db.query(PedidosCompras).filter(
                PedidosCompras.folio_factura == pedido.folio_factura,
                PedidosCompras.material_codigo == pedido.material
            ).first()
            
            if pedido_compras:
                logger.info(f"Verificado: Pedido {pedido.id} -> PedidosCompras {pedido_compras.id}")
            else:
                logger.warning(f"No encontrado: Pedido {pedido.id} en pedidos_compras")
        
        return {
            'total_pedidos': total_pedidos,
            'total_pedidos_compras': total_pedidos_compras,
            'migration_successful': total_pedidos_compras > 0
        }
        
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Ejecutar migración
    resultado = migrate_pedidos_to_pedidos_compras()
    
    # Verificar migración
    verificacion = verify_migration()
    
    print("\n" + "="*50)
    print("RESUMEN DE MIGRACION")
    print("="*50)
    print(f"Pedidos migrados exitosamente: {resultado['migrados_exitosos']}")
    print(f"Pedidos con errores: {resultado['migrados_con_errores']}")
    print(f"Total en pedidos_compras: {resultado['total_pedidos_compras']}")
    print(f"Migracion exitosa: {verificacion['migration_successful']}")
    print("="*50)
