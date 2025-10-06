"""
Script para actualizar compras_v2 con datos de proveedores
- Actualiza puerto_origen desde proveedores.pais_origen
- Calcula fecha_salida_estimada = fecha_pedido + promedio_dias_produccion
- Calcula fecha_arribo_estimada = fecha_salida_estimada + promedio_dias_transporte_maritimo
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
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

def get_proveedores_data():
    """Obtiene datos de proveedores para el cálculo de fechas"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                "Nombre",
                promedio_dias_produccion,
                promedio_dias_transporte_maritimo,
                "Puerto"
            FROM "Proveedores"
        """)
        
        proveedores = cursor.fetchall()
        
        # Convertir a diccionario para fácil acceso
        proveedores_dict = {}
        for p in proveedores:
            proveedores_dict[p['Nombre']] = {
                'promedio_dias_produccion': safe_float(p['promedio_dias_produccion'], 0.0),
                'promedio_dias_transporte_maritimo': safe_float(p['promedio_dias_transporte_maritimo'], 0.0),
                'puerto': p['Puerto'] or 'N/A'
            }
        
        logger.info(f"Obtenidos datos de {len(proveedores_dict)} proveedores activos")
        
        cursor.close()
        conn.close()
        
        return proveedores_dict
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de proveedores: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return None

def get_compras_v2_batch(offset=0, limit=50):
    """Obtiene un lote de compras_v2 para actualizar"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                imi,
                proveedor,
                fecha_pedido,
                puerto_origen
            FROM compras_v2
            WHERE imi > 0
            ORDER BY imi
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        compras_batch = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return compras_batch
        
    except Exception as e:
        logger.error(f"Error obteniendo lote de compras_v2: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return None

def update_single_compra(compra, proveedores_data):
    """Actualiza una sola compra con datos de proveedores"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        imi = compra['imi']
        proveedor = compra['proveedor']
        fecha_pedido = compra['fecha_pedido']
        
        # Obtener datos del proveedor
        if proveedor in proveedores_data:
            proveedor_data = proveedores_data[proveedor]
            promedio_dias_produccion = proveedor_data['promedio_dias_produccion']
            promedio_dias_transporte = proveedor_data['promedio_dias_transporte_maritimo']
            puerto_origen = proveedor_data['puerto']
        else:
            logger.warning(f"Proveedor '{proveedor}' no encontrado en tabla Proveedores")
            promedio_dias_produccion = 0.0
            promedio_dias_transporte = 0.0
            puerto_origen = 'N/A'
        
        # Calcular fechas estimadas
        fecha_salida_estimada = None
        fecha_arribo_estimada = None
        
        if fecha_pedido:
            # Siempre calcular fecha salida estimada (incluso si días producción = 0)
            fecha_salida_estimada = fecha_pedido + timedelta(days=promedio_dias_produccion)
            
            # Calcular fecha arribo estimada si hay días de transporte
            if promedio_dias_transporte >= 0:  # Incluir 0 días
                fecha_arribo_estimada = fecha_salida_estimada + timedelta(days=promedio_dias_transporte)
        
        # Actualizar registro
        cursor.execute("""
            UPDATE compras_v2 
            SET 
                puerto_origen = %s,
                fecha_salida_estimada = %s,
                fecha_arribo_estimada = %s,
                updated_at = %s
            WHERE imi = %s
        """, (
            puerto_origen,
            fecha_salida_estimada,
            fecha_arribo_estimada,
            datetime.utcnow(),
            imi
        ))
        
        # Confirmar cambios
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando compra IMI {compra['imi']}: {str(e)}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def update_compras_v2_with_proveedores():
    """Actualiza todas las compras_v2 con datos de proveedores"""
    
    # Obtener datos de proveedores
    proveedores_data = get_proveedores_data()
    if not proveedores_data:
        logger.error("No se pudieron obtener datos de proveedores")
        return False
    
    # Contadores
    compras_actualizadas = 0
    errores = 0
    offset = 0
    batch_size = 20  # Lotes pequeños para evitar problemas de conexión
    
    logger.info("Iniciando actualización de compras_v2 con datos de proveedores...")
    
    while True:
        # Obtener lote de compras
        compras_batch = get_compras_v2_batch(offset, batch_size)
        
        if not compras_batch:
            break
        
        logger.info(f"Procesando lote {offset//batch_size + 1}: {len(compras_batch)} compras")
        
        # Actualizar cada compra del lote
        for compra in compras_batch:
            try:
                success = update_single_compra(compra, proveedores_data)
                
                if success:
                    compras_actualizadas += 1
                else:
                    errores += 1
                
            except Exception as e:
                logger.warning(f"Error procesando compra IMI {compra['imi']}: {str(e)}")
                errores += 1
                continue
        
        offset += batch_size
        
        logger.info(f"Progreso: {compras_actualizadas} compras actualizadas")
    
    logger.info(f"Actualización completada:")
    logger.info(f"  - Compras actualizadas: {compras_actualizadas}")
    logger.info(f"  - Errores: {errores}")
    
    return compras_actualizadas > 0

def verify_updates():
    """Verifica que las actualizaciones se aplicaron correctamente"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar algunas compras actualizadas
        cursor.execute("""
            SELECT 
                c2.imi,
                c2.proveedor,
                c2.puerto_origen,
                c2.fecha_pedido,
                c2.fecha_salida_estimada,
                c2.fecha_arribo_estimada,
                p.promedio_dias_produccion,
                p.promedio_dias_transporte_maritimo
            FROM compras_v2 c2
            LEFT JOIN "Proveedores" p ON c2.proveedor = p."Nombre"
            WHERE c2.imi > 0
            ORDER BY c2.imi
            LIMIT 10
        """)
        
        verificaciones = cursor.fetchall()
        
        logger.info("Verificaciones de actualizaciones:")
        for v in verificaciones:
            logger.info(f"  IMI {v['imi']}: {v['proveedor']}")
            logger.info(f"    Puerto origen: {v['puerto_origen']}")
            logger.info(f"    Fecha pedido: {v['fecha_pedido']}")
            logger.info(f"    Fecha salida estimada: {v['fecha_salida_estimada']}")
            logger.info(f"    Fecha arribo estimada: {v['fecha_arribo_estimada']}")
            logger.info(f"    Días producción: {v['promedio_dias_produccion']}")
            logger.info(f"    Días transporte: {v['promedio_dias_transporte_maritimo']}")
            logger.info("")
        
        # Contar compras con fechas calculadas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_compras,
                COUNT(fecha_salida_estimada) as con_fecha_salida,
                COUNT(fecha_arribo_estimada) as con_fecha_arribo
            FROM compras_v2 
            WHERE imi > 0
        """)
        
        conteos = cursor.fetchone()
        
        logger.info(f"Conteos de actualizaciones:")
        logger.info(f"  - Total compras: {conteos['total_compras']}")
        logger.info(f"  - Con fecha salida estimada: {conteos['con_fecha_salida']}")
        logger.info(f"  - Con fecha arribo estimada: {conteos['con_fecha_arribo']}")
        
        cursor.close()
        conn.close()
        
        return {
            'total_compras': conteos['total_compras'],
            'con_fecha_salida': conteos['con_fecha_salida'],
            'con_fecha_arribo': conteos['con_fecha_arribo'],
            'update_successful': conteos['con_fecha_salida'] > 0
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
    print("ACTUALIZACION DE COMPRAS_V2 CON DATOS DE PROVEEDORES")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Ejecutar actualización
        logger.info("Iniciando actualización de compras_v2...")
        update_success = update_compras_v2_with_proveedores()
        
        if update_success:
            # Verificar actualizaciones
            verification = verify_updates()
            
            print("\n" + "="*60)
            print("RESUMEN DE ACTUALIZACION DE COMPRAS_V2")
            print("="*60)
            print(f"Actualización exitosa: {verification['update_successful']}")
            print(f"Total compras: {verification['total_compras']}")
            print(f"Con fecha salida estimada: {verification['con_fecha_salida']}")
            print(f"Con fecha arribo estimada: {verification['con_fecha_arribo']}")
            print("="*60)
            
            if verification['update_successful']:
                logger.info("ACTUALIZACION DE COMPRAS_V2 EXITOSA!")
                logger.info("Las fechas estimadas han sido calculadas correctamente")
                return True
            else:
                logger.error("La actualización no fue exitosa")
                return False
        else:
            logger.error("La actualización falló")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
