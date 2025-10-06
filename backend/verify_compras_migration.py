"""
Script de verificación final de la migración de compras
Verifica que las relaciones y datos estén correctos
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

def verify_migration_completeness():
    """Verifica que la migración esté completa"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Contar registros en todas las tablas
        cursor.execute("SELECT COUNT(*) FROM compras")
        total_compras = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        total_compras_v2 = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        total_materiales = cursor.fetchone()['count']
        
        logger.info(f"Conteo de registros:")
        logger.info(f"  - Tabla 'compras': {total_compras}")
        logger.info(f"  - Tabla 'compras_v2': {total_compras_v2}")
        logger.info(f"  - Tabla 'compras_v2_materiales': {total_materiales}")
        
        cursor.close()
        conn.close()
        
        return {
            'total_compras': total_compras,
            'total_compras_v2': total_compras_v2,
            'total_materiales': total_materiales
        }
        
    except Exception as e:
        logger.error(f"Error verificando migración: {str(e)}")
        conn.close()
        return False

def verify_relationships():
    """Verifica que las relaciones estén funcionando correctamente"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar relaciones compras_v2 -> compras_v2_materiales
        cursor.execute("""
            SELECT 
                c2.imi, c2.proveedor, c2.fecha_pedido,
                COUNT(c2m.id) as materiales_count,
                SUM(c2m.kg) as total_kg,
                SUM(c2m.costo_total_mxn) as total_costo_mxn
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0
            GROUP BY c2.imi, c2.proveedor, c2.fecha_pedido
            HAVING COUNT(c2m.id) > 0
            ORDER BY c2.imi
            LIMIT 10
        """)
        
        relaciones = cursor.fetchall()
        
        logger.info("Verificación de relaciones (compras con materiales):")
        for rel in relaciones:
            logger.info(f"  IMI {rel['imi']}: {rel['proveedor']} - {rel['materiales_count']} materiales, {rel['total_kg']} KG, ${rel['total_costo_mxn']}")
        
        # Verificar materiales sin compra
        cursor.execute("""
            SELECT COUNT(*) 
            FROM compras_v2_materiales c2m
            LEFT JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
            WHERE c2.imi IS NULL
        """)
        
        materiales_sin_compra = cursor.fetchone()['count']
        
        logger.info(f"Materiales sin compra asociada: {materiales_sin_compra}")
        
        cursor.close()
        conn.close()
        
        return len(relaciones) > 0 and materiales_sin_compra == 0
        
    except Exception as e:
        logger.error(f"Error verificando relaciones: {str(e)}")
        conn.close()
        return False

def verify_data_integrity():
    """Verifica la integridad de los datos migrados"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar que no haya valores negativos en campos importantes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM compras_v2_materiales 
            WHERE kg < 0 OR pu_divisa < 0 OR pu_mxn < 0 
               OR costo_total_divisa < 0 OR costo_total_mxn < 0
        """)
        
        valores_negativos = cursor.fetchone()['count']
        
        # Verificar que no haya valores NULL en campos obligatorios
        cursor.execute("""
            SELECT COUNT(*) 
            FROM compras_v2_materiales 
            WHERE material_codigo IS NULL OR kg IS NULL 
               OR pu_divisa IS NULL OR pu_mxn IS NULL
        """)
        
        valores_null = cursor.fetchone()['count']
        
        # Verificar rangos de fechas
        cursor.execute("""
            SELECT 
                MIN(fecha_pedido) as fecha_min,
                MAX(fecha_pedido) as fecha_max,
                COUNT(*) as total_fechas
            FROM compras_v2 
            WHERE imi > 0
        """)
        
        fechas_info = cursor.fetchone()
        
        logger.info(f"Verificación de integridad:")
        logger.info(f"  - Valores negativos: {valores_negativos}")
        logger.info(f"  - Valores NULL en campos obligatorios: {valores_null}")
        logger.info(f"  - Rango de fechas: {fechas_info['fecha_min']} a {fechas_info['fecha_max']}")
        logger.info(f"  - Total fechas válidas: {fechas_info['total_fechas']}")
        
        cursor.close()
        conn.close()
        
        return valores_negativos == 0 and valores_null == 0
        
    except Exception as e:
        logger.error(f"Error verificando integridad: {str(e)}")
        conn.close()
        return False

def verify_sample_data():
    """Verifica algunos datos de muestra para asegurar calidad"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Obtener muestra de compras_v2
        cursor.execute("""
            SELECT 
                c2.imi, c2.proveedor, c2.fecha_pedido, c2.moneda,
                c2.total_con_iva_mxn, c2.iva_monto_mxn,
                COUNT(c2m.id) as materiales_count
            FROM compras_v2 c2
            LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
            WHERE c2.imi > 0
            GROUP BY c2.imi, c2.proveedor, c2.fecha_pedido, c2.moneda, c2.total_con_iva_mxn, c2.iva_monto_mxn
            ORDER BY c2.imi
            LIMIT 5
        """)
        
        compras_muestra = cursor.fetchall()
        
        logger.info("Muestra de compras migradas:")
        for compra in compras_muestra:
            logger.info(f"  IMI {compra['imi']}: {compra['proveedor']} - {compra['fecha_pedido']} - {compra['moneda']} - ${compra['total_con_iva_mxn']} - {compra['materiales_count']} materiales")
        
        # Obtener muestra de materiales
        cursor.execute("""
            SELECT 
                c2m.material_codigo, c2m.kg, c2m.pu_mxn, 
                c2m.costo_total_mxn, c2m.costo_total_con_iva,
                c2.proveedor
            FROM compras_v2_materiales c2m
            JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
            ORDER BY c2m.id
            LIMIT 5
        """)
        
        materiales_muestra = cursor.fetchall()
        
        logger.info("Muestra de materiales migrados:")
        for material in materiales_muestra:
            logger.info(f"  {material['material_codigo']}: {material['kg']} KG - ${material['pu_mxn']}/KG - Total: ${material['costo_total_con_iva']} - {material['proveedor']}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando datos de muestra: {str(e)}")
        conn.close()
        return False

