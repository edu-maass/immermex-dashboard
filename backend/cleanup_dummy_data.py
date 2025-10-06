"""
Script para limpiar datos dummy de las migraciones
Elimina registros dummy creados durante las migraciones de pedidos y compras
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

def check_dummy_data():
    """Verifica qué datos dummy existen en las tablas"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar datos dummy en compras_v2
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM compras_v2 
            WHERE proveedor = 'DUMMY_PROVEEDOR' OR puerto_origen = 'DUMMY_PUERTO'
        """)
        compras_dummy = cursor.fetchone()['count']
        
        # Verificar datos dummy en pedidos_compras
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM pedidos_compras 
            WHERE compra_imi = 0
        """)
        pedidos_dummy = cursor.fetchone()['count']
        
        # Verificar datos dummy en compras_v2_materiales
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM compras_v2_materiales 
            WHERE compra_imi = 0
        """)
        materiales_dummy = cursor.fetchone()['count']
        
        logger.info(f"Datos dummy encontrados:")
        logger.info(f"  - compras_v2: {compras_dummy} registros")
        logger.info(f"  - pedidos_compras: {pedidos_dummy} registros")
        logger.info(f"  - compras_v2_materiales: {materiales_dummy} registros")
        
        cursor.close()
        conn.close()
        
        return {
            'compras_dummy': compras_dummy,
            'pedidos_dummy': pedidos_dummy,
            'materiales_dummy': materiales_dummy
        }
        
    except Exception as e:
        logger.error(f"Error verificando datos dummy: {str(e)}")
        conn.close()
        return None

def clean_dummy_data():
    """Elimina todos los datos dummy de las tablas"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Eliminar materiales dummy primero (por restricciones de clave foránea)
        cursor.execute("""
            DELETE FROM compras_v2_materiales 
            WHERE compra_imi = 0
        """)
        materiales_eliminados = cursor.rowcount
        
        # Eliminar pedidos dummy
        cursor.execute("""
            DELETE FROM pedidos_compras 
            WHERE compra_imi = 0
        """)
        pedidos_eliminados = cursor.rowcount
        
        # Eliminar compras dummy
        cursor.execute("""
            DELETE FROM compras_v2 
            WHERE proveedor = 'DUMMY_PROVEEDOR' OR puerto_origen = 'DUMMY_PUERTO'
        """)
        compras_eliminadas = cursor.rowcount
        
        # Confirmar cambios
        conn.commit()
        
        logger.info(f"Datos dummy eliminados:")
        logger.info(f"  - compras_v2_materiales: {materiales_eliminados} registros")
        logger.info(f"  - pedidos_compras: {pedidos_eliminados} registros")
        logger.info(f"  - compras_v2: {compras_eliminadas} registros")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error eliminando datos dummy: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def verify_cleanup():
    """Verifica que la limpieza se completó correctamente"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar que no queden datos dummy
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM compras_v2 
            WHERE proveedor = 'DUMMY_PROVEEDOR' OR puerto_origen = 'DUMMY_PUERTO'
        """)
        compras_dummy_restantes = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM pedidos_compras 
            WHERE compra_imi = 0
        """)
        pedidos_dummy_restantes = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM compras_v2_materiales 
            WHERE compra_imi = 0
        """)
        materiales_dummy_restantes = cursor.fetchone()['count']
        
        # Contar registros válidos
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        compras_validas = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM pedidos_compras WHERE compra_imi > 0")
        pedidos_validos = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales WHERE compra_imi > 0")
        materiales_validos = cursor.fetchone()['count']
        
        logger.info(f"Verificación de limpieza:")
        logger.info(f"  - Datos dummy restantes: {compras_dummy_restantes + pedidos_dummy_restantes + materiales_dummy_restantes}")
        logger.info(f"  - Registros válidos:")
        logger.info(f"    * compras_v2: {compras_validas}")
        logger.info(f"    * pedidos_compras: {pedidos_validos}")
        logger.info(f"    * compras_v2_materiales: {materiales_validos}")
        
        cursor.close()
        conn.close()
        
        return {
            'dummy_restantes': compras_dummy_restantes + pedidos_dummy_restantes + materiales_dummy_restantes,
            'compras_validas': compras_validas,
            'pedidos_validos': pedidos_validos,
            'materiales_validos': materiales_validos
        }
        
    except Exception as e:
        logger.error(f"Error verificando limpieza: {str(e)}")
        conn.close()
        return False

def main():
    """Función principal"""
    print("LIMPIEZA DE DATOS DUMMY DE MIGRACIONES")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Verificar datos dummy existentes
        logger.info("Verificando datos dummy existentes...")
        dummy_data = check_dummy_data()
        
        if not dummy_data:
            logger.error("No se pudo verificar los datos dummy")
            return False
        
        total_dummy = dummy_data['compras_dummy'] + dummy_data['pedidos_dummy'] + dummy_data['materiales_dummy']
        
        if total_dummy == 0:
            logger.info("No se encontraron datos dummy para eliminar")
            return True
        
        logger.info(f"Se encontraron {total_dummy} registros dummy para eliminar")
        
        # Eliminar datos dummy
        logger.info("Eliminando datos dummy...")
        cleanup_success = clean_dummy_data()
        
        if cleanup_success:
            # Verificar limpieza
            logger.info("Verificando limpieza...")
            verification = verify_cleanup()
            
            print("\n" + "="*60)
            print("RESUMEN DE LIMPIEZA")
            print("="*60)
            print(f"Datos dummy eliminados: {total_dummy}")
            print(f"Datos dummy restantes: {verification['dummy_restantes']}")
            print(f"Registros válidos:")
            print(f"  - compras_v2: {verification['compras_validas']}")
            print(f"  - pedidos_compras: {verification['pedidos_validos']}")
            print(f"  - compras_v2_materiales: {verification['materiales_validos']}")
            print("="*60)
            
            if verification['dummy_restantes'] == 0:
                logger.info("LIMPIEZA COMPLETADA EXITOSAMENTE!")
                logger.info("Todos los datos dummy han sido eliminados")
                return True
            else:
                logger.warning("Quedan algunos datos dummy por eliminar")
                return False
        else:
            logger.error("Error durante la limpieza")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
