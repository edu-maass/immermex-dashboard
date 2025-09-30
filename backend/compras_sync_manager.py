"""
Script de configuración y sincronización automática de compras
Ejecuta la configuración inicial y sincronización periódica
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
import schedule
import time

# Agregar el directorio backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.compras_import_service import ComprasImportService
from services.onedrive_service import OneDriveService, get_onedrive_credentials_instructions

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('compras_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ComprasSyncManager:
    """Gestor de sincronización automática de compras"""
    
    def __init__(self):
        self.compras_service = ComprasImportService()
        self.sync_interval = int(os.getenv("ONEDRIVE_SYNC_INTERVAL", "3600"))  # 1 hora
        self.is_running = False
    
    async def sync_compras(self):
        """Ejecuta sincronización de compras"""
        try:
            logger.info("Iniciando sincronización de compras")
            start_time = datetime.now()
            
            result = await self.compras_service.sync_compras_automatic()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result["success"]:
                logger.info(f"Sincronización completada en {duration:.2f}s")
                logger.info(f"Archivos procesados: {result.get('files_processed', 0)}")
                logger.info(f"Registros importados: {result.get('records_imported', 0)}")
            else:
                logger.error(f"Error en sincronización: {result.get('error', 'Error desconocido')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error durante sincronización: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_sync(self):
        """Programa la sincronización automática"""
        # Sincronización cada hora
        schedule.every().hour.do(self.run_sync)
        
        # Sincronización al inicio
        schedule.every().day.at("08:00").do(self.run_sync)
        
        logger.info("Sincronización programada cada hora y a las 8:00 AM")
    
    def run_sync(self):
        """Ejecuta sincronización en hilo separado"""
        if not self.is_running:
            self.is_running = True
            try:
                asyncio.run(self.sync_compras())
            finally:
                self.is_running = False
    
    def start_scheduler(self):
        """Inicia el programador de tareas"""
        logger.info("Iniciando programador de sincronización")
        self.schedule_sync()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto

async def test_onedrive_connection():
    """Prueba la conexión con OneDrive"""
    try:
        logger.info("Probando conexión con OneDrive...")
        
        onedrive_service = OneDriveService()
        
        # Probar obtención de token
        token = await onedrive_service.get_access_token()
        logger.info("✓ Token de acceso obtenido")
        
        # Probar listado de archivos
        files = await onedrive_service.list_files_in_folder()
        logger.info(f"✓ Encontrados {len(files)} archivos en la carpeta de compras")
        
        for file in files[:3]:  # Mostrar solo los primeros 3
            logger.info(f"  - {file.name} ({file.size} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando conexión con OneDrive: {e}")
        return False

async def test_database_connection():
    """Prueba la conexión con la base de datos"""
    try:
        logger.info("Probando conexión con base de datos...")
        
        from database_service_refactored import DatabaseService
        db_service = DatabaseService()
        
        # Probar consulta simple
        result = await db_service.execute_query("SELECT 1 as test")
        logger.info("✓ Conexión con base de datos exitosa")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando conexión con base de datos: {e}")
        return False

async def setup_initial_sync():
    """Configuración inicial y primera sincronización"""
    logger.info("="*60)
    logger.info("CONFIGURACIÓN INICIAL DE COMPRAS")
    logger.info("="*60)
    
    # Verificar variables de entorno
    required_vars = [
        "ONEDRIVE_CLIENT_ID",
        "ONEDRIVE_CLIENT_SECRET", 
        "ONEDRIVE_REFRESH_TOKEN",
        "DATABASE_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        logger.info("\n" + get_onedrive_credentials_instructions())
        return False
    
    logger.info("✓ Variables de entorno configuradas")
    
    # Probar conexiones
    db_ok = await test_database_connection()
    onedrive_ok = await test_onedrive_connection()
    
    if not db_ok or not onedrive_ok:
        logger.error("❌ No se pueden establecer las conexiones necesarias")
        return False
    
    # Ejecutar primera sincronización
    logger.info("Ejecutando primera sincronización...")
    sync_manager = ComprasSyncManager()
    result = await sync_manager.sync_compras()
    
    if result["success"]:
        logger.info("✓ Primera sincronización exitosa")
        logger.info(f"  - Archivos procesados: {result.get('files_processed', 0)}")
        logger.info(f"  - Registros importados: {result.get('records_imported', 0)}")
    else:
        logger.error(f"❌ Error en primera sincronización: {result.get('error', 'Error desconocido')}")
    
    return result["success"]

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestor de sincronización de compras")
    parser.add_argument("--setup", action="store_true", help="Ejecutar configuración inicial")
    parser.add_argument("--sync", action="store_true", help="Ejecutar sincronización única")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar como daemon (sincronización automática)")
    parser.add_argument("--test", action="store_true", help="Probar conexiones")
    
    args = parser.parse_args()
    
    if args.setup:
        logger.info("Ejecutando configuración inicial...")
        success = asyncio.run(setup_initial_sync())
        if success:
            logger.info("✓ Configuración inicial completada exitosamente")
        else:
            logger.error("❌ Error en configuración inicial")
            sys.exit(1)
    
    elif args.sync:
        logger.info("Ejecutando sincronización única...")
        sync_manager = ComprasSyncManager()
        result = asyncio.run(sync_manager.sync_compras())
        if result["success"]:
            logger.info("✓ Sincronización completada")
        else:
            logger.error("❌ Error en sincronización")
            sys.exit(1)
    
    elif args.test:
        logger.info("Probando conexiones...")
        db_ok = asyncio.run(test_database_connection())
        onedrive_ok = asyncio.run(test_onedrive_connection())
        
        if db_ok and onedrive_ok:
            logger.info("✓ Todas las conexiones funcionan correctamente")
        else:
            logger.error("❌ Algunas conexiones fallaron")
            sys.exit(1)
    
    elif args.daemon:
        logger.info("Iniciando daemon de sincronización...")
        sync_manager = ComprasSyncManager()
        sync_manager.start_scheduler()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
