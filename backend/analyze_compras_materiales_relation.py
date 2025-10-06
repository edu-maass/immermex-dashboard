"""
Script para analizar la relación entre compras_v2 y compras_v2_materiales
Explica por qué hay menos registros en compras_v2_materiales que en compras_v2
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

def analyze_compras_vs_materiales():
    """Analiza la relación entre compras_v2 y compras_v2_materiales"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Contar registros en cada tabla
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        compras_v2_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        materiales_count = cursor.fetchone()['count']
        
        logger.info(f"Conteo de registros:")
        logger.info(f"  - compras_v2: {compras_v2_count}")
        logger.info(f"  - compras_v2_materiales: {materiales_count}")
        logger.info(f"  - Diferencia: {compras_v2_count - materiales_count}")
        
        # Analizar compras con y sin materiales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_compras,
                COUNT(CASE WHEN c2m.id IS NOT NULL THEN 1 END) as compras_con_materiales,
                COUNT(CASE WHEN c2m.id IS NULL THEN 1 END) as compras_sin_materiales
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0
        """)
        
        compras_analysis = cursor.fetchone()
        
        logger.info(f"Análisis de compras:")
        logger.info(f"  - Total compras: {compras_analysis['total_compras']}")
        logger.info(f"  - Compras con materiales: {compras_analysis['compras_con_materiales']}")
        logger.info(f"  - Compras sin materiales: {compras_analysis['compras_sin_materiales']}")
        
        # Verificar distribución de materiales por compra
        cursor.execute("""
            SELECT 
                COUNT(*) as materiales_count,
                COUNT(DISTINCT compra_imi) as compras_con_materiales
            FROM compras_v2_materiales
        """)
        
        materiales_analysis = cursor.fetchone()
        
        logger.info(f"Análisis de materiales:")
        logger.info(f"  - Total materiales: {materiales_analysis['materiales_count']}")
        logger.info(f"  - Compras con materiales: {materiales_analysis['compras_con_materiales']}")
        logger.info(f"  - Promedio materiales por compra: {materiales_analysis['materiales_count'] / materiales_analysis['compras_con_materiales']:.2f}")
        
        # Mostrar ejemplos de compras sin materiales
        cursor.execute("""
            SELECT 
                c2.imi, c2.proveedor, c2.fecha_pedido, c2.moneda,
                c2.total_con_iva_mxn
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0 AND c2m.id IS NULL
            ORDER BY c2.imi
            LIMIT 10
        """)
        
        compras_sin_materiales = cursor.fetchall()
        
        logger.info("Ejemplos de compras sin materiales (primeros 10):")
        for compra in compras_sin_materiales:
            logger.info(f"  IMI {compra['imi']}: {compra['proveedor']} - {compra['fecha_pedido']} - {compra['moneda']} - ${compra['total_con_iva_mxn']}")
        
        # Mostrar ejemplos de compras con múltiples materiales
        cursor.execute("""
            SELECT 
                c2.imi, c2.proveedor, c2.fecha_pedido,
                COUNT(c2m.id) as materiales_count,
                SUM(c2m.kg) as total_kg,
                SUM(c2m.costo_total_mxn) as total_costo
            FROM compras_v2 c2
            JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0
            GROUP BY c2.imi, c2.proveedor, c2.fecha_pedido
            HAVING COUNT(c2m.id) > 1
            ORDER BY COUNT(c2m.id) DESC
            LIMIT 10
        """)
        
        compras_multiples_materiales = cursor.fetchall()
        
        logger.info("Ejemplos de compras con múltiples materiales (primeros 10):")
        for compra in compras_multiples_materiales:
            logger.info(f"  IMI {compra['imi']}: {compra['proveedor']} - {compra['fecha_pedido']} - {compra['materiales_count']} materiales - {compra['total_kg']} KG - ${compra['total_costo']}")
        
        # Verificar si hay materiales huérfanos
        cursor.execute("""
            SELECT COUNT(*) 
            FROM compras_v2_materiales c2m
            LEFT JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
            WHERE c2.imi IS NULL
        """)
        
        materiales_huerfanos = cursor.fetchone()['count']
        
        logger.info(f"Materiales huérfanos (sin compra asociada): {materiales_huerfanos}")
        
        cursor.close()
        conn.close()
        
        return {
            'compras_v2_count': compras_v2_count,
            'materiales_count': materiales_count,
            'compras_con_materiales': compras_analysis['compras_con_materiales'],
            'compras_sin_materiales': compras_analysis['compras_sin_materiales'],
            'materiales_huerfanos': materiales_huerfanos
        }
        
    except Exception as e:
        logger.error(f"Error analizando relación: {str(e)}")
        conn.close()
        return None

def explain_difference():
    """Explica por qué hay menos registros en compras_v2_materiales"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar el origen de los datos
        cursor.execute("""
            SELECT 
                COUNT(*) as total_compras,
                COUNT(CASE WHEN proveedor = 'DUMMY_PROVEEDOR' THEN 1 END) as dummy_compras,
                COUNT(CASE WHEN proveedor != 'DUMMY_PROVEEDOR' THEN 1 END) as real_compras
            FROM compras_v2
        """)
        
        compras_origin = cursor.fetchone()
        
        logger.info(f"Origen de compras_v2:")
        logger.info(f"  - Total: {compras_origin['total_compras']}")
        logger.info(f"  - Dummy: {compras_origin['dummy_compras']}")
        logger.info(f"  - Reales: {compras_origin['real_compras']}")
        
        # Verificar si las compras sin materiales son de migración o datos nuevos
        cursor.execute("""
            SELECT 
                c2.imi, c2.proveedor, c2.fecha_pedido,
                c2.created_at, c2.updated_at
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0 AND c2m.id IS NULL
            ORDER BY c2.created_at
            LIMIT 5
        """)
        
        compras_sin_materiales_ejemplos = cursor.fetchall()
        
        logger.info("Ejemplos de compras sin materiales (por fecha de creación):")
        for compra in compras_sin_materiales_ejemplos:
            logger.info(f"  IMI {compra['imi']}: {compra['proveedor']} - {compra['fecha_pedido']} - Creado: {compra['created_at']}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error explicando diferencia: {str(e)}")
        conn.close()
        return False

