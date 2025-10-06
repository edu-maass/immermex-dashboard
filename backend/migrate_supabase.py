"""
Script para verificar y migrar datos en Supabase PostgreSQL
Conecta directamente a la base de datos de Supabase
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_connection():
    """Obtiene conexión directa a Supabase PostgreSQL"""
    try:
        # Variables de entorno de Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_PASSWORD")
        
        if not supabase_url or not supabase_password:
            logger.error("Variables SUPABASE_URL y SUPABASE_PASSWORD no encontradas")
            return None
        
        # Extraer project ref de la URL
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
            
            # Usar conexión directa a PostgreSQL
            conn_string = f"postgresql://postgres:{supabase_password}@db.{project_ref}.supabase.co:5432/postgres"
            
            logger.info(f"Conectando a Supabase PostgreSQL: db.{project_ref}.supabase.co")
            
            conn = psycopg2.connect(
                conn_string,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
            
            return conn
        else:
            logger.error("Formato de SUPABASE_URL no reconocido")
            return None
            
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def check_supabase_tables():
    """Verifica las tablas existentes en Supabase"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar tabla pedidos
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'pedidos' AND table_schema = 'public'
        """)
        pedidos_exists = cursor.fetchone()['count'] > 0
        
        if pedidos_exists:
            cursor.execute("SELECT COUNT(*) as count FROM pedidos")
            pedidos_count = cursor.fetchone()['count']
            logger.info(f"Tabla 'pedidos' existe con {pedidos_count} registros")
        else:
            logger.warning("Tabla 'pedidos' no existe")
        
        # Verificar tabla pedidos_compras
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'pedidos_compras' AND table_schema = 'public'
        """)
        pedidos_compras_exists = cursor.fetchone()['count'] > 0
        
        if pedidos_compras_exists:
            cursor.execute("SELECT COUNT(*) as count FROM pedidos_compras")
            pedidos_compras_count = cursor.fetchone()['count']
            logger.info(f"Tabla 'pedidos_compras' existe con {pedidos_compras_count} registros")
        else:
            logger.warning("Tabla 'pedidos_compras' no existe")
        
        # Mostrar estructura de tabla pedidos
        if pedidos_exists:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'pedidos' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            logger.info("Estructura de tabla 'pedidos':")
            for col in columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Mostrar estructura de tabla pedidos_compras
        if pedidos_compras_exists:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'pedidos_compras' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            logger.info("Estructura de tabla 'pedidos_compras':")
            for col in columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        cursor.close()
        conn.close()
        
        return pedidos_exists, pedidos_compras_exists
        
    except Exception as e:
        logger.error(f"Error verificando tablas: {str(e)}")
        conn.close()
        return False, False

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
                    0,  # compra_imi inicializado en 0
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
                
                if migrados % 100 == 0:
                    logger.info(f"Progreso: {migrados}/{pedidos_count} registros migrados")
                
            except Exception as e:
                errores += 1
                logger.warning(f"Error migrando pedido {pedido['id']}: {str(e)}")
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
    print("VERIFICACION Y MIGRACION EN SUPABASE POSTGRESQL")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Verificar tablas
        logger.info("Verificando tablas en Supabase...")
        pedidos_exists, pedidos_compras_exists = check_supabase_tables()
        
        if not pedidos_exists:
            logger.error("Tabla 'pedidos' no existe en Supabase")
            return False
        
        if not pedidos_compras_exists:
            logger.error("Tabla 'pedidos_compras' no existe en Supabase")
            return False
        
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
