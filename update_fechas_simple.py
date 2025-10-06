#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simple para ejecutar en el servidor de producción
Actualiza las fechas estimadas de todos los registros existentes
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Obtiene conexión a la base de datos usando variables de entorno"""
    try:
        # Intentar conectar usando DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            conn = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor,
                sslmode='require',
                connect_timeout=30
            )
            return conn
        
        # Si no hay DATABASE_URL, intentar con variables individuales
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "postgres")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return None

def update_fechas_estimadas():
    """Actualiza las fechas estimadas para todos los registros existentes"""
    try:
        logger.info("Iniciando actualización de fechas estimadas...")
        
        conn = get_database_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos")
            return False
        
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
            logger.info("Agregando columna fecha_planta_estimada...")
            cursor.execute("""
                ALTER TABLE compras_v2 
                ADD COLUMN fecha_planta_estimada DATE
            """)
            conn.commit()
            logger.info("Columna fecha_planta_estimada agregada exitosamente")
        
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
            logger.info("No se encontraron registros para actualizar")
            cursor.close()
            conn.close()
            return True
        
        logger.info(f"Encontrados {len(records)} registros para procesar")
        
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
        
        logger.info(f"Datos de {len(proveedores_data)} proveedores cargados")
        
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
                
                logger.info(f"IMI {imi}: {fecha_pedido} -> Salida: {fecha_salida_estimada}, Arribo: {fecha_arribo_estimada}, Planta: {fecha_planta_estimada}")
            else:
                skipped_count += 1
        
        # Commit todos los cambios
        conn.commit()
        
        logger.info(f"Actualización completada:")
        logger.info(f"  - Registros actualizados: {updated_count}")
        logger.info(f"  - Registros sin cambios: {skipped_count}")
        logger.info(f"  - Total procesados: {len(records)}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando fechas estimadas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_fechas_estimadas()
    if success:
        print("Actualización completada exitosamente")
    else:
        print("Error en la actualización")
    sys.exit(0 if success else 1)
