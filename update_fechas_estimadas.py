#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.compras_v2_service import ComprasV2Service
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

def update_existing_fechas_estimadas():
    """Actualiza las fechas estimadas para todos los registros existentes en compras_v2"""
    try:
        print("Iniciando actualización de fechas estimadas para registros existentes...")
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            print("No se pudo conectar a la base de datos")
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
            print("Agregando columna fecha_planta_estimada...")
            cursor.execute("""
                ALTER TABLE compras_v2 
                ADD COLUMN fecha_planta_estimada DATE
            """)
            conn.commit()
            print("Columna fecha_planta_estimada agregada exitosamente")
        
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
            print("No se encontraron registros para actualizar")
            cursor.close()
            conn.close()
            return True
        
        print(f"Encontrados {len(records)} registros para procesar")
        
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
            proveedores_data[row[0]] = {
                'promedio_dias_produccion': float(row[1] or 0.0),
                'promedio_dias_transporte_maritimo': float(row[2] or 0.0)
            }
        
        print(f"Datos de {len(proveedores_data)} proveedores cargados")
        
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
                
                print(f"IMI {imi}: {fecha_pedido} -> Salida: {fecha_salida_estimada}, Arribo: {fecha_arribo_estimada}, Planta: {fecha_planta_estimada}")
            else:
                skipped_count += 1
        
        # Commit todos los cambios
        conn.commit()
        
        print(f"\nActualización completada:")
        print(f"  - Registros actualizados: {updated_count}")
        print(f"  - Registros sin cambios: {skipped_count}")
        print(f"  - Total procesados: {len(records)}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error actualizando fechas estimadas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def preview_changes():
    """Muestra un preview de los cambios que se realizarán sin hacer actualizaciones"""
    try:
        print("Generando preview de cambios...")
        
        service = ComprasV2Service()
        conn = service.get_connection()
        
        if not conn:
            print("No se pudo conectar a la base de datos")
            return False
        
        cursor = conn.cursor()
        
        # Obtener algunos registros de ejemplo
        cursor.execute("""
            SELECT 
                imi, 
                proveedor, 
                fecha_pedido,
                fecha_salida_estimada,
                fecha_arribo_estimada
            FROM compras_v2 
            WHERE fecha_pedido IS NOT NULL
            ORDER BY imi
            LIMIT 10
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("No se encontraron registros para mostrar")
            cursor.close()
            conn.close()
            return True
        
        # Obtener datos de proveedores
        cursor.execute("""
            SELECT 
                "Nombre",
                promedio_dias_produccion,
                promedio_dias_transporte_maritimo
            FROM "Proveedores"
        """)
        
        proveedores_data = {}
        for row in cursor.fetchall():
            proveedores_data[row[0]] = {
                'promedio_dias_produccion': float(row[1] or 0.0),
                'promedio_dias_transporte_maritimo': float(row[2] or 0.0)
            }
        
        print(f"\nPreview de cambios (primeros 10 registros):")
        print("=" * 80)
        print(f"{'IMI':<8} | {'Proveedor':<20} | {'Fecha Pedido':<12} | {'Nueva Fecha Planta':<15}")
        print("-" * 80)
        
        for record in records:
            imi = record['imi']
            proveedor = record['proveedor']
            fecha_pedido = record['fecha_pedido']
            
            proveedor_data = proveedores_data.get(proveedor, {
                'promedio_dias_produccion': 0.0,
                'promedio_dias_transporte_maritimo': 0.0
            })
            
            fecha_salida_estimada = fecha_pedido + timedelta(days=proveedor_data['promedio_dias_produccion'])
            fecha_arribo_estimada = fecha_salida_estimada + timedelta(days=proveedor_data['promedio_dias_transporte_maritimo'])
            fecha_planta_estimada = fecha_arribo_estimada + timedelta(days=15)
            
            print(f"{imi:<8} | {proveedor:<20} | {fecha_pedido:<12} | {fecha_planta_estimada:<15}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error generando preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        success = preview_changes()
    else:
        print("Este script actualizará las fechas estimadas para todos los registros existentes.")
        print("Use --preview para ver los cambios antes de ejecutar.")
        print("¿Continuar? (y/N): ", end="")
        
        response = input().strip().lower()
        if response in ['y', 'yes', 'sí', 'si']:
            success = update_existing_fechas_estimadas()
        else:
            print("Operación cancelada")
            success = True
    
    if success:
        print("\nOperación completada exitosamente")
    else:
        print("\nError en la operación")
    sys.exit(0 if success else 1)
