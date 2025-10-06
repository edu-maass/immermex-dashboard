"""
Script para analizar la estructura de las tablas de compras
Verifica las tablas compras, compras_v2 y compras_v2_materiales en Supabase
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

def analyze_table_structure(table_name):
    """Analiza la estructura de una tabla específica"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = %s AND table_schema = 'public'
        """, (table_name,))
        
        exists = cursor.fetchone()['count'] > 0
        
        if not exists:
            logger.warning(f"Tabla '{table_name}' no existe")
            return None
        
        # Obtener estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()['count']
        
        logger.info(f"Tabla '{table_name}' - {count} registros:")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            logger.info(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        cursor.close()
        conn.close()
        
        return {
            'exists': True,
            'columns': columns,
            'count': count
        }
        
    except Exception as e:
        logger.error(f"Error analizando tabla {table_name}: {str(e)}")
        conn.close()
        return None

def analyze_foreign_keys():
    """Analiza las relaciones de clave foránea entre las tablas"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Verificar relaciones de clave foránea
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('compras', 'compras_v2', 'compras_v2_materiales')
        """)
        
        constraints = cursor.fetchall()
        
        logger.info("Relaciones de clave foránea:")
        for constraint in constraints:
            logger.info(f"  {constraint['table_name']}.{constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}")
        
        cursor.close()
        conn.close()
        
        return constraints
        
    except Exception as e:
        logger.error(f"Error analizando claves foráneas: {str(e)}")
        conn.close()
        return None

def get_sample_data(table_name, limit=5):
    """Obtiene datos de muestra de una tabla"""
    conn = get_supabase_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        sample_data = cursor.fetchall()
        
        logger.info(f"Datos de muestra de '{table_name}':")
        for i, record in enumerate(sample_data, 1):
            logger.info(f"  Registro {i}: {dict(record)}")
        
        cursor.close()
        conn.close()
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de muestra de {table_name}: {str(e)}")
        conn.close()
        return None

def main():
    """Función principal de análisis"""
    print("ANALISIS DE ESTRUCTURA DE TABLAS DE COMPRAS")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Analizar tabla compras (original)
        logger.info("Analizando tabla 'compras'...")
        compras_structure = analyze_table_structure('compras')
        
        if compras_structure:
            get_sample_data('compras')
        
        # Analizar tabla compras_v2
        logger.info("\nAnalizando tabla 'compras_v2'...")
        compras_v2_structure = analyze_table_structure('compras_v2')
        
        if compras_v2_structure:
            get_sample_data('compras_v2')
        
        # Analizar tabla compras_v2_materiales
        logger.info("\nAnalizando tabla 'compras_v2_materiales'...")
        compras_v2_materiales_structure = analyze_table_structure('compras_v2_materiales')
        
        if compras_v2_materiales_structure:
            get_sample_data('compras_v2_materiales')
        
        # Analizar relaciones de clave foránea
        logger.info("\nAnalizando relaciones de clave foránea...")
        foreign_keys = analyze_foreign_keys()
        
        # Resumen
        print("\n" + "="*60)
        print("RESUMEN DEL ANALISIS")
        print("="*60)
        print(f"Tabla 'compras': {'Existe' if compras_structure else 'No existe'}")
        if compras_structure:
            print(f"  - Registros: {compras_structure['count']}")
            print(f"  - Columnas: {len(compras_structure['columns'])}")
        
        print(f"Tabla 'compras_v2': {'Existe' if compras_v2_structure else 'No existe'}")
        if compras_v2_structure:
            print(f"  - Registros: {compras_v2_structure['count']}")
            print(f"  - Columnas: {len(compras_v2_structure['columns'])}")
        
        print(f"Tabla 'compras_v2_materiales': {'Existe' if compras_v2_materiales_structure else 'No existe'}")
        if compras_v2_materiales_structure:
            print(f"  - Registros: {compras_v2_materiales_structure['count']}")
            print(f"  - Columnas: {len(compras_v2_materiales_structure['columns'])}")
        
        print(f"Relaciones de clave foránea: {len(foreign_keys) if foreign_keys else 0}")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
