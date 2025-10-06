#!/usr/bin/env python3
"""
Script para calcular promedios reales de días de producción desde el Excel
y actualizar la tabla Proveedores en PostgreSQL
"""

import pandas as pd
import os
import sys
import logging
from sqlalchemy import create_engine, text
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_excel_and_calculate():
    """Analiza el Excel y calcula los promedios reales"""
    
    excel_file = "docs/IMM-Compras de  importacion (Compartido).xlsx"
    
    if not os.path.exists(excel_file):
        logger.error(f"Archivo no encontrado: {excel_file}")
        return None
    
    try:
        logger.info(f"Analizando archivo: {excel_file}")
        
        # Leer la pestaña "Resumen Compras"
        df = pd.read_excel(excel_file, sheet_name="Resumen Compras")
        
        logger.info(f"Archivo cargado exitosamente. Dimensiones: {df.shape}")
        
        # Identificar las columnas correctas
        fecha_pedido_col = "Fecha Pedido"
        fecha_bl_col = "Fecha Salida Puerto Origen (ETD/BL)"
        proveedor_col = "Proveedor"
        
        logger.info(f"Usando columnas:")
        logger.info(f"  - Fecha Pedido: {fecha_pedido_col}")
        logger.info(f"  - Fecha BL: {fecha_bl_col}")
        logger.info(f"  - Proveedor: {proveedor_col}")
        
        # Convertir fechas a datetime
        df[fecha_pedido_col] = pd.to_datetime(df[fecha_pedido_col], errors='coerce')
        df[fecha_bl_col] = pd.to_datetime(df[fecha_bl_col], errors='coerce')
        
        # Filtrar datos válidos
        valid_data = df[
            (df[fecha_pedido_col].notna()) & 
            (df[fecha_bl_col].notna()) & 
            (df[proveedor_col].notna()) &
            (df[proveedor_col] != '') &
            (df[fecha_bl_col] >= df[fecha_pedido_col])  # BL debe ser posterior al pedido
        ].copy()
        
        logger.info(f"Registros válidos encontrados: {len(valid_data)}")
        
        if len(valid_data) == 0:
            logger.warning("No hay registros válidos para calcular días de producción")
            return None
        
        # Calcular días de producción
        valid_data['dias_produccion'] = (valid_data[fecha_bl_col] - valid_data[fecha_pedido_col]).dt.days
        
        # Filtrar valores muy altos (posibles errores)
        valid_data = valid_data[
            (valid_data['dias_produccion'] >= 0) & 
            (valid_data['dias_produccion'] <= 180)  # Máximo 6 meses
        ]
        
        logger.info(f"Registros después de filtrar valores inválidos: {len(valid_data)}")
        
        # Calcular promedios por proveedor
        promedios = valid_data.groupby(proveedor_col)['dias_produccion'].agg([
            'count', 'mean', 'min', 'max', 'std'
        ]).round(2)
        
        promedios.columns = ['total_registros', 'promedio_dias', 'min_dias', 'max_dias', 'desviacion']
        promedios = promedios.sort_values('promedio_dias', ascending=False)
        
        logger.info(f"\nPromedios de días de producción por proveedor:")
        logger.info(promedios.to_string())
        
        return promedios
        
    except Exception as e:
        logger.error(f"Error analizando Excel: {str(e)}")
        return None

def update_proveedores_database(promedios):
    """Actualiza la tabla Proveedores con los promedios calculados"""
    
    DATABASE_URL = 'postgresql://postgres.ldxahcawfrvlmdiwapli:Database_Immermex@aws-1-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
            connect_args={
                "sslmode": "require"
            }
        )
        
        logger.info("Conectando a la base de datos PostgreSQL...")
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                updated_count = 0
                
                for proveedor, row in promedios.iterrows():
                    promedio_dias = int(row['promedio_dias'])
                    total_registros = int(row['total_registros'])
                    
                    logger.info(f"Actualizando {proveedor}: {promedio_dias} días (basado en {total_registros} registros)")
                    
                    # Insertar o actualizar en la tabla Proveedores
                    # Usar UPSERT sin ON CONFLICT ya que no hay restricción única
                    update_sql = """
                        UPDATE "Proveedores" 
                        SET promedio_dias_produccion = :promedio
                        WHERE "Nombre" = :nombre;
                        
                        INSERT INTO "Proveedores" ("Nombre", promedio_dias_produccion, created_at)
                        SELECT :nombre, :promedio, CURRENT_TIMESTAMP
                        WHERE NOT EXISTS (SELECT 1 FROM "Proveedores" WHERE "Nombre" = :nombre);
                    """
                    
                    conn.execute(text(update_sql), {
                        "nombre": proveedor,
                        "promedio": promedio_dias
                    })
                    updated_count += 1
                
                trans.commit()
                logger.info(f"Se actualizaron {updated_count} proveedores exitosamente")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error actualizando tabla Proveedores: {str(e)}")
                return False
        
        # Verificar actualizaciones
        logger.info("Verificando actualizaciones...")
        
        with engine.connect() as conn:
            verify_sql = """
                SELECT "Nombre", promedio_dias_produccion, created_at
                FROM "Proveedores" 
                WHERE promedio_dias_produccion IS NOT NULL 
                    AND promedio_dias_produccion > 0
                ORDER BY promedio_dias_produccion DESC
            """
            
            result = conn.execute(text(verify_sql))
            updated_proveedores = result.fetchall()
            
            logger.info(f"Verificación: {len(updated_proveedores)} proveedores tienen promedios actualizados")
            
            for row in updated_proveedores:
                nombre, promedio, created_at = row
                logger.info(f"  - {nombre}: {promedio} días")
        
        return True
        
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando cálculo de promedios reales desde Excel...")
    
    # Analizar Excel y calcular promedios
    promedios = analyze_excel_and_calculate()
    
    if promedios is not None and len(promedios) > 0:
        logger.info("Promedios calculados exitosamente desde el Excel")
        
        # Actualizar base de datos
        if update_proveedores_database(promedios):
            logger.info("Base de datos actualizada exitosamente")
            logger.info("Los promedios de días de producción ahora están basados en datos reales del Excel")
        else:
            logger.error("Error actualizando la base de datos")
            sys.exit(1)
    else:
        logger.error("No se pudieron calcular los promedios desde el Excel")
        sys.exit(1)
    
    logger.info("Proceso completado exitosamente")

if __name__ == "__main__":
    main()
