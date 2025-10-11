"""
Script para exportar backups de Supabase a CSV
Uso: python export_backup.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import csv
from datetime import datetime
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_table_to_csv(table_name, output_dir="backups", conn=None):
    """Exporta una tabla completa a CSV"""
    
    try:
        # Crear directorio de backups si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Usar conexión existente o crear nueva
        should_close = False
        if conn is None:
            # Obtener DATABASE_URL desde variables de entorno
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("DATABASE_URL no configurada en variables de entorno")
                return False
            
            conn = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
            should_close = True
        
        cursor = conn.cursor()
        
        # Obtener todos los datos
        logger.info(f"Exportando tabla {table_name}...")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning(f"⚠️  Tabla {table_name} está vacía")
            cursor.close()
            if should_close:
                conn.close()
            return True  # No es un error, solo está vacía
        
        # Crear archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{table_name}_{timestamp}.csv"
        
        # Escribir CSV
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            # Obtener nombres de columnas
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"✅ Exportados {len(rows)} registros de {table_name} a {filename}")
        
        cursor.close()
        if should_close:
            conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exportando {table_name}: {str(e)}")
        return False

def create_backup_log(output_dir="backups", tables_info=None):
    """Crea un log con información del backup"""
    
    try:
        log_file = f"{output_dir}/backup_log.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{timestamp} - Backup automático\n")
            if tables_info:
                for table, count in tables_info.items():
                    f.write(f"  - {table}: {count} registros\n")
        
        logger.info(f"✅ Log de backup actualizado: {log_file}")
        
    except Exception as e:
        logger.error(f"❌ Error creando log: {str(e)}")

def get_table_counts(conn):
    """Obtiene conteo de registros de cada tabla"""
    
    tables = [
        'compras_v2',
        'compras_v2_materiales',
        'facturacion',
        'cobranza',
        'pedidos',
        'archivos_procesados'
    ]
    
    counts = {}
    cursor = conn.cursor()
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
        except Exception as e:
            logger.warning(f"No se pudo contar {table}: {str(e)}")
            counts[table] = 0
    
    cursor.close()
    return counts

def main():
    """Función principal de backup"""
    
    logger.info("="*60)
    logger.info("INICIANDO BACKUP DE SUPABASE")
    logger.info("="*60)
    
    # Verificar DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL no configurada")
        logger.info("Configura con: export DATABASE_URL='postgresql://...'")
        return False
    
    try:
        # Conectar a base de datos
        logger.info("Conectando a Supabase...")
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
        logger.info("✅ Conexión establecida")
        
        # Obtener conteos
        logger.info("Obteniendo conteos de tablas...")
        counts = get_table_counts(conn)
        
        # Mostrar resumen
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE TABLAS:")
        for table, count in counts.items():
            logger.info(f"  {table:<30} {count:>10} registros")
        logger.info("="*60 + "\n")
        
        # Exportar cada tabla
        tables_to_export = [
            'compras_v2',
            'compras_v2_materiales',
            'facturacion',
            'cobranza',
            'pedidos',
            'archivos_procesados'
        ]
        
        success_count = 0
        for table in tables_to_export:
            if export_table_to_csv(table, conn=conn):
                success_count += 1
        
        # Crear log de backup
        create_backup_log(tables_info=counts)
        
        # Cerrar conexión
        conn.close()
        
        # Resumen final
        logger.info("\n" + "="*60)
        logger.info(f"BACKUP COMPLETADO: {success_count}/{len(tables_to_export)} tablas")
        logger.info("="*60)
        
        return success_count == len(tables_to_export)
        
    except Exception as e:
        logger.error(f"❌ Error en backup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

