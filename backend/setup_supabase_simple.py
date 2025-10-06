"""
Script para configurar variables de entorno de Supabase
Ayuda a configurar la conexión a PostgreSQL de Supabase
"""

import os
import sys

def check_environment_variables():
    """Verifica las variables de entorno necesarias"""
    print("VERIFICACION DE VARIABLES DE ENTORNO SUPABASE")
    print("="*50)
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_password = os.getenv("SUPABASE_PASSWORD")
    
    print(f"SUPABASE_URL: {'Configurada' if supabase_url else 'No configurada'}")
    if supabase_url:
        print(f"  Valor: {supabase_url}")
    
    print(f"SUPABASE_PASSWORD: {'Configurada' if supabase_password else 'No configurada'}")
    if supabase_password:
        print(f"  Valor: {'*' * len(supabase_password)}")
    
    return supabase_url, supabase_password

def setup_environment_variables():
    """Ayuda a configurar las variables de entorno"""
    print("\nCONFIGURACION DE VARIABLES DE ENTORNO")
    print("="*50)
    
    print("Para configurar las variables de entorno de Supabase:")
    print()
    print("1. Obten las credenciales de tu proyecto Supabase:")
    print("   - Ve a https://supabase.com/dashboard")
    print("   - Selecciona tu proyecto")
    print("   - Ve a Settings > Database")
    print("   - Copia la 'Connection string' o usa:")
    print("     - Host: db.[project-ref].supabase.co")
    print("     - Password: [tu-password]")
    print()
    print("2. Configura las variables de entorno:")
    print()
    print("   En Windows (PowerShell):")
    print("   $env:SUPABASE_URL = 'https://[project-ref].supabase.co'")
    print("   $env:SUPABASE_PASSWORD = '[tu-password]'")
    print()
    print("   En Windows (CMD):")
    print("   set SUPABASE_URL=https://[project-ref].supabase.co")
    print("   set SUPABASE_PASSWORD=[tu-password]")
    print()
    print("   En Linux/Mac:")
    print("   export SUPABASE_URL='https://[project-ref].supabase.co'")
    print("   export SUPABASE_PASSWORD='[tu-password]'")
    print()
    print("3. O crea un archivo .env en la carpeta backend con:")
    print("   SUPABASE_URL=https://[project-ref].supabase.co")
    print("   SUPABASE_PASSWORD=[tu-password]")

def test_connection():
    """Prueba la conexión a Supabase"""
    print("\nPRUEBA DE CONEXION")
    print("="*50)
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_PASSWORD")
        
        if not supabase_url or not supabase_password:
            print("Variables de entorno no configuradas")
            return False
        
        # Extraer project ref
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
            
            conn_string = f"postgresql://postgres:{supabase_password}@db.{project_ref}.supabase.co:5432/postgres"
            
            print(f"Conectando a: db.{project_ref}.supabase.co")
            
            conn = psycopg2.connect(
                conn_string,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            
            print("Conexion exitosa a Supabase PostgreSQL")
            print(f"  Version: {version['version'][:50]}...")
            
            cursor.close()
            conn.close()
            
            return True
        else:
            print("Formato de SUPABASE_URL incorrecto")
            return False
            
    except Exception as e:
        print(f"Error de conexion: {str(e)}")
        return False

def main():
    """Función principal"""
    print("CONFIGURACION DE SUPABASE PARA IMMERMEX")
    print("="*60)
    
    # Verificar variables de entorno
    supabase_url, supabase_password = check_environment_variables()
    
    if not supabase_url or not supabase_password:
        setup_environment_variables()
        print("\n" + "="*60)
        print("CONFIGURA LAS VARIABLES DE ENTORNO Y EJECUTA ESTE SCRIPT NUEVAMENTE")
        print("="*60)
        return False
    
    # Probar conexión
    if test_connection():
        print("\nCONFIGURACION COMPLETA")
        print("Ya puedes ejecutar el script de migracion:")
        print("python migrate_supabase.py")
        return True
    else:
        print("\nCONFIGURACION INCOMPLETA")
        print("Revisa las credenciales de Supabase")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
