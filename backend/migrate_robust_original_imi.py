"""
Script robusto para migrar compras manteniendo los IMI originales
Maneja mejor las conexiones SSL y usa transacciones más pequeñas
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from decimal import Decimal
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_production_config():
    """Carga la configuración desde production.env"""
    env_file = "production.env"
    
    if not os.path.exists(env_file):
        logger.error(f"Archivo {env_file} no encontrado")
        return None
    
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value
    
    return config

def get_supabase_connection():
    """Obtiene conexión a Supabase usando la configuración de production.env"""
    try:
        config = load_production_config()
        if not config:
            return None
        
        database_url = config.get("DATABASE_URL")
        
        if not database_url:
            logger.error("DATABASE_URL no encontrada en production.env")
            return None
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode='require',
            connect_timeout=30,
            keepalives_idle=600,
            keepalives_interval=30,
            keepalives_count=3
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def clean_all_tables():
    """Elimina todos los registros de las tablas de compras"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Contar registros antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM compras_v2")
        compras_v2_before = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        materiales_before = cursor.fetchone()['count']
        
        logger.info(f"Registros antes de limpiar:")
        logger.info(f"  - compras_v2: {compras_v2_before}")
        logger.info(f"  - compras_v2_materiales: {materiales_before}")
        
        # Eliminar materiales primero (por restricciones de clave foránea)
        cursor.execute("DELETE FROM compras_v2_materiales")
        materiales_eliminados = cursor.rowcount
        
        # Eliminar compras
        cursor.execute("DELETE FROM compras_v2")
        compras_eliminadas = cursor.rowcount
        
        # Confirmar cambios
        conn.commit()
        
        logger.info(f"Limpieza completada:")
        logger.info(f"  - Materiales eliminados: {materiales_eliminados}")
        logger.info(f"  - Compras eliminadas: {compras_eliminadas}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error limpiando tablas: {str(e)}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def safe_decimal(value, default=0.0):
    """Convierte un valor a Decimal de forma segura"""
    if value is None:
        return Decimal(str(default))
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except:
        return Decimal(str(default))

def safe_float(value, default=0.0):
    """Convierte un valor a float de forma segura"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except:
        return default

def get_compras_batch(offset=0, limit=50):
    """Obtiene un lote de compras para migrar"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Obtener compras agrupadas por número de factura manteniendo IMI original
        cursor.execute("""
            SELECT 
                numero_factura,
                proveedor,
                fecha_compra,
                moneda,
                tipo_cambio,
                dias_credito,
                puerto_origen,
                fecha_salida_puerto,
                fecha_arribo_puerto,
                fecha_entrada_inmermex,
                financiera,
                porcentaje_anticipo,
                fecha_anticipo,
                anticipo_dlls,
                tipo_cambio_anticipo,
                pago_factura_dlls,
                tipo_cambio_factura,
                porcentaje_imi,
                fecha_entrada_aduana,
                pedimento,
                gastos_aduanales,
                costo_total,
                porcentaje_gastos_aduanales,
                fecha_pago_impuestos,
                fecha_salida_aduana,
                dias_en_puerto,
                agente,
                fac_agente,
                archivo_id,
                created_at,
                updated_at,
                COUNT(*) as materiales_count,
                SUM(cantidad) as total_cantidad,
                SUM(subtotal) as total_subtotal,
                SUM(iva) as total_iva,
                SUM(total) as total_total,
                MIN(id) as imi_original
            FROM compras
            WHERE numero_factura IS NOT NULL AND numero_factura != ''
            GROUP BY 
                numero_factura, proveedor, fecha_compra, moneda, tipo_cambio,
                dias_credito, puerto_origen, fecha_salida_puerto, fecha_arribo_puerto,
                fecha_entrada_inmermex, financiera, porcentaje_anticipo, fecha_anticipo,
                anticipo_dlls, tipo_cambio_anticipo, pago_factura_dlls, tipo_cambio_factura,
                porcentaje_imi, fecha_entrada_aduana, pedimento, gastos_aduanales,
                costo_total, porcentaje_gastos_aduanales, fecha_pago_impuestos,
                fecha_salida_aduana, dias_en_puerto, agente, fac_agente,
                archivo_id, created_at, updated_at
            ORDER BY numero_factura
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        compras_batch = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return compras_batch
        
    except Exception as e:
        logger.error(f"Error obteniendo lote de compras: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return None

def get_materiales_by_factura(numero_factura):
    """Obtiene todos los materiales de una factura específica"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                concepto as material_codigo,
                cantidad as kg,
                precio_unitario as pu_divisa,
                subtotal,
                iva,
                total,
                pu_mxn,
                precio_dlls,
                xr
            FROM compras
            WHERE numero_factura = %s
            ORDER BY concepto
        """, (numero_factura,))
        
        materiales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return materiales
        
    except Exception as e:
        logger.error(f"Error obteniendo materiales para factura {numero_factura}: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return None

def migrate_single_compra(compra):
    """Migra una sola compra y sus materiales"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Usar IMI original
        imi_original = compra['imi_original']
        
        # Convertir valores a tipos seguros
        tipo_cambio = safe_float(compra['tipo_cambio'], 1.0)
        dias_credito = int(compra['dias_credito'] or 30)
        porcentaje_anticipo = safe_float(compra['porcentaje_anticipo'], 0.0)
        anticipo_monto = safe_float(compra['anticipo_dlls'], 0.0)
        gastos_aduanales = safe_float(compra['gastos_aduanales'], 0.0)
        porcentaje_gastos = safe_float(compra['porcentaje_gastos_aduanales'], 0.0)
        total_iva = safe_float(compra['total_iva'], 0.0)
        total_total = safe_float(compra['total_total'], 0.0)
        
        # Crear registro en compras_v2 usando IMI original
        cursor.execute("""
            INSERT INTO compras_v2 (
                imi, proveedor, fecha_pedido, puerto_origen,
                fecha_salida_estimada, fecha_salida_real,
                fecha_arribo_estimada, fecha_arribo_real,
                fecha_planta_estimada, fecha_planta_real,
                moneda, dias_credito, anticipo_pct, anticipo_monto,
                fecha_anticipo, fecha_pago_factura,
                tipo_cambio_estimado, tipo_cambio_real,
                gastos_importacion_divisa, gastos_importacion_mxn,
                porcentaje_gastos_importacion, iva_monto_divisa,
                iva_monto_mxn, total_con_iva_divisa, total_con_iva_mxn,
                created_at, updated_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            imi_original,  # imi original
            compra['proveedor'],  # proveedor
            compra['fecha_compra'],  # fecha_pedido
            compra['puerto_origen'],  # puerto_origen
            compra['fecha_salida_puerto'],  # fecha_salida_estimada
            None,  # fecha_salida_real
            compra['fecha_arribo_puerto'],  # fecha_arribo_estimada
            None,  # fecha_arribo_real
            compra['fecha_entrada_inmermex'],  # fecha_planta_estimada
            None,  # fecha_planta_real
            compra['moneda'] or 'USD',  # moneda
            dias_credito,  # dias_credito
            porcentaje_anticipo,  # anticipo_pct
            anticipo_monto,  # anticipo_monto
            compra['fecha_anticipo'],  # fecha_anticipo
            compra['pago_factura_dlls'],  # fecha_pago_factura
            tipo_cambio,  # tipo_cambio_estimado
            safe_float(compra['tipo_cambio_factura']),  # tipo_cambio_real
            gastos_aduanales,  # gastos_importacion_divisa
            gastos_aduanales * tipo_cambio,  # gastos_importacion_mxn
            porcentaje_gastos,  # porcentaje_gastos_importacion
            total_iva,  # iva_monto_divisa
            total_iva * tipo_cambio,  # iva_monto_mxn
            total_total,  # total_con_iva_divisa
            total_total * tipo_cambio,  # total_con_iva_mxn
            compra['created_at'],  # created_at
            compra['updated_at']  # updated_at
        ))
        
        # Obtener materiales de esta factura
        materiales = get_materiales_by_factura(compra['numero_factura'])
        
        materiales_migrados = 0
        
        if materiales:
            # Migrar materiales a compras_v2_materiales usando IMI original
            for material in materiales:
                try:
                    # Convertir valores a tipos seguros
                    kg = safe_float(material['kg'], 0.0)
                    pu_divisa = safe_float(material['pu_divisa'], 0.0)
                    pu_mxn = safe_float(material['pu_mxn'], pu_divisa * tipo_cambio)
                    costo_total_divisa = safe_float(material['subtotal'], 0.0)
                    costo_total_mxn = safe_float(material['total'], costo_total_divisa * tipo_cambio)
                    iva = safe_float(material['iva'], 0.0)
                    
                    # Calcular valores con importación
                    pu_mxn_importacion = pu_mxn * (1 + porcentaje_gastos)
                    costo_total_mxn_importacion = costo_total_mxn * (1 + porcentaje_gastos)
                    costo_total_con_iva = costo_total_mxn_importacion + iva
                    
                    cursor.execute("""
                        INSERT INTO compras_v2_materiales (
                            compra_id, material_codigo, kg, pu_divisa, pu_mxn,
                            costo_total_divisa, costo_total_mxn, pu_mxn_importacion,
                            costo_total_mxn_imporacion, iva, costo_total_con_iva,
                            compra_imi, created_at, updated_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        imi_original,  # compra_id usando IMI original
                        material['material_codigo'],  # material_codigo
                        kg,  # kg
                        pu_divisa,  # pu_divisa
                        pu_mxn,  # pu_mxn
                        costo_total_divisa,  # costo_total_divisa
                        costo_total_mxn,  # costo_total_mxn
                        pu_mxn_importacion,  # pu_mxn_importacion
                        costo_total_mxn_importacion,  # costo_total_mxn_imporacion
                        iva,  # iva
                        costo_total_con_iva,  # costo_total_con_iva
                        imi_original,  # compra_imi usando IMI original
                        compra['created_at'],  # created_at
                        compra['updated_at']  # updated_at
                    ))
                    
                    materiales_migrados += 1
                    
                except Exception as e:
                    logger.warning(f"Error migrando material {material['material_codigo']}: {str(e)}")
                    continue
        
        # Confirmar cambios
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True, materiales_migrados
        
    except Exception as e:
        logger.error(f"Error migrando compra {compra['numero_factura']}: {str(e)}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False, 0

def migrate_compras_robust():
    """Migra datos de compras usando lotes pequeños para evitar problemas de conexión"""
    
    # Contadores
    compras_v2_migradas = 0
    materiales_migrados = 0
    errores = 0
    offset = 0
    batch_size = 10  # Lotes más pequeños
    
    logger.info("Iniciando migración robusta con lotes pequeños...")
    
    while True:
        # Obtener lote de compras
        compras_batch = get_compras_batch(offset, batch_size)
        
        if not compras_batch:
            break
        
        logger.info(f"Procesando lote {offset//batch_size + 1}: {len(compras_batch)} compras")
        
        # Migrar cada compra del lote
        for compra in compras_batch:
            try:
                success, materiales_count = migrate_single_compra(compra)
                
                if success:
                    compras_v2_migradas += 1
                    materiales_migrados += materiales_count
                else:
                    errores += 1
                
                # Pequeña pausa para evitar sobrecarga
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error procesando compra {compra['numero_factura']}: {str(e)}")
                errores += 1
                continue
        
        offset += batch_size
        
        # Pausa entre lotes
        time.sleep(1)
        
        logger.info(f"Progreso: {compras_v2_migradas} compras migradas, {materiales_migrados} materiales")
    
    logger.info(f"Migración completada:")
    logger.info(f"  - Compras migradas a compras_v2: {compras_v2_migradas}")
    logger.info(f"  - Materiales migrados: {materiales_migrados}")
    logger.info(f"  - Errores: {errores}")
    
    return compras_v2_migradas > 0

def verify_migration_with_original_imi():
    """Verifica que la migración con IMI original se completó correctamente"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Contar registros en todas las tablas
        cursor.execute("SELECT COUNT(*) FROM compras")
        total_compras = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        total_compras_v2 = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        total_materiales = cursor.fetchone()['count']
        
        logger.info(f"Verificación de migración con IMI original:")
        logger.info(f"  - Registros en 'compras': {total_compras}")
        logger.info(f"  - Registros en 'compras_v2': {total_compras_v2}")
        logger.info(f"  - Registros en 'compras_v2_materiales': {total_materiales}")
        
        # Verificar rango de IMI
        cursor.execute("""
            SELECT 
                MIN(imi) as min_imi,
                MAX(imi) as max_imi,
                COUNT(DISTINCT imi) as imi_unicos
            FROM compras_v2 
            WHERE imi > 0
        """)
        
        imi_info = cursor.fetchone()
        
        logger.info(f"Rango de IMI en compras_v2:")
        logger.info(f"  - IMI mínimo: {imi_info['min_imi']}")
        logger.info(f"  - IMI máximo: {imi_info['max_imi']}")
        logger.info(f"  - IMI únicos: {imi_info['imi_unicos']}")
        
        # Verificar algunas relaciones
        cursor.execute("""
            SELECT 
                c2.imi, c2.proveedor, c2.fecha_pedido,
                COUNT(c2m.id) as materiales_count
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0
            GROUP BY c2.imi, c2.proveedor, c2.fecha_pedido
            ORDER BY c2.imi
            LIMIT 5
        """)
        
        verificaciones = cursor.fetchall()
        logger.info("Verificaciones de relaciones:")
        for v in verificaciones:
            logger.info(f"  IMI {v['imi']}: {v['proveedor']} - {v['materiales_count']} materiales")
        
        cursor.close()
        conn.close()
        
        return {
            'total_compras': total_compras,
            'total_compras_v2': total_compras_v2,
            'total_materiales': total_materiales,
            'min_imi': imi_info['min_imi'],
            'max_imi': imi_info['max_imi'],
            'migration_successful': total_compras_v2 > 0 and total_materiales > 0
        }
        
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return False

def main():
    """Función principal"""
    print("MIGRACION ROBUSTA CON IMI ORIGINALES")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Limpiar tablas
        logger.info("Limpiando tablas existentes...")
        cleanup_success = clean_all_tables()
        
        if not cleanup_success:
            logger.error("Error limpiando tablas")
            return False
        
        # Ejecutar migración robusta con IMI originales
        logger.info("Iniciando migración robusta con IMI originales...")
        migration_success = migrate_compras_robust()
        
        if migration_success:
            # Verificar migración
            verification = verify_migration_with_original_imi()
            
            print("\n" + "="*60)
            print("RESUMEN DE MIGRACION ROBUSTA CON IMI ORIGINALES")
            print("="*60)
            print(f"Migración exitosa: {verification['migration_successful']}")
            print(f"Registros en 'compras': {verification['total_compras']}")
            print(f"Registros en 'compras_v2': {verification['total_compras_v2']}")
            print(f"Registros en 'compras_v2_materiales': {verification['total_materiales']}")
            print(f"Rango de IMI: {verification['min_imi']} - {verification['max_imi']}")
            print("="*60)
            
            if verification['migration_successful']:
                logger.info("MIGRACION ROBUSTA CON IMI ORIGINALES EXITOSA!")
                logger.info("Los IMI originales han sido preservados correctamente")
                return True
            else:
                logger.error("La migración no fue exitosa")
                return False
        else:
            logger.error("La migración falló")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
