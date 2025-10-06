"""
Script para verificar la estructura de la tabla Proveedores
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

def check_proveedores_structure():
    """Verifica la estructura de la tabla Proveedores"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Obtener estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'Proveedores' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("ESTRUCTURA DE LA TABLA 'Proveedores':")
        print("="*60)
        for col in columns:
            print(f"- {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        
        # Obtener algunos registros de ejemplo
        cursor.execute("""
            SELECT * FROM "Proveedores" LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        
        print(f"\nDATOS DE EJEMPLO (primeros 5 registros):")
        print("="*60)
        for i, row in enumerate(sample_data, 1):
            print(f"Registro {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
            print()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando estructura: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    check_proveedores_structure()
