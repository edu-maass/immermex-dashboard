"""
Script de migración de datos de tabla 'pedidos' a 'pedidos_compras'
Migra todos los datos existentes y enriquece con información adicional
"""

import hashlib
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, Pedido, PedidosCompras, Facturacion, Cobranza, init_db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_hash_registro(pedido_data: dict) -> str:
    """Genera hash único para evitar duplicados"""
    # Crear string único basado en campos clave
    hash_string = f"{pedido_data.get('folio_factura', '')}_{pedido_data.get('pedido', '')}_{pedido_data.get('material', '')}_{pedido_data.get('kg', 0)}"
    return hashlib.md5(hash_string.encode()).hexdigest()

def enrich_pedido_data(pedido: Pedido, db: Session) -> dict:
    """Enriquece datos del pedido con información adicional de facturación y cobranza"""
    
    # Buscar información de facturación relacionada
    factura_info = db.query(Facturacion).filter(
        Facturacion.folio_factura == pedido.folio_factura
    ).first()
    
    # Buscar información de cobranza relacionada
    cobranza_info = None
    if factura_info and factura_info.uuid_factura:
        cobranza_info = db.query(Cobranza).filter(
            Cobranza.uuid_factura_relacionada == factura_info.uuid_factura
        ).first()
    
    # Preparar datos enriquecidos
    enriched_data = {
        # Campos básicos del pedido original
        'folio_factura': pedido.folio_factura,
        'pedido': pedido.pedido,
        'kg': pedido.kg,
        'precio_unitario': pedido.precio_unitario,
        'importe_sin_iva': pedido.importe_sin_iva,
        'material': pedido.material,
        'dias_credito': pedido.dias_credito,
        'fecha_factura': pedido.fecha_factura,
        'fecha_pago': pedido.fecha_pago,
        'archivo_id': pedido.archivo_id,
        
        # Campos enriquecidos desde facturación
        'cliente': factura_info.cliente if factura_info else None,
        'agente': factura_info.agente if factura_info else None,
        'serie_factura': factura_info.serie_factura if factura_info else None,
        'uuid_factura': factura_info.uuid_factura if factura_info else None,
        'monto_neto': factura_info.monto_neto if factura_info else 0.0,
        'monto_total': factura_info.monto_total if factura_info else 0.0,
        'saldo_pendiente': factura_info.saldo_pendiente if factura_info else 0.0,
        'importe_cobrado': factura_info.importe_cobrado if factura_info else 0.0,
        'fecha_cobro': factura_info.fecha_cobro if factura_info else None,
        'dias_cobro': factura_info.dias_cobro if factura_info else 0,
        
        # Campos de categorización
        'categoria_material': _categorize_material(pedido.material),
        'subcategoria_material': _subcategorize_material(pedido.material),
        'unidad_medida': 'KG',
        'moneda': 'MXN',
        'tipo_cambio': 1.0,
        
        # Campos de estado
        'estado_pedido': 'activo',
        'estado_pago': 'pagado' if pedido.fecha_pago else 'pendiente',
        'estado_facturacion': 'facturado',
        
        # Campos temporales calculados
        'mes': pedido.fecha_factura.month if pedido.fecha_factura else None,
        'año': pedido.fecha_factura.year if pedido.fecha_factura else None,
        'trimestre': _calculate_trimestre(pedido.fecha_factura) if pedido.fecha_factura else None,
        'semana': pedido.fecha_factura.isocalendar()[1] if pedido.fecha_factura else None,
        
        # Campos de auditoría
        'archivo_origen': f"migrated_from_pedidos_{datetime.now().strftime('%Y%m%d')}",
        'created_at': pedido.created_at,
        'updated_at': pedido.updated_at,
        'procesado_at': datetime.utcnow(),
    }
    
    # Generar hash único
    enriched_data['hash_registro'] = generate_hash_registro(enriched_data)
    
    return enriched_data

def _categorize_material(material: str) -> str:
    """Categoriza el material basado en su código o nombre"""
    if not material:
        return 'Sin categoría'
    
    material_upper = material.upper()
    
    # Lógica de categorización basada en códigos comunes
    if any(code in material_upper for code in ['ACERO', 'STEEL', 'IRON']):
        return 'Acero'
    elif any(code in material_upper for code in ['ALUMINIO', 'ALUMINIUM', 'AL']):
        return 'Aluminio'
    elif any(code in material_upper for code in ['COBRE', 'COPPER', 'CU']):
        return 'Cobre'
    elif any(code in material_upper for code in ['ZINC', 'ZN']):
        return 'Zinc'
    elif any(code in material_upper for code in ['PLOMO', 'LEAD', 'PB']):
        return 'Plomo'
    elif any(code in material_upper for code in ['NICKEL', 'NI']):
        return 'Níquel'
    else:
        return 'Otros Metales'

def _subcategorize_material(material: str) -> str:
    """Subcategoriza el material con más detalle"""
    if not material:
        return 'Sin subcategoría'
    
    material_upper = material.upper()
    
    # Lógica de subcategorización
    if any(code in material_upper for code in ['LAMINA', 'SHEET', 'PLATE']):
        return 'Lámina'
    elif any(code in material_upper for code in ['VARILLA', 'ROD', 'BAR']):
        return 'Varilla'
    elif any(code in material_upper for code in ['TUBO', 'TUBE', 'PIPE']):
        return 'Tubo'
    elif any(code in material_upper for code in ['ALAMBRE', 'WIRE']):
        return 'Alambre'
    elif any(code in material_upper for code in ['PERFIL', 'PROFILE']):
        return 'Perfil'
    else:
        return 'General'

