"""
Script para investigar la inconsistencia en los datos
Analiza por qué hay más registros en compras_v2_materiales que en pedidos_compras
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

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

def analyze_data_inconsistency():
    """Analiza la inconsistencia en los datos"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Contar registros en cada tabla
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        compras_v2_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM pedidos_compras")
        pedidos_compras_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        materiales_count = cursor.fetchone()['count']
        
        logger.info(f"Conteo actual de registros:")
        logger.info(f"  - compras_v2: {compras_v2_count}")
        logger.info(f"  - pedidos_compras: {pedidos_compras_count}")
        logger.info(f"  - compras_v2_materiales: {materiales_count}")
        
        # Analizar el origen de los materiales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_materiales,
                COUNT(DISTINCT compra_imi) as compras_con_materiales,
                MIN(compra_imi) as min_imi,
                MAX(compra_imi) as max_imi
            FROM compras_v2_materiales
        """)
        
        materiales_info = cursor.fetchone()
        
        logger.info(f"Análisis de compras_v2_materiales:")
        logger.info(f"  - Total materiales: {materiales_info['total_materiales']}")
        logger.info(f"  - Compras con materiales: {materiales_info['compras_con_materiales']}")
        logger.info(f"  - Rango de IMI: {materiales_info['min_imi']} a {materiales_info['max_imi']}")
        
        # Verificar si los materiales tienen compras asociadas
        cursor.execute("""
            SELECT 
                c2m.compra_imi,
                COUNT(c2m.id) as materiales_count,
                c2.proveedor,
                c2.fecha_pedido
            FROM compras_v2_materiales c2m
            LEFT JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
            GROUP BY c2m.compra_imi, c2.proveedor, c2.fecha_pedido
            ORDER BY c2m.compra_imi
            LIMIT 10
        """)
        
        materiales_con_compras = cursor.fetchall()
        
        logger.info("Materiales con sus compras asociadas (primeros 10):")
        for mat in materiales_con_compras:
            proveedor = mat['proveedor'] if mat['proveedor'] else 'SIN COMPRA'
            fecha = mat['fecha_pedido'] if mat['fecha_pedido'] else 'SIN FECHA'
            logger.info(f"  IMI {mat['compra_imi']}: {mat['materiales_count']} materiales - {proveedor} - {fecha}")
        
        # Verificar materiales sin compra asociada
        cursor.execute("""
            SELECT COUNT(*) 
            FROM compras_v2_materiales c2m
            LEFT JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
            WHERE c2.imi IS NULL
        """)
        
        materiales_sin_compra = cursor.fetchone()['count']
        
        logger.info(f"Materiales sin compra asociada: {materiales_sin_compra}")
        
        # Verificar el estado de pedidos_compras
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN compra_imi > 0 THEN 1 END) as con_compra_imi,
                COUNT(CASE WHEN compra_imi = 0 THEN 1 END) as con_compra_imi_cero,
                COUNT(CASE WHEN compra_imi IS NULL THEN 1 END) as sin_compra_imi
            FROM pedidos_compras
        """)
        
        pedidos_info = cursor.fetchone()
        
        logger.info(f"Análisis de pedidos_compras:")
        logger.info(f"  - Total: {pedidos_info['total']}")
        logger.info(f"  - Con compra_imi > 0: {pedidos_info['con_compra_imi']}")
        logger.info(f"  - Con compra_imi = 0: {pedidos_info['con_compra_imi_cero']}")
        logger.info(f"  - Sin compra_imi: {pedidos_info['sin_compra_imi']}")
        
        cursor.close()
        conn.close()
        
        return {
            'compras_v2_count': compras_v2_count,
            'pedidos_compras_count': pedidos_compras_count,
            'materiales_count': materiales_count,
            'materiales_sin_compra': materiales_sin_compra,
            'materiales_con_compras': len(materiales_con_compras)
        }
        
    except Exception as e:
        logger.error(f"Error analizando inconsistencia: {str(e)}")
        conn.close()
        return None

def check_migration_status():
    """Verifica el estado de las migraciones"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar si hay datos en la tabla original de pedidos
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos_original_count = cursor.fetchone()['count']
        
        # Verificar si hay datos en la tabla original de compras
        cursor.execute("SELECT COUNT(*) FROM compras")
        compras_original_count = cursor.fetchone()['count']
        
        logger.info(f"Estado de tablas originales:")
        logger.info(f"  - pedidos (original): {pedidos_original_count}")
        logger.info(f"  - compras (original): {compras_original_count}")
        
        # Verificar si los datos de pedidos_compras fueron eliminados por error
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pedidos_compras 
            WHERE compra_imi > 0
        """)
        
        pedidos_validos = cursor.fetchone()['count']
        
        logger.info(f"Pedidos válidos (con compra_imi > 0): {pedidos_validos}")
        
        cursor.close()
        conn.close()
        
        return {
            'pedidos_original_count': pedidos_original_count,
            'compras_original_count': compras_original_count,
            'pedidos_validos': pedidos_validos
        }
        
    except Exception as e:
        logger.error(f"Error verificando estado de migración: {str(e)}")
        conn.close()
        return None

def main():
    """Función principal de análisis"""
    print("ANALISIS DE INCONSISTENCIA EN DATOS")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Analizar inconsistencia
        logger.info("Analizando inconsistencia en los datos...")
        inconsistency_data = analyze_data_inconsistency()
        
        # Verificar estado de migración
        logger.info("\nVerificando estado de migración...")
        migration_status = check_migration_status()
        
        print("\n" + "="*60)
        print("ANALISIS COMPLETO")
        print("="*60)
        
        if inconsistency_data:
            print(f"Registros actuales:")
            print(f"  - compras_v2: {inconsistency_data['compras_v2_count']}")
            print(f"  - pedidos_compras: {inconsistency_data['pedidos_compras_count']}")
            print(f"  - compras_v2_materiales: {inconsistency_data['materiales_count']}")
            print(f"  - Materiales sin compra: {inconsistency_data['materiales_sin_compra']}")
        
        if migration_status:
            print(f"\nEstado de migración:")
            print(f"  - pedidos (original): {migration_status['pedidos_original_count']}")
            print(f"  - compras (original): {migration_status['compras_original_count']}")
            print(f"  - pedidos válidos: {migration_status['pedidos_validos']}")
        
        print("="*60)
        
        # Conclusiones
        if inconsistency_data and migration_status:
            if inconsistency_data['pedidos_compras_count'] == 0 and migration_status['pedidos_original_count'] > 0:
                print("\nPROBLEMA IDENTIFICADO:")
                print("Los datos de pedidos_compras fueron eliminados incorrectamente.")
                print("La limpieza eliminó TODOS los pedidos, no solo los dummy.")
                print("\nSOLUCION:")
                print("Necesitamos restaurar los datos de pedidos_compras desde la tabla original 'pedidos'.")
            elif inconsistency_data['materiales_sin_compra'] > 0:
                print("\nPROBLEMA IDENTIFICADO:")
                print("Hay materiales sin compra asociada.")
                print("Esto indica datos huérfanos que necesitan limpieza.")
            else:
                print("\nESTADO:")
                print("Los datos parecen estar en orden.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
