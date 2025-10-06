"""
Script para restaurar datos de pedidos_compras
Restaura los datos válidos desde la tabla original 'pedidos'
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

def restore_pedidos_compras():
    """Restaura los datos de pedidos_compras desde la tabla original pedidos"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la tabla pedidos tenga datos
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos_count = cursor.fetchone()['count']
        
        if pedidos_count == 0:
            logger.info("No hay datos en la tabla 'pedidos' para restaurar")
            return True
        
        logger.info(f"Restaurando {pedidos_count} registros desde tabla 'pedidos'")
        
        # Obtener datos de pedidos
        cursor.execute("""
            SELECT id, folio_factura, pedido, kg, precio_unitario, importe_sin_iva, 
                   material, dias_credito, fecha_factura, fecha_pago, archivo_id, 
                   created_at, updated_at
            FROM pedidos
            ORDER BY id
        """)
        
        pedidos_data = cursor.fetchall()
        
        # Restaurar cada pedido
        restaurados = 0
        errores = 0
        
        for pedido in pedidos_data:
            try:
                # Calcular importe con IVA (16%)
                importe_con_iva = float(pedido['importe_sin_iva']) * 1.16 if pedido['importe_sin_iva'] else 0.0
                
                # Insertar en pedidos_compras con compra_imi = NULL (sin relación por ahora)
                cursor.execute("""
                    INSERT INTO pedidos_compras 
                    (folio_factura, material_codigo, kg, precio_unitario, 
                     importe_sin_iva, importe_con_iva, dias_credito, fecha_factura, 
                     fecha_pago, archivo_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
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
                
                restaurados += 1
                
                if restaurados % 50 == 0:
                    logger.info(f"Progreso: {restaurados}/{pedidos_count} registros restaurados")
                
            except Exception as e:
                errores += 1
                logger.warning(f"Error restaurando pedido {pedido['id']}: {str(e)}")
                continue
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar restauración
        cursor.execute("SELECT COUNT(*) FROM pedidos_compras")
        total_pedidos_compras = cursor.fetchone()['count']
        
        logger.info(f"Restauración completada:")
        logger.info(f"  - Registros restaurados exitosamente: {restaurados}")
        logger.info(f"  - Registros con errores: {errores}")
        logger.info(f"  - Total en pedidos_compras: {total_pedidos_compras}")
        
        cursor.close()
        conn.close()
        
        return restaurados > 0
        
    except Exception as e:
        logger.error(f"Error en restauración: {str(e)}")
        conn.rollback()
        conn.close()
        return False

def verify_restoration():
    """Verifica que la restauración se completó correctamente"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Contar registros en todas las tablas
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM pedidos_compras")
        total_pedidos_compras = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2 WHERE imi > 0")
        total_compras_v2 = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM compras_v2_materiales")
        total_materiales = cursor.fetchone()['count']
        
        logger.info(f"Verificación de restauración:")
        logger.info(f"  - Registros en 'pedidos': {total_pedidos}")
        logger.info(f"  - Registros en 'pedidos_compras': {total_pedidos_compras}")
        logger.info(f"  - Registros en 'compras_v2': {total_compras_v2}")
        logger.info(f"  - Registros en 'compras_v2_materiales': {total_materiales}")
        
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
            'total_compras_v2': total_compras_v2,
            'total_materiales': total_materiales,
            'restoration_successful': total_pedidos_compras > 0,
            'verification_rate': verificaciones_exitosas / len(verificaciones) if verificaciones else 0
        }
        
    except Exception as e:
        logger.error(f"Error en verificación: {str(e)}")
        conn.close()
        return False

def main():
    """Función principal"""
    print("RESTAURACION DE DATOS DE PEDIDOS_COMPRAS")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Ejecutar restauración
        logger.info("Iniciando restauración de pedidos_compras...")
        restoration_success = restore_pedidos_compras()
        
        if restoration_success:
            # Verificar restauración
            verification = verify_restoration()
            
            print("\n" + "="*60)
            print("RESUMEN DE RESTAURACION")
            print("="*60)
            print(f"Restauración exitosa: {verification['restoration_successful']}")
            print(f"Registros en 'pedidos': {verification['total_pedidos']}")
            print(f"Registros en 'pedidos_compras': {verification['total_pedidos_compras']}")
            print(f"Registros en 'compras_v2': {verification['total_compras_v2']}")
            print(f"Registros en 'compras_v2_materiales': {verification['total_materiales']}")
            print(f"Tasa de verificación: {verification['verification_rate']:.2%}")
            print("="*60)
            
            if verification['restoration_successful']:
                logger.info("RESTAURACION COMPLETADA EXITOSAMENTE!")
                logger.info("Los datos de pedidos_compras han sido restaurados")
                return True
            else:
                logger.error("La restauración no fue exitosa")
                return False
        else:
            logger.error("La restauración falló")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
