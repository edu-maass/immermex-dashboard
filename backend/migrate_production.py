"""
Script para migrar la base de datos en producción (Supabase)
"""

import os
import sys
from dotenv import load_dotenv
from database import init_db
from logging_config import setup_logging

def main():
    """Ejecuta la migración de la base de datos en producción"""
    logger = setup_logging()
    
    try:
        # Cargar variables de entorno
        load_dotenv('production.env')
        
        # Verificar que DATABASE_URL esté configurada
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("❌ DATABASE_URL no está configurada")
            sys.exit(1)
        
        if not database_url.startswith("postgresql://"):
            logger.error("❌ DATABASE_URL debe ser una URL de PostgreSQL para producción")
            sys.exit(1)
        
        logger.info("🚀 Iniciando migración de base de datos en producción...")
        logger.info(f"🔗 Conectando a: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'Supabase'}")
        
        # Inicializar base de datos
        success = init_db()
        
        if success:
            logger.info("✅ Migración completada exitosamente")
            logger.info("🎉 Base de datos de producción lista para usar")
        else:
            logger.error("❌ Error en la migración")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
