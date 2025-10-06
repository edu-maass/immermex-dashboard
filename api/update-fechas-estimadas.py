"""
Función Vercel para actualizar fechas estimadas
Archivo: api/update-fechas-estimadas.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

def handler(request):
    """Función principal para actualizar fechas estimadas"""
    try:
        # Obtener conexión a la base de datos
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'DATABASE_URL no configurada'})
            }
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode='require',
            connect_timeout=30
        )
        
        cursor = conn.cursor()
        
        # Verificar si la columna fecha_planta_estimada existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2' 
            AND column_name = 'fecha_planta_estimada'
        """)
        
        column_exists = cursor.fetchone()
        
        if not column_exists:
            cursor.execute("""
                ALTER TABLE compras_v2 
                ADD COLUMN fecha_planta_estimada DATE
            """)
            conn.commit()
        
        # Obtener todos los registros que necesitan actualización
        cursor.execute("""
            SELECT 
                imi, 
                proveedor, 
                fecha_pedido,
                fecha_salida_estimada,
                fecha_arribo_estimada,
                fecha_planta_estimada
            FROM compras_v2 
            WHERE fecha_pedido IS NOT NULL
            ORDER BY imi
        """)
        
        records = cursor.fetchall()
        
        if not records:
            cursor.close()
            conn.close()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No se encontraron registros para actualizar',
                    'updated': 0,
                    'skipped': 0
                })
            }
        
        # Obtener datos de proveedores para cálculos
        cursor.execute("""
            SELECT 
                "Nombre",
                promedio_dias_produccion,
                promedio_dias_transporte_maritimo
            FROM "Proveedores"
        """)
        
        proveedores_data = {}
        for row in cursor.fetchall():
            proveedores_data[row['Nombre']] = {
                'promedio_dias_produccion': float(row['promedio_dias_produccion'] or 0.0),
                'promedio_dias_transporte_maritimo': float(row['promedio_dias_transporte_maritimo'] or 0.0)
            }
        
        # Procesar cada registro
        updated_count = 0
        skipped_count = 0
        
        for record in records:
            imi = record['imi']
            proveedor = record['proveedor']
            fecha_pedido = record['fecha_pedido']
            fecha_salida_actual = record['fecha_salida_estimada']
            fecha_arribo_actual = record['fecha_arribo_estimada']
            fecha_planta_actual = record['fecha_planta_estimada']
            
            # Obtener datos del proveedor
            proveedor_data = proveedores_data.get(proveedor, {
                'promedio_dias_produccion': 0.0,
                'promedio_dias_transporte_maritimo': 0.0
            })
            
            # Calcular fechas estimadas
            fecha_salida_estimada = fecha_pedido + timedelta(days=proveedor_data['promedio_dias_produccion'])
            fecha_arribo_estimada = fecha_salida_estimada + timedelta(days=proveedor_data['promedio_dias_transporte_maritimo'])
            fecha_planta_estimada = fecha_arribo_estimada + timedelta(days=15)
            
            # Verificar si necesita actualización
            needs_update = False
            update_fields = []
            update_values = []
            
            if fecha_salida_actual != fecha_salida_estimada:
                update_fields.append("fecha_salida_estimada = %s")
                update_values.append(fecha_salida_estimada)
                needs_update = True
            
            if fecha_arribo_actual != fecha_arribo_estimada:
                update_fields.append("fecha_arribo_estimada = %s")
                update_values.append(fecha_arribo_estimada)
                needs_update = True
            
            if fecha_planta_actual != fecha_planta_estimada:
                update_fields.append("fecha_planta_estimada = %s")
                update_values.append(fecha_planta_estimada)
                needs_update = True
            
            if needs_update:
                # Siempre actualizar timestamp
                update_fields.append("updated_at = %s")
                update_values.append(datetime.utcnow())
                
                # Agregar IMI para WHERE
                update_values.append(imi)
                
                # Ejecutar actualización
                update_query = f"""
                    UPDATE compras_v2 SET
                        {', '.join(update_fields)}
                    WHERE imi = %s
                """
                
                cursor.execute(update_query, update_values)
                updated_count += 1
            else:
                skipped_count += 1
        
        # Commit todos los cambios
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Actualización de fechas estimadas completada',
                'total_records': len(records),
                'updated': updated_count,
                'skipped': skipped_count,
                'proveedores_loaded': len(proveedores_data)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
