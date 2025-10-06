"""
Script para crear la tabla pedidos_compras optimizada en PostgreSQL
"""

from database import engine, Base, PedidosCompras
from sqlalchemy import inspect
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_existing_tables():
    """Verifica las tablas existentes en la base de datos"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("Tablas disponibles en PostgreSQL:")
    for table in tables:
        print(f"- {table}")
    
    return tables

def check_pedidos_structure():
    """Verifica la estructura de la tabla pedidos existente"""
    inspector = inspect(engine)
    
    if 'pedidos' in inspector.get_table_names():
        columns = inspector.get_columns('pedidos')
        print("\nEstructura de tabla 'pedidos':")
        for col in columns:
            print(f"- {col['name']}: {col['type']}")
        return columns
    else:
        print("Tabla 'pedidos' no encontrada")
        return []

def create_pedidos_compras_table():
    """Crea la tabla pedidos_compras optimizada"""
    try:
        # Verificar si la tabla ya existe
        inspector = inspect(engine)
        if 'pedidos_compras' in inspector.get_table_names():
            print("✅ Tabla 'pedidos_compras' ya existe")
            return True
        
        # Crear la tabla
        print("🚀 Creando tabla 'pedidos_compras'...")
        PedidosCompras.__table__.create(engine, checkfirst=True)
        print("✅ Tabla 'pedidos_compras' creada exitosamente")
        
        # Verificar la nueva estructura
        columns = inspector.get_columns('pedidos_compras')
        print("\nEstructura de tabla 'pedidos_compras' creada:")
        for col in columns:
            print(f"- {col['name']}: {col['type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando tabla 'pedidos_compras': {str(e)}")
        return False

def migrate_data_from_pedidos():
    """Migra datos de la tabla pedidos a pedidos_compras"""
    try:
        from database import SessionLocal, Pedido, PedidosCompras, Facturacion
        from datetime import datetime
        
        db = SessionLocal()
        
        # Obtener todos los pedidos existentes
        pedidos_existentes = db.query(Pedido).all()
        print(f"\n📊 Encontrados {len(pedidos_existentes)} pedidos para migrar")
        
        if not pedidos_existentes:
            print("✅ No hay pedidos para migrar")
            return True
        
        # Obtener información de facturación para enriquecer datos
        facturas = db.query(Facturacion).all()
        facturas_por_folio = {}
        
        for factura in facturas:
            if factura.folio_factura:
                folio_limpio = str(factura.folio_factura).strip()
                facturas_por_folio[folio_limpio] = factura
        
        # Migrar cada pedido
        migrados = 0
        errores = 0
        
        for pedido in pedidos_existentes:
            try:
                # Buscar factura relacionada
                factura_relacionada = None
                if pedido.folio_factura:
                    folio_limpio = str(pedido.folio_factura).strip()
                    factura_relacionada = facturas_por_folio.get(folio_limpio)
                
                # Crear registro en pedidos_compras
                pedido_compras = PedidosCompras(
                    # Campos básicos del pedido original
                    folio_factura=pedido.folio_factura,
                    pedido=pedido.pedido,
                    kg=pedido.kg,
                    precio_unitario=pedido.precio_unitario,
                    importe_sin_iva=pedido.importe_sin_iva,
                    material=pedido.material,
                    dias_credito=pedido.dias_credito,
                    fecha_factura=pedido.fecha_factura,
                    fecha_pago=pedido.fecha_pago,
                    archivo_id=pedido.archivo_id,
                    
                    # Campos enriquecidos desde facturación
                    cliente=factura_relacionada.cliente if factura_relacionada else None,
                    agente=factura_relacionada.agente if factura_relacionada else None,
                    serie_factura=factura_relacionada.serie_factura if factura_relacionada else None,
                    uuid_factura=factura_relacionada.uuid_factura if factura_relacionada else None,
                    monto_neto=factura_relacionada.monto_neto if factura_relacionada else 0.0,
                    monto_total=factura_relacionada.monto_total if factura_relacionada else 0.0,
                    saldo_pendiente=factura_relacionada.saldo_pendiente if factura_relacionada else 0.0,
                    importe_cobrado=factura_relacionada.importe_cobrado if factura_relacionada else 0.0,
                    fecha_cobro=factura_relacionada.fecha_cobro if factura_relacionada else None,
                    dias_cobro=factura_relacionada.dias_cobro if factura_relacionada else 0,
                    
                    # Campos de categorización
                    categoria_material=_categorize_material(pedido.material),
                    subcategoria_material=_subcategorize_material(pedido.material),
                    unidad_medida='KG',
                    moneda='MXN',
                    tipo_cambio=1.0,
                    
                    # Campos de estado
                    estado_pedido='activo',
                    estado_pago='pagado' if pedido.fecha_pago else 'pendiente',
                    estado_facturacion='facturado',
                    
                    # Campos temporales calculados
                    mes=pedido.fecha_factura.month if pedido.fecha_factura else None,
                    año=pedido.fecha_factura.year if pedido.fecha_factura else None,
                    trimestre=_calculate_trimestre(pedido.fecha_factura) if pedido.fecha_factura else None,
                    semana=pedido.fecha_factura.isocalendar()[1] if pedido.fecha_factura else None,
                    
                    # Campos de auditoría
                    archivo_origen=f"migrated_from_pedidos_{datetime.now().strftime('%Y%m%d')}",
                    created_at=pedido.created_at,
                    updated_at=pedido.updated_at,
                    procesado_at=datetime.utcnow(),
                )
                
                db.add(pedido_compras)
                migrados += 1
                
                if migrados % 100 == 0:
                    print(f"📈 Progreso: {migrados} pedidos migrados...")
                
            except Exception as e:
                errores += 1
                print(f"⚠️ Error migrando pedido {pedido.id}: {str(e)}")
                continue
        
        # Confirmar cambios
        db.commit()
        
        print(f"\n🎉 Migración completada!")
        print(f"✅ Pedidos migrados: {migrados}")
        print(f"❌ Errores: {errores}")
        
        # Verificar migración
        total_pedidos_compras = db.query(PedidosCompras).count()
        print(f"📊 Total registros en pedidos_compras: {total_pedidos_compras}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"💥 Error en migración: {str(e)}")
        return False

def _categorize_material(material: str) -> str:
    """Categoriza el material basado en su código o nombre"""
    if not material:
        return 'Sin categoría'
    
    material_upper = material.upper()
    
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

if __name__ == "__main__":
    print("🔍 Verificando estructura de base de datos...")
    
    # Verificar tablas existentes
    tables = check_existing_tables()
    
    # Verificar estructura de pedidos
    pedidos_columns = check_pedidos_structure()
    
    # Crear tabla pedidos_compras
    if create_pedidos_compras_table():
        print("\n🚀 Iniciando migración de datos...")
        migrate_data_from_pedidos()
    
    print("\n✅ Proceso completado!")