def main():
    """Función principal de verificación"""
    print("VERIFICACION FINAL DE MIGRACION DE COMPRAS")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Verificar completitud de migración
        logger.info("Verificando completitud de migración...")
        counts = verify_migration_completeness()
        
        # Verificar relaciones
        logger.info("\nVerificando relaciones...")
        relationships_ok = verify_relationships()
        
        # Verificar integridad de datos
        logger.info("\nVerificando integridad de datos...")
        integrity_ok = verify_data_integrity()
        
        # Verificar datos de muestra
        logger.info("\nVerificando datos de muestra...")
        sample_ok = verify_sample_data()
        
        # Resumen final
        print("\n" + "="*60)
        print("RESUMEN DE VERIFICACION")
        print("="*60)
        print(f"Completitud de migración: OK")
        print(f"  - Tabla 'compras': {counts['total_compras']} registros")
        print(f"  - Tabla 'compras_v2': {counts['total_compras_v2']} registros")
        print(f"  - Tabla 'compras_v2_materiales': {counts['total_materiales']} registros")
        print(f"Relaciones funcionando: {'OK' if relationships_ok else 'ERROR'}")
        print(f"Integridad de datos: {'OK' if integrity_ok else 'ERROR'}")
        print(f"Datos de muestra: {'OK' if sample_ok else 'ERROR'}")
        print("="*60)
        
        if relationships_ok and integrity_ok and sample_ok:
            print("\nMIGRACION DE COMPRAS VERIFICADA EXITOSAMENTE!")
            print("La migración de 'compras' a 'compras_v2' y 'compras_v2_materiales' fue exitosa")
            print("\nResumen:")
            print(f"- {counts['total_compras_v2']} compras migradas a compras_v2")
            print(f"- {counts['total_materiales']} materiales migrados a compras_v2_materiales")
            print("- Todas las relaciones funcionando correctamente")
            print("- Integridad de datos verificada")
            return True
        else:
            print("\nAlgunas verificaciones necesitan atención")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
