"""
Script para agregar columnas de fechas reales a la tabla compras_v2 en Supabase
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def add_real_date_columns_supabase():
    """Agrega las columnas de fechas reales a compras_v2 en Supabase"""
    try:
        # Usar las variables de entorno de Supabase
        conn = psycopg2.connect(
            host=os.getenv('SUPABASE_URL').replace('https://', '').replace('http://', ''),
            port=5432,
            database='postgres',
            user='postgres',
            password=os.getenv('SUPABASE_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        # Verificar si las columnas ya existen
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2' 
            AND column_name IN ('fecha_salida_real', 'fecha_arribo_real', 'fecha_planta_real')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Columnas existentes: {existing_columns}")
        
        # Agregar columnas que no existen
        columns_to_add = [
            ('fecha_salida_real', 'DATE'),
            ('fecha_arribo_real', 'DATE'),
            ('fecha_planta_real', 'DATE')
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                print(f"Agregando columna {column_name}...")
                cursor.execute(f"""
                    ALTER TABLE compras_v2 
                    ADD COLUMN {column_name} {column_type}
                """)
                print(f"Columna {column_name} agregada exitosamente")
            else:
                print(f"Columna {column_name} ya existe")
        
        # Commit los cambios
        conn.commit()
        print("Todas las columnas agregadas exitosamente")
        
        # Verificar la estructura final
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2' 
            AND column_name LIKE '%fecha%'
            ORDER BY ordinal_position
        """)
        
        print("\nEstructura de columnas de fecha en compras_v2:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error agregando columnas: {e}")
        return False

if __name__ == "__main__":
    print("Agregando columnas de fechas reales a compras_v2 en Supabase...")
    success = add_real_date_columns_supabase()
    if success:
        print("Proceso completado exitosamente")
    else:
        print("Error en el proceso")
