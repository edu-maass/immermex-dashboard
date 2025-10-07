"""
Script para agregar la columna fecha_vencimiento a la tabla compras_v2
Calcula la fecha de vencimiento sumando los días de crédito a la fecha real de salida o la estimada cuando no se tenga la real
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging

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
    """Obtiene conexión a Supabase usando las variables de entorno"""
    try:
        # Intentar usar variables de entorno directamente
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_PASSWORD")
        
        if supabase_url and supabase_password:
            # Construir URL PostgreSQL desde variables de Supabase
            if "supabase.co" in supabase_url:
                project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
                database_url = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
                logger.info(f"Usando variables de entorno para conectar a Supabase")
            else:
                logger.error("Formato de SUPABASE_URL no reconocido")
                return None
        else:
            # Fallback a archivo de configuración
            config = load_production_config()
            if not config:
                logger.error("No se encontró configuración de Supabase")
                return None
            
            database_url = config.get("DATABASE_URL")
            if not database_url:
                logger.error("DATABASE_URL no encontrada en la configuración")
                return None
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
        
        logger.info("Conexión a Supabase establecida exitosamente")
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def check_table_exists(conn, table_name):
    """Verifica si la tabla existe"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        
        exists = cursor.fetchone()['exists']
        cursor.close()
        return exists
        
    except Exception as e:
        logger.error(f"Error verificando existencia de tabla {table_name}: {str(e)}")
        return False

def check_column_exists(conn, table_name, column_name):
    """Verifica si la columna existe en la tabla"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s 
                AND column_name = %s
            )
        """, (table_name, column_name))
        
        exists = cursor.fetchone()['exists']
        cursor.close()
        return exists
        
    except Exception as e:
        logger.error(f"Error verificando existencia de columna {column_name}: {str(e)}")
        return False

def add_fecha_vencimiento_column(conn):
    """Agrega la columna fecha_vencimiento a la tabla compras_v2"""
    try:
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        if check_column_exists(conn, 'compras_v2', 'fecha_vencimiento'):
            logger.info("La columna fecha_vencimiento ya existe en la tabla compras_v2")
            cursor.close()
            return True
        
        # Agregar la columna
        logger.info("Agregando columna fecha_vencimiento a la tabla compras_v2...")
        cursor.execute("""
            ALTER TABLE compras_v2 
            ADD COLUMN fecha_vencimiento DATE
        """)
        
        conn.commit()
        logger.info("Columna fecha_vencimiento agregada exitosamente")
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error agregando columna fecha_vencimiento: {str(e)}")
        conn.rollback()
        return False

def calculate_fecha_vencimiento(conn):
    """Calcula y actualiza la fecha_vencimiento para todos los registros"""
    try:
        cursor = conn.cursor()
        
        # Obtener todos los registros que necesitan cálculo
        logger.info("Obteniendo registros para calcular fecha_vencimiento...")
        cursor.execute("""
            SELECT id, fecha_salida_real, fecha_salida_estimada, dias_credito
            FROM compras_v2
            WHERE dias_credito IS NOT NULL AND dias_credito > 0
            AND (fecha_salida_real IS NOT NULL OR fecha_salida_estimada IS NOT NULL)
        """)
        
        records = cursor.fetchall()
        logger.info(f"Encontrados {len(records)} registros para procesar")
        
        updated_count = 0
        
        for record in records:
            try:
                # Determinar qué fecha usar (prioridad: fecha_salida_real > fecha_salida_estimada)
                fecha_base = None
                if record['fecha_salida_real']:
                    fecha_base = record['fecha_salida_real']
                elif record['fecha_salida_estimada']:
                    fecha_base = record['fecha_salida_estimada']
                
                if fecha_base and record['dias_credito']:
                    # Calcular fecha de vencimiento
                    fecha_vencimiento = fecha_base + timedelta(days=record['dias_credito'])
                    
                    # Actualizar el registro
                    cursor.execute("""
                        UPDATE compras_v2 
                        SET fecha_vencimiento = %s
                        WHERE id = %s
                    """, (fecha_vencimiento, record['id']))
                    
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        logger.info(f"Progreso: {updated_count}/{len(records)} registros actualizados")
                        
            except Exception as e:
                logger.warning(f"Error procesando registro {record['id']}: {str(e)}")
                continue
        
        conn.commit()
        logger.info(f"Cálculo completado: {updated_count} registros actualizados")
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error calculando fecha_vencimiento: {str(e)}")
        conn.rollback()
        return False

