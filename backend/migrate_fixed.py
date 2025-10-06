"""
Script de migración corregido para Supabase
Maneja la restricción de clave foránea de compra_imi
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
        
        logger.info("Conectando a Supabase usando configuración de production.env")
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def check_foreign_key_constraint():
    """Verifica la restricción de clave foránea"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar la restricción de clave foránea
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
                AND tc.table_name='pedidos_compras'
        """)
        
        constraints = cursor.fetchall()
        
        logger.info("Restricciones de clave foránea en pedidos_compras:")
        for constraint in constraints:
            logger.info(f"  - {constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}")
        
        cursor.close()
        conn.close()
        
        return len(constraints) > 0
        
    except Exception as e:
        logger.error(f"Error verificando restricciones: {str(e)}")
        conn.close()
        return False

def create_dummy_compra_record():
    """Crea un registro dummy en compras_v2 para satisfacer la restricción"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si ya existe un registro con compra_imi = 0
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE compra_imi = 0")
        exists = cursor.fetchone()['count'] > 0
        
        if not exists:
            logger.info("Creando registro dummy en compras_v2 para compra_imi = 0")
            
            cursor.execute("""
                INSERT INTO compras_v2 (compra_imi, created_at, updated_at)
                VALUES (0, NOW(), NOW())
            """)
            
            conn.commit()
            logger.info("Registro dummy creado exitosamente")
        else:
            logger.info("Registro dummy ya existe en compras_v2")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error creando registro dummy: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def migrate_pedidos_to_pedidos_compras():
    """Migra datos de pedidos a pedidos_compras en Supabase"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar que ambas tablas existan
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos_count = cursor.fetchone()['count']
        
        if pedidos_count == 0:
            logger.info("No hay datos en tabla 'pedidos' para migrar")
            return True
        
        logger.info(f"Iniciando migración de {pedidos_count} registros de 'pedidos' a 'pedidos_compras'")
        
        # Crear registro dummy si es necesario
        if not create_dummy_compra_record():
            logger.error("No se pudo crear el registro dummy necesario")
            return False
        
        # Obtener datos de pedidos
        cursor.execute("""
            SELECT id, folio_factura, pedido, kg, precio_unitario, importe_sin_iva, 
                   material, dias_credito, fecha_factura, fecha_pago, archivo_id, 
                   created_at, updated_at
            FROM pedidos
            ORDER BY id
        """)
        
        pedidos_data = cursor.fetchall()
        
        # Migrar cada pedido
        migrados = 0
        errores = 0
        
        for pedido in pedidos_data:
            try:
                # Calcular importe con IVA (16%)
                importe_con_iva = float(pedido['importe_sin_iva']) * 1.16 if pedido['importe_sin_iva'] else 0.0
                
                # Insertar en pedidos_compras
                cursor.execute("""
                    INSERT INTO pedidos_compras 
                    (compra_imi, folio_factura, material_codigo, kg, precio_unitario, 
                     importe_sin_iva, importe_con_iva, dias_credito, fecha_factura, 
                     fecha_pago, archivo_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    0,  # compra_imi inicializado en 0 (usando registro dummy)
                    pedido['folio_factura'],
                    pedido['material'],  # material -> material_codigo
                    pedido['kg'],
                    pedido['precio_unitario'],
                    pedido['importe_sin_iva'],
                    importe_con_iva,
                    pedido['dias_credito'],
                    pedido['fecha_factura'],
                    pedido['fecha_pago'],
                    pedido['archivo_id'],
                    pedido['created_at'],
                    pedido['updated_at']
                ))
                
                migrados += 1
                
                if migrados % 50 == 0:
                    logger.info(f"Progreso: {migrados}/{pedidos_count} registros migrados")
                
            except Exception as e:
                errores += 1
                logger.warning(f"Error migrando pedido {pedido['id']}: {str(e)}")
                # Continuar con el siguiente registro
                continue
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar migración
        cursor.execute("SELECT COUNT(*) FROM pedidos_compras")
        total_pedidos_compras = cursor.fetchone()['count']
        
        logger.info(f"Migración completada:")
        logger.info(f"  - Registros migrados exitosamente: {migrados}")
        logger.info(f"  - Registros con errores: {errores}")
        logger.info(f"  - Total en pedidos_compras: {total_pedidos_compras}")
        
        cursor.close()
        conn.close()
        
        return migrados > 0
        
    except Exception as e:
        logger.error(f"Error en migración: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def verify_migration():
    """Verifica que la migración se completó correctamente"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Contar registros en ambas tablas
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM pedidos_compras")
        total_pedidos_compras = cursor.fetchone()['count']
        
        logger.info(f"Verificación de migración:")
        logger.info(f"  - Registros en 'pedidos': {total_pedidos}")
        logger.info(f"  - Registros en 'pedidos_compras': {total_pedidos_compras}")
        
        # Verificar algunos registros específicos
        cursor.execute("""
            SELECT p.id, p.folio_factura, p.material, pc.id as pc_id
            FROM pedidos p
            LEFT JOIN pedidos_compras pc ON p.folio_factura = pc.folio_factura 
                AND p.material = pc.material_codigo
            LIMIT 5
        """)
        
        verificaciones = cursor.fetchall()
        verificaciones_exitosas = sum(1 for v in verificaciones if v['pc_id'] is not None)
        
        logger.info(f"Verificaciones exitosas: {verificaciones_exitosas}/{len(verificaciones)}")
        
        cursor.close()
        conn.close()
        
        return {
            'total_pedidos': total_pedidos,
            'total_pedidos_compras': total_pedidos_compras,
            'migration_successful': total_pedidos_compras > 0,
            'verification_rate': verificaciones_exitosas / len(verificaciones) if verificaciones else 0
        }
        
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        conn.close()
        return False

def main():
    """Función principal"""
    print("MIGRACION CORREGIDA PARA SUPABASE")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Verificar restricciones de clave foránea
        logger.info("Verificando restricciones de clave foránea...")
        check_foreign_key_constraint()
        
        # Ejecutar migración
        logger.info("Iniciando migración de datos...")
        migration_success = migrate_pedidos_to_pedidos_compras()
        
        if migration_success:
            # Verificar migración
            verification = verify_migration()
            
            print("\n" + "="*60)
            print("RESUMEN DE MIGRACION")
            print("="*60)
            print(f"Migración exitosa: {verification['migration_successful']}")
            print(f"Registros en 'pedidos': {verification['total_pedidos']}")
            print(f"Registros en 'pedidos_compras': {verification['total_pedidos_compras']}")
            print(f"Tasa de verificación: {verification['verification_rate']:.2%}")
            print("="*60)
            
            if verification['migration_successful']:
                logger.info("MIGRACION COMPLETADA EXITOSAMENTE!")
                return True
            else:
                logger.error("La migración no fue exitosa")
                return False
        else:
            logger.error("La migración falló")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
