"""
Script para verificar las tablas existentes en Supabase
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
            sslmode='require',
            connect_timeout=30
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def list_tables():
    """Lista todas las tablas en la base de datos"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        print("TABLAS EXISTENTES EN SUPABASE:")
        print("="*50)
        for table in tables:
            print(f"- {table['table_name']}")
        
        print(f"\nTotal de tablas: {len(tables)}")
        
        # Buscar tablas que contengan "proveedor" o "provider"
        proveedor_tables = [t for t in tables if 'proveedor' in t['table_name'].lower() or 'provider' in t['table_name'].lower()]
        
        if proveedor_tables:
            print(f"\nTablas relacionadas con proveedores:")
            for table in proveedor_tables:
                print(f"- {table['table_name']}")
        else:
            print(f"\nNo se encontraron tablas con 'proveedor' o 'provider'")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error listando tablas: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    list_tables()