def verify_results(conn):
    """Verifica los resultados del proceso"""
    try:
        cursor = conn.cursor()
        
        # Contar registros con fecha_vencimiento calculada
        cursor.execute("""
            SELECT COUNT(*) as total_con_fecha_vencimiento
            FROM compras_v2
            WHERE fecha_vencimiento IS NOT NULL
        """)
        
        result = cursor.fetchone()
        total_con_fecha = result['total_con_fecha_vencimiento']
        
        # Contar registros con días de crédito
        cursor.execute("""
            SELECT COUNT(*) as total_con_dias_credito
            FROM compras_v2
            WHERE dias_credito IS NOT NULL AND dias_credito > 0
        """)
        
        result = cursor.fetchone()
        total_con_dias = result['total_con_dias_credito']
        
        # Mostrar algunos ejemplos
        cursor.execute("""
            SELECT id, proveedor, fecha_salida_real, fecha_salida_estimada, 
                   dias_credito, fecha_vencimiento
            FROM compras_v2
            WHERE fecha_vencimiento IS NOT NULL
            ORDER BY id
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        
        logger.info("=== RESULTADOS DEL PROCESO ===")
        logger.info(f"Total registros con fecha_vencimiento calculada: {total_con_fecha}")
        logger.info(f"Total registros con días de crédito: {total_con_dias}")
        logger.info("\nEjemplos de registros actualizados:")
        
        for example in examples:
            fecha_usada = example['fecha_salida_real'] if example['fecha_salida_real'] else example['fecha_salida_estimada']
            logger.info(f"  ID: {example['id']}, Proveedor: {example['proveedor']}")
            logger.info(f"    Fecha base: {fecha_usada} ({'real' if example['fecha_salida_real'] else 'estimada'})")
            logger.info(f"    Días crédito: {example['dias_credito']}")
            logger.info(f"    Fecha vencimiento: {example['fecha_vencimiento']}")
            logger.info("")
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Error verificando resultados: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("AGREGANDO COLUMNA FECHA_VENCIMIENTO A COMPRAS_V2")
    logger.info("=" * 60)
    
    # Conectar a Supabase
    conn = get_supabase_connection()
    if not conn:
        logger.error("No se pudo conectar a Supabase")
        return False
    
    try:
        # Verificar que la tabla compras_v2 existe
        if not check_table_exists(conn, 'compras_v2'):
            logger.error("La tabla compras_v2 no existe")
            return False
        
        logger.info("Tabla compras_v2 encontrada")
        
        # Paso 1: Agregar la columna fecha_vencimiento
        logger.info("\nPaso 1: Agregando columna fecha_vencimiento...")
        if not add_fecha_vencimiento_column(conn):
            logger.error("Error agregando columna")
            return False
        
        # Paso 2: Calcular fecha_vencimiento para registros existentes
        logger.info("\nPaso 2: Calculando fecha_vencimiento para registros existentes...")
        if not calculate_fecha_vencimiento(conn):
            logger.error("Error calculando fecha_vencimiento")
            return False
        
        # Paso 3: Verificar resultados
        logger.info("\nPaso 3: Verificando resultados...")
        if not verify_results(conn):
            logger.error("Error verificando resultados")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("PROCESO COMPLETADO EXITOSAMENTE")
        logger.info("=" * 60)
        logger.info("La columna fecha_vencimiento ha sido agregada y calculada")
        logger.info("La fecha se calcula como: fecha_salida_real + dias_credito")
        logger.info("Si no hay fecha_salida_real, se usa fecha_salida_estimada + dias_credito")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en proceso principal: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()
            logger.info("Conexión cerrada")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