def _calculate_trimestre(fecha: datetime) -> int:
    """Calcula el trimestre basado en la fecha"""
    if not fecha:
        return None
    return (fecha.month - 1) // 3 + 1

def migrate_pedidos_to_pedidos_compras():
    """Migra todos los datos de pedidos a pedidos_compras"""
    
    logger.info("🚀 Iniciando migración de pedidos a pedidos_compras...")
    
    # Inicializar base de datos
    init_db()
    
    db = SessionLocal()
    
    try:
        # Obtener todos los pedidos existentes
        pedidos_existentes = db.query(Pedido).all()
        logger.info(f"📊 Encontrados {len(pedidos_existentes)} pedidos para migrar")
        
        if not pedidos_existentes:
            logger.info("✅ No hay pedidos para migrar")
            return
        
        # Contadores para estadísticas
        migrados_exitosos = 0
        migrados_con_errores = 0
        duplicados_omitidos = 0
        
        # Migrar cada pedido
        for pedido in pedidos_existentes:
            try:
                # Enriquecer datos del pedido
                datos_enriquecidos = enrich_pedido_data(pedido, db)
                
                # Verificar si ya existe un registro con el mismo hash
                registro_existente = db.query(PedidosCompras).filter(
                    PedidosCompras.hash_registro == datos_enriquecidos['hash_registro']
                ).first()
                
                if registro_existente:
                    duplicados_omitidos += 1
                    logger.debug(f"⚠️ Registro duplicado omitido: {pedido.id}")
                    continue
                
                # Crear nuevo registro en pedidos_compras
                nuevo_pedido_compras = PedidosCompras(**datos_enriquecidos)
                db.add(nuevo_pedido_compras)
                
                migrados_exitosos += 1
                
                # Log de progreso cada 100 registros
                if migrados_exitosos % 100 == 0:
                    logger.info(f"📈 Progreso: {migrados_exitosos} pedidos migrados...")
                
            except Exception as e:
                migrados_con_errores += 1
                logger.error(f"❌ Error migrando pedido {pedido.id}: {str(e)}")
                continue
        
        # Confirmar cambios
        db.commit()
        
        # Estadísticas finales
        logger.info("🎉 Migración completada!")
        logger.info(f"✅ Pedidos migrados exitosamente: {migrados_exitosos}")
        logger.info(f"⚠️ Pedidos con errores: {migrados_con_errores}")
        logger.info(f"🔄 Duplicados omitidos: {duplicados_omitidos}")
        
        # Verificar migración
        total_pedidos_compras = db.query(PedidosCompras).count()
        logger.info(f"📊 Total de registros en pedidos_compras: {total_pedidos_compras}")
        
        return {
            'migrados_exitosos': migrados_exitosos,
            'migrados_con_errores': migrados_con_errores,
            'duplicados_omitidos': duplicados_omitidos,
            'total_pedidos_compras': total_pedidos_compras
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"💥 Error crítico en la migración: {str(e)}")
        raise
    finally:
        db.close()

def verify_migration():
    """Verifica que la migración se completó correctamente"""
    
    logger.info("🔍 Verificando migración...")
    
    db = SessionLocal()
    
    try:
        # Contar registros en ambas tablas
        total_pedidos = db.query(Pedido).count()
        total_pedidos_compras = db.query(PedidosCompras).count()
        
        logger.info(f"📊 Registros en tabla 'pedidos': {total_pedidos}")
        logger.info(f"📊 Registros en tabla 'pedidos_compras': {total_pedidos_compras}")
        
        # Verificar algunos registros específicos
        sample_pedidos = db.query(Pedido).limit(5).all()
        
        for pedido in sample_pedidos:
            pedido_compras = db.query(PedidosCompras).filter(
                PedidosCompras.folio_factura == pedido.folio_factura,
                PedidosCompras.pedido == pedido.pedido
            ).first()
            
            if pedido_compras:
                logger.info(f"✅ Verificado: Pedido {pedido.id} -> PedidosCompras {pedido_compras.id}")
            else:
                logger.warning(f"⚠️ No encontrado: Pedido {pedido.id} en pedidos_compras")
        
        return {
            'total_pedidos': total_pedidos,
            'total_pedidos_compras': total_pedidos_compras,
            'migration_successful': total_pedidos_compras > 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error en verificación: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Ejecutar migración
    resultado = migrate_pedidos_to_pedidos_compras()
    
    # Verificar migración
    verificacion = verify_migration()
    
    print("\n" + "="*50)
    print("RESUMEN DE MIGRACIÓN")
    print("="*50)
    print(f"Pedidos migrados exitosamente: {resultado['migrados_exitosos']}")
    print(f"Pedidos con errores: {resultado['migrados_con_errores']}")
    print(f"Duplicados omitidos: {resultado['duplicados_omitidos']}")
    print(f"Total en pedidos_compras: {resultado['total_pedidos_compras']}")
    print(f"Migración exitosa: {verificacion['migration_successful']}")
    print("="*50)
