"""
Función para calcular fecha_vencimiento en compras_v2
Se integra con el servicio existente para calcular automáticamente la fecha de vencimiento
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def calculate_fecha_vencimiento(fecha_salida_real, fecha_salida_estimada, dias_credito):
    """
    Calcula la fecha de vencimiento basada en la fecha de salida y días de crédito
    
    Args:
        fecha_salida_real: Fecha real de salida (prioridad alta)
        fecha_salida_estimada: Fecha estimada de salida (prioridad baja)
        dias_credito: Número de días de crédito
    
    Returns:
        datetime: Fecha de vencimiento calculada o None si no se puede calcular
    """
    try:
        # Validar días de crédito
        if not dias_credito or dias_credito <= 0:
            return None
        
        # Determinar qué fecha usar (prioridad: fecha_salida_real > fecha_salida_estimada)
        fecha_base = None
        
        if fecha_salida_real:
            fecha_base = fecha_salida_real
        elif fecha_salida_estimada:
            fecha_base = fecha_salida_estimada
        
        if not fecha_base:
            return None
        
        # Calcular fecha de vencimiento
        fecha_vencimiento = fecha_base + timedelta(days=dias_credito)
        
        logger.debug(f"Fecha vencimiento calculada: {fecha_base} + {dias_credito} días = {fecha_vencimiento}")
        
        return fecha_vencimiento
        
    except Exception as e:
        logger.error(f"Error calculando fecha_vencimiento: {str(e)}")
        return None

def add_fecha_vencimiento_to_compra(compra_data):
    """
    Agrega fecha_vencimiento calculada a los datos de una compra
    
    Args:
        compra_data: Diccionario con los datos de la compra
    
    Returns:
        dict: Datos de la compra con fecha_vencimiento agregada
    """
    try:
        # Extraer datos necesarios
        fecha_salida_real = compra_data.get('fecha_salida_real')
        fecha_salida_estimada = compra_data.get('fecha_salida_estimada')
        dias_credito = compra_data.get('dias_credito')
        
        # Calcular fecha de vencimiento
        fecha_vencimiento = calculate_fecha_vencimiento(
            fecha_salida_real, 
            fecha_salida_estimada, 
            dias_credito
        )
        
        # Agregar al diccionario de datos
        compra_data['fecha_vencimiento'] = fecha_vencimiento
        
        return compra_data
        
    except Exception as e:
        logger.error(f"Error agregando fecha_vencimiento a compra: {str(e)}")
        return compra_data

def update_existing_compras_with_fecha_vencimiento(conn):
    """
    Actualiza registros existentes en compras_v2 con fecha_vencimiento calculada
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        int: Número de registros actualizados
    """
    try:
        cursor = conn.cursor()
        
        # Obtener registros que necesitan actualización
        cursor.execute("""
            SELECT id, fecha_salida_real, fecha_salida_estimada, dias_credito
            FROM compras_v2
            WHERE (fecha_vencimiento IS NULL OR fecha_vencimiento = '1900-01-01')
            AND dias_credito IS NOT NULL AND dias_credito > 0
            AND (fecha_salida_real IS NOT NULL OR fecha_salida_estimada IS NOT NULL)
        """)
        
        records = cursor.fetchall()
        logger.info(f"Encontrados {len(records)} registros para actualizar con fecha_vencimiento")
        
        updated_count = 0
        
        for record in records:
            try:
                # Calcular fecha de vencimiento
                fecha_vencimiento = calculate_fecha_vencimiento(
                    record['fecha_salida_real'],
                    record['fecha_salida_estimada'],
                    record['dias_credito']
                )
                
                if fecha_vencimiento:
                    # Actualizar el registro
                    cursor.execute("""
                        UPDATE compras_v2 
                        SET fecha_vencimiento = %s
                        WHERE id = %s
                    """, (fecha_vencimiento, record['id']))
                    
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        logger.info(f"Progreso: {updated_count}/{len(records)} registros actualizados")
                        
            except Exception as e:
                logger.warning(f"Error actualizando registro {record['id']}: {str(e)}")
                continue
        
        conn.commit()
        logger.info(f"Actualización completada: {updated_count} registros actualizados")
        cursor.close()
        
        return updated_count
        
    except Exception as e:
        logger.error(f"Error actualizando registros existentes: {str(e)}")
        conn.rollback()
        return 0

def get_fecha_vencimiento_stats(conn):
    """
    Obtiene estadísticas sobre fecha_vencimiento en compras_v2
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        dict: Estadísticas de fecha_vencimiento
    """
    try:
        cursor = conn.cursor()
        
        # Contar registros con fecha_vencimiento
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(fecha_vencimiento) as con_fecha_vencimiento,
                COUNT(CASE WHEN fecha_vencimiento IS NOT NULL AND fecha_vencimiento != '1900-01-01' THEN 1 END) as fecha_vencimiento_valida,
                COUNT(CASE WHEN dias_credito IS NOT NULL AND dias_credito > 0 THEN 1 END) as con_dias_credito,
                COUNT(CASE WHEN fecha_salida_real IS NOT NULL THEN 1 END) as con_fecha_salida_real,
                COUNT(CASE WHEN fecha_salida_estimada IS NOT NULL THEN 1 END) as con_fecha_salida_estimada
            FROM compras_v2
        """)
        
        stats = cursor.fetchone()
        
        # Calcular porcentajes
        total = stats['total_registros']
        if total > 0:
            stats['porcentaje_con_fecha_vencimiento'] = round((stats['con_fecha_vencimiento'] / total) * 100, 2)
            stats['porcentaje_fecha_vencimiento_valida'] = round((stats['fecha_vencimiento_valida'] / total) * 100, 2)
        else:
            stats['porcentaje_con_fecha_vencimiento'] = 0
            stats['porcentaje_fecha_vencimiento_valida'] = 0
        
        cursor.close()
        
        return dict(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return {}

# Función de utilidad para mostrar estadísticas
def print_fecha_vencimiento_stats(stats):
    """Imprime estadísticas de fecha_vencimiento de forma legible"""
    print("\n=== ESTADÍSTICAS DE FECHA_VENCIMIENTO ===")
    print(f"Total registros: {stats.get('total_registros', 0)}")
    print(f"Con fecha_vencimiento: {stats.get('con_fecha_vencimiento', 0)} ({stats.get('porcentaje_con_fecha_vencimiento', 0)}%)")
    print(f"Fecha vencimiento válida: {stats.get('fecha_vencimiento_valida', 0)} ({stats.get('porcentaje_fecha_vencimiento_valida', 0)}%)")
    print(f"Con días de crédito: {stats.get('con_dias_credito', 0)}")
    print(f"Con fecha salida real: {stats.get('con_fecha_salida_real', 0)}")
    print(f"Con fecha salida estimada: {stats.get('con_fecha_salida_estimada', 0)}")
    print("=" * 50)

