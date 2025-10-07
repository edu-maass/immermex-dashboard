"""
Script para verificar la estructura real de la tabla compras_v2 en Supabase
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
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

def check_table_structure():
    """Verifica la estructura de la tabla compras_v2"""
    conn = get_supabase_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Obtener estructura de compras_v2
        logger.info("=== ESTRUCTURA DE TABLA compras_v2 ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            logger.info(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Obtener estructura de compras_v2_materiales
        logger.info("\n=== ESTRUCTURA DE TABLA compras_v2_materiales ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2_materiales' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            logger.info(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verificando estructura: {str(e)}")

if __name__ == "__main__":
    check_table_structure()

