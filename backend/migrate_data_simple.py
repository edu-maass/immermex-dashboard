"""
Script de migración de datos de tabla 'pedidos' a 'pedidos_compras'
Migra datos existentes de manera segura con verificaciones
"""

from database import SessionLocal, Pedido, PedidosCompras, Facturacion
from datetime import datetime
from sqlalchemy import text
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    try:
        db = SessionLocal()
        # Probar consulta simple
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Conexion a base de datos verificada")
        return True
    except Exception as e:
        logger.error(f"Error de conexion a base de datos: {str(e)}")
        return False

def check_tables_exist():
    """Verifica que las tablas necesarias existan"""
    try:
        db = SessionLocal()
        
        # Verificar tabla pedidos
        pedidos_count = db.query(Pedido).count()
        logger.info(f"Registros en tabla 'pedidos': {pedidos_count}")
        
        # Verificar tabla pedidos_compras
        try:
            pedidos_compras_count = db.query(PedidosCompras).count()
            logger.info(f"Registros en tabla 'pedidos_compras': {pedidos_compras_count}")
        except Exception as e:
            logger.error(f"Error accediendo a tabla 'pedidos_compras': {str(e)}")
            logger.info("La tabla 'pedidos_compras' puede no existir aun")
            return False, pedidos_count, 0
        
        db.close()
        return True, pedidos_count, pedidos_compras_count
        
    except Exception as e:
        logger.error(f"Error verificando tablas: {str(e)}")
        return False, 0, 0

def migrate_pedidos_data():
    """Migra datos de pedidos a pedidos_compras"""
    logger.info("Iniciando migracion de datos...")
    
    db = SessionLocal()
    
    try:
        # Obtener todos los pedidos existentes
        pedidos_existentes = db.query(Pedido).all()
        logger.info(f"Encontrados {len(pedidos_existentes)} pedidos para migrar")
        
        if not pedidos_existentes:
            logger.info("No hay pedidos para migrar")
            return True
        
        # Obtener información de facturación para enriquecer datos
        facturas = db.query(Facturacion).all()
        facturas_por_folio = {}
        
        for factura in facturas:
            if factura.folio_factura:
                folio_limpio = str(factura.folio_factura).strip()
                facturas_por_folio[folio_limpio] = factura
        
        logger.info(f"Encontradas {len(facturas)} facturas para enriquecer datos")
        
        # Contadores para estadísticas
        migrados_exitosos = 0
        migrados_con_errores = 0
        errores_detallados = []
        
        # Migrar cada pedido
        for i, pedido in enumerate(pedidos_existentes, 1):
            try:
                # Buscar factura relacionada
                factura_relacionada = None
                if pedido.folio_factura:
                    folio_limpio = str(pedido.folio_factura).strip()
                    factura_relacionada = facturas_por_folio.get(folio_limpio)
                
                # Calcular importe con IVA (asumiendo 16% de IVA)
                importe_con_iva = pedido.importe_sin_iva * 1.16 if pedido.importe_sin_iva else 0.0
                
                # Crear registro en pedidos_compras
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
                
                # Log de progreso cada 50 registros
                if i % 50 == 0:
                    logger.info(f"Progreso: {i}/{len(pedidos_existentes)} pedidos procesados...")
                
            except Exception as e:
                migrados_con_errores += 1
                error_msg = f"Error migrando pedido {pedido.id}: {str(e)}"
                logger.warning(f"WARNING: {error_msg}")
                errores_detallados.append(error_msg)
                continue
        
        # Confirmar cambios
        db.commit()
        
        # Estadísticas finales
        logger.info("Migracion completada!")
        logger.info(f"Pedidos migrados exitosamente: {migrados_exitosos}")
        logger.info(f"Pedidos con errores: {migrados_con_errores}")
        
        # Verificar migración
        total_pedidos_compras = db.query(PedidosCompras).count()
        logger.info(f"Total de registros en pedidos_compras: {total_pedidos_compras}")
        
        # Guardar errores detallados si los hay
        if errores_detallados:
            with open('migration_errors.log', 'w') as f:
                for error in errores_detallados:
                    f.write(f"{error}\n")
            logger.info(f"Errores detallados guardados en migration_errors.log")
        
        return migrados_exitosos > 0
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error critico en la migracion: {str(e)}")
        raise
    finally:
        db.close()

def verify_migration():
    """Verifica que la migración se completó correctamente"""
    logger.info("Verificando migracion...")
    
    db = SessionLocal()
    
    try:
        # Contar registros en ambas tablas
        total_pedidos = db.query(Pedido).count()
        total_pedidos_compras = db.query(PedidosCompras).count()
        
        logger.info(f"Registros en tabla 'pedidos': {total_pedidos}")
        logger.info(f"Registros en tabla 'pedidos_compras': {total_pedidos_compras}")
        
        # Verificar algunos registros específicos
        sample_pedidos = db.query(Pedido).limit(5).all()
        verificaciones_exitosas = 0
        
        for pedido in sample_pedidos:
            pedido_compras = db.query(PedidosCompras).filter(
                PedidosCompras.folio_factura == pedido.folio_factura,
                PedidosCompras.material_codigo == pedido.material
            ).first()
            
            if pedido_compras:
                logger.info(f"Verificado: Pedido {pedido.id} -> PedidosCompras {pedido_compras.id}")
                verificaciones_exitosas += 1
            else:
                logger.warning(f"No encontrado: Pedido {pedido.id} en pedidos_compras")
        
        logger.info(f"Verificaciones exitosas: {verificaciones_exitosas}/{len(sample_pedidos)}")
        
        return {
            'total_pedidos': total_pedidos,
            'total_pedidos_compras': total_pedidos_compras,
            'migration_successful': total_pedidos_compras > 0,
            'verification_rate': verificaciones_exitosas / len(sample_pedidos) if sample_pedidos else 0
        }
        
    except Exception as e:
        logger.error(f"Error en verificacion: {str(e)}")
        raise
    finally:
        db.close()

def main():
    """Función principal de migración"""
    print("INICIANDO MIGRACION DE DATOS")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Verificar conexión a base de datos
        if not check_database_connection():
            logger.error("No se puede continuar sin conexion a base de datos")
            return False
        
        # Verificar tablas
        tables_ok, pedidos_count, pedidos_compras_count = check_tables_exist()
        if not tables_ok:
            logger.error("No se puede continuar sin acceso a las tablas necesarias")
            return False
        
        # Si ya hay datos en pedidos_compras, preguntar si continuar
        if pedidos_compras_count > 0:
            logger.warning(f"Ya existen {pedidos_compras_count} registros en pedidos_compras")
            logger.info("La migracion continuara agregando nuevos registros")
        
        # Ejecutar migración
        migration_success = migrate_pedidos_data()
        
        if migration_success:
            # Verificar migración
            verification = verify_migration()
            
            # Resumen final
            print("\n" + "="*60)
            print("RESUMEN DE MIGRACION")
            print("="*60)
            print(f"Migracion exitosa: {verification['migration_successful']}")
            print(f"Registros en 'pedidos': {verification['total_pedidos']}")
            print(f"Registros en 'pedidos_compras': {verification['total_pedidos_compras']}")
            print(f"Tasa de verificacion: {verification['verification_rate']:.2%}")
            print("="*60)
            
            if verification['migration_successful']:
                logger.info("MIGRACION COMPLETADA EXITOSAMENTE!")
                return True
            else:
                logger.error("La migracion no fue exitosa")
                return False
        else:
            logger.error("La migracion fallo")
            return False
            
    except Exception as e:
        logger.error(f"Error critico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