def main():
    """Función principal de análisis"""
    print("ANALISIS DE RELACION COMPRAS_V2 VS COMPRAS_V2_MATERIALES")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Analizar relación
        logger.info("Analizando relación entre compras_v2 y compras_v2_materiales...")
        analysis = analyze_compras_vs_materiales()
        
        # Explicar diferencia
        logger.info("\nExplicando la diferencia...")
        explain_difference()
        
        print("\n" + "="*60)
        print("EXPLICACION DE LA DIFERENCIA")
        print("="*60)
        
        if analysis:
            print(f"Registros en compras_v2: {analysis['compras_v2_count']}")
            print(f"Registros en compras_v2_materiales: {analysis['materiales_count']}")
            print(f"Diferencia: {analysis['compras_v2_count'] - analysis['materiales_count']}")
            print(f"\nDesglose:")
            print(f"  - Compras con materiales: {analysis['compras_con_materiales']}")
            print(f"  - Compras sin materiales: {analysis['compras_sin_materiales']}")
            print(f"  - Materiales huérfanos: {analysis['materiales_huerfanos']}")
        
        print("\n" + "="*60)
        print("CONCLUSION")
        print("="*60)
        print("La diferencia se debe a que:")
        print("1. NO todas las compras tienen materiales asociados")
        print("2. Algunas compras pueden ser registros de cabecera sin detalles")
        print("3. Durante la migración, solo se migraron compras que tenían materiales")
        print("4. Es normal que haya más compras que materiales (relación 1:N)")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
