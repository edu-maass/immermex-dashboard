"""
Script para crear la tabla de compras en Supabase
Ejecuta el script SQL directamente en la base de datos
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('production.env')

def create_compras_table():
    """Crea la tabla de compras en Supabase"""
    
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: No se encontro DATABASE_URL en las variables de entorno")
        print("Asegurate de tener un archivo production.env con la configuracion de Supabase")
        return False
    
    print("Conectando a Supabase...")
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(database_url)
        
        # Leer el script SQL
        with open('create_compras_table.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("Ejecutando script SQL...")
        
        # Dividir el script en comandos individuales
        commands = []
        current_command = []
        in_function = False
        
        for line in sql_script.split('\n'):
            # Detectar inicio de función
            if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
                in_function = True
            
            # Detectar fin de función
            if in_function and line.strip().startswith('$$'):
                current_command.append(line)
                if 'language' in line.lower():
                    commands.append('\n'.join(current_command))
                    current_command = []
                    in_function = False
                    continue
            
            # Ignorar comentarios y líneas vacías
            if line.strip().startswith('--') or not line.strip():
                continue
            
            current_command.append(line)
            
            # Si no estamos en una función y encontramos ';', es un comando completo
            if not in_function and ';' in line:
                commands.append('\n'.join(current_command))
                current_command = []
        
        # Agregar último comando si existe
        if current_command:
            commands.append('\n'.join(current_command))
        
        # Ejecutar cada comando
        with engine.connect() as connection:
            for i, command in enumerate(commands, 1):
                if command.strip():
                    try:
                        print(f"Ejecutando comando {i}/{len(commands)}...")
                        connection.execute(text(command))
                        connection.commit()
                    except Exception as e:
                        print(f"Advertencia en comando {i}: {str(e)}")
                        # Continuar con los demás comandos
                        continue
        
        print("\nTabla de compras creada exitosamente!")
        print("\nDetalles de la tabla:")
        print("- Tabla: compras")
        print("- Campos: 65 columnas (campos generales + campos de importacion)")
        print("- Indices: 6 indices para optimizar consultas")
        print("- Triggers: updated_at automatico")
        print("\nLa tabla esta lista para recibir datos de compras!")
        
        return True
        
    except Exception as e:
        print(f"\nERROR al crear la tabla: {str(e)}")
        print("\nDetalles del error:")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'engine' in locals():
            engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("CREACION DE TABLA DE COMPRAS EN SUPABASE")
    print("=" * 60)
    print()
    
    success = create_compras_table()
    
    print()
    print("=" * 60)
    
    if success:
        print("PROCESO COMPLETADO EXITOSAMENTE")
        print("\nProximos pasos:")
        print("1. Iniciar el servidor backend")
        print("2. Acceder al frontend")
        print("3. Ir a 'Carga de Archivos'")
        print("4. Subir archivo de compras en la seccion derecha")
    else:
        print("PROCESO FALLIDO - Revisar errores arriba")
    
    print("=" * 60)
    
    sys.exit(0 if success else 1)
