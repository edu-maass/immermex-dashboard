"""
Script de migración de datos de tabla 'compras' a 'compras_v2' y 'compras_v2_materiales'
Mantiene la lógica y relaciones correctas entre las tablas
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from decimal import Decimal

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
            sslmode='require'
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def get_next_imi():
    """Obtiene el siguiente número IMI disponible"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Obtener el máximo IMI actual
        cursor.execute("SELECT MAX(imi) FROM compras_v2 WHERE imi > 0")
        max_imi = cursor.fetchone()['max']
        
        next_imi = (max_imi or 0) + 1
        
        cursor.close()
        conn.close()
        
        return next_imi
        
    except Exception as e:
        logger.error(f"Error obteniendo siguiente IMI: {str(e)}")
        conn.close()
        return None

def group_compras_by_factura():
    """Agrupa las compras por número de factura para crear registros únicos en compras_v2"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Obtener compras agrupadas por número de factura
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
                SUM(total) as total_total
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
        """)
        
        grouped_compras = cursor.fetchall()
        
        logger.info(f"Encontradas {len(grouped_compras)} facturas únicas para migrar")
        
        cursor.close()
        conn.close()
        
        return grouped_compras
        
    except Exception as e:
        logger.error(f"Error agrupando compras: {str(e)}")
        conn.close()
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
        conn.close()
        return None

def migrate_compras_to_compras_v2():
    """Migra datos de compras a compras_v2 y compras_v2_materiales"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Obtener compras agrupadas por factura
        grouped_compras = group_compras_by_factura()
        
        if not grouped_compras:
            logger.info("No hay compras para migrar")
            return True
        
        # Obtener siguiente IMI
        next_imi = get_next_imi()
        if not next_imi:
            logger.error("No se pudo obtener siguiente IMI")
            return False
        
        logger.info(f"Iniciando migración con IMI {next_imi}")
        
        # Contadores
        compras_v2_migradas = 0
        materiales_migrados = 0
        errores = 0
        
        # Migrar cada factura
        for compra in grouped_compras:
            try:
                # Crear registro en compras_v2
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
                    next_imi,  # imi
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
                    compra['dias_credito'] or 30,  # dias_credito
                    compra['porcentaje_anticipo'] or 0.0,  # anticipo_pct
                    compra['anticipo_dlls'] or 0.0,  # anticipo_monto
                    compra['fecha_anticipo'],  # fecha_anticipo
                    compra['pago_factura_dlls'],  # fecha_pago_factura
                    compra['tipo_cambio'] or 1.0,  # tipo_cambio_estimado
                    compra['tipo_cambio_factura'],  # tipo_cambio_real
                    compra['gastos_aduanales'] or 0.0,  # gastos_importacion_divisa
                    (compra['gastos_aduanales'] or 0.0) * (compra['tipo_cambio'] or 1.0),  # gastos_importacion_mxn
                    compra['porcentaje_gastos_aduanales'] or 0.0,  # porcentaje_gastos_importacion
                    compra['total_iva'] or 0.0,  # iva_monto_divisa
                    (compra['total_iva'] or 0.0) * (compra['tipo_cambio'] or 1.0),  # iva_monto_mxn
                    compra['total_total'] or 0.0,  # total_con_iva_divisa
                    (compra['total_total'] or 0.0) * (compra['tipo_cambio'] or 1.0),  # total_con_iva_mxn
                    compra['created_at'],  # created_at
                    compra['updated_at']  # updated_at
                ))
                
                compras_v2_migradas += 1
                
                # Obtener materiales de esta factura
                materiales = get_materiales_by_factura(compra['numero_factura'])
                
                if materiales:
                    # Migrar materiales a compras_v2_materiales
                    for material in materiales:
                        try:
                            # Calcular valores
                            pu_mxn = material['pu_mxn'] or (material['pu_divisa'] * (compra['tipo_cambio'] or 1.0))
                            costo_total_divisa = material['subtotal'] or 0.0
                            costo_total_mxn = material['total'] or (costo_total_divisa * (compra['tipo_cambio'] or 1.0))
                            
                            # Calcular valores con importación
                            pu_mxn_importacion = pu_mxn * (1 + (compra['porcentaje_gastos_aduanales'] or 0.0))
                            costo_total_mxn_importacion = costo_total_mxn * (1 + (compra['porcentaje_gastos_aduanales'] or 0.0))
                            
                            # Calcular IVA
                            iva = material['iva'] or 0.0
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
                                next_imi,  # compra_id (usando IMI como ID)
                                material['material_codigo'],  # material_codigo
                                material['kg'],  # kg
                                material['pu_divisa'],  # pu_divisa
                                pu_mxn,  # pu_mxn
                                costo_total_divisa,  # costo_total_divisa
                                costo_total_mxn,  # costo_total_mxn
                                pu_mxn_importacion,  # pu_mxn_importacion
                                costo_total_mxn_importacion,  # costo_total_mxn_imporacion
                                iva,  # iva
                                costo_total_con_iva,  # costo_total_con_iva
                                next_imi,  # compra_imi
                                compra['created_at'],  # created_at
                                compra['updated_at']  # updated_at
                            ))
                            
                            materiales_migrados += 1
                            
                        except Exception as e:
                            logger.warning(f"Error migrando material {material['material_codigo']}: {str(e)}")
                            errores += 1
                            continue
                
                next_imi += 1
                
                if compras_v2_migradas % 50 == 0:
                    logger.info(f"Progreso: {compras_v2_migradas} compras migradas...")
                
            except Exception as e:
                logger.warning(f"Error migrando compra {compra['numero_factura']}: {str(e)}")
                errores += 1
                continue
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar migración
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        total_compras_v2 = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        total_materiales = cursor.fetchone()['count']
        
        logger.info(f"Migración completada:")
        logger.info(f"  - Compras migradas a compras_v2: {compras_v2_migradas}")
        logger.info(f"  - Materiales migrados: {materiales_migrados}")
        logger.info(f"  - Errores: {errores}")
        logger.info(f"  - Total en compras_v2: {total_compras_v2}")
        logger.info(f"  - Total en compras_v2_materiales: {total_materiales}")
        
        cursor.close()
        conn.close()
        
        return compras_v2_migradas > 0
        
    except Exception as e:
        logger.error(f"Error en migración: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def verify_migration():
    """Verifica que la migración se completó correctamente"""
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
        
        logger.info(f"Verificación de migración:")
        logger.info(f"  - Registros en 'compras': {total_compras}")
        logger.info(f"  - Registros en 'compras_v2': {total_compras_v2}")
        logger.info(f"  - Registros en 'compras_v2_materiales': {total_materiales}")
        
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
            'migration_successful': total_compras_v2 > 0 and total_materiales > 0
        }
        
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        conn.close()
        return False

def main():
    """Función principal"""
    print("MIGRACION DE COMPRAS A COMPRAS_V2 Y COMPRAS_V2_MATERIALES")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Ejecutar migración
        logger.info("Iniciando migración de compras...")
        migration_success = migrate_compras_to_compras_v2()
        
        if migration_success:
            # Verificar migración
            verification = verify_migration()
            
            print("\n" + "="*60)
            print("RESUMEN DE MIGRACION")
            print("="*60)
            print(f"Migración exitosa: {verification['migration_successful']}")
            print(f"Registros en 'compras': {verification['total_compras']}")
            print(f"Registros en 'compras_v2': {verification['total_compras_v2']}")
            print(f"Registros en 'compras_v2_materiales': {verification['total_materiales']}")
            print("="*60)
            
            if verification['migration_successful']:
                logger.info("MIGRACION COMPLETADA EXITOSAMENTE!")
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
