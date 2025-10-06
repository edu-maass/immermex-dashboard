#!/usr/bin/env python3
"""
Script simplificado para calcular el promedio de días de producción por proveedor
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Función principal del script"""
    # Configurar URL de base de datos
    DATABASE_URL = 'postgresql://postgres.ldxahcawfrvlmdiwapli:Database_Immermex@aws-1-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        # Crear engine
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
        
        logger.info("Conectando a la base de datos...")
        
        # Consulta para calcular días de producción por proveedor
        calculation_sql = """
            SELECT 
                proveedor,
                COUNT(*) as total_registros,
                AVG(
                    CASE 
                        WHEN fecha_salida_puerto IS NOT NULL AND fecha_compra IS NOT NULL 
                        THEN EXTRACT(DAYS FROM (fecha_salida_puerto - fecha_compra))
                        ELSE NULL 
                    END
                ) as promedio_dias_produccion,
                MIN(fecha_compra) as primera_compra,
                MAX(fecha_compra) as ultima_compra
            FROM compras 
            WHERE proveedor IS NOT NULL 
                AND proveedor != ''
                AND fecha_salida_puerto IS NOT NULL 
                AND fecha_compra IS NOT NULL
                AND fecha_salida_puerto >= fecha_compra
            GROUP BY proveedor
            ORDER BY promedio_dias_produccion DESC
        """
        
        logger.info("Calculando promedios de días de producción...")
        
        with engine.connect() as conn:
            result = conn.execute(text(calculation_sql))
            averages = result.fetchall()
        
        if not averages:
            logger.warning("No se encontraron registros válidos para calcular promedios")
            return
        
        logger.info(f"Se encontraron {len(averages)} proveedores con datos válidos")
        
        # Mostrar resultados
        logger.info("Resultados del cálculo:")
        logger.info("-" * 80)
        for row in averages:
            proveedor, total_registros, promedio, primera_compra, ultima_compra = row
            logger.info(f"Proveedor: {proveedor}")
            logger.info(f"  - Total registros: {total_registros}")
            logger.info(f"  - Promedio días producción: {promedio:.2f}")
            logger.info(f"  - Primera compra: {primera_compra}")
            logger.info(f"  - Última compra: {ultima_compra}")
            logger.info("-" * 40)
        
        # Actualizar tabla Proveedores
        logger.info("Actualizando tabla Proveedores...")
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                updated_count = 0
                
                for row in averages:
                    proveedor, total_registros, promedio, primera_compra, ultima_compra = row
                    
                    if promedio is not None:
                        # Actualizar o insertar en la tabla Proveedores
                        update_sql = """
                            INSERT INTO "Proveedores" ("Nombre", promedio_dias_produccion, created_at)
                            VALUES (:nombre, :promedio, CURRENT_TIMESTAMP)
                            ON CONFLICT ("Nombre") 
                            DO UPDATE SET 
                                promedio_dias_produccion = EXCLUDED.promedio_dias_produccion
                        """
                        
                        conn.execute(text(update_sql), {
                            "nombre": proveedor,
                            "promedio": round(promedio, 2)
                        })
                        updated_count += 1
                        logger.info(f"Actualizado proveedor: {proveedor} con promedio: {promedio:.2f} días")
                
                trans.commit()
                logger.info(f"Se actualizaron {updated_count} proveedores exitosamente")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error actualizando tabla Proveedores: {str(e)}")
                return
        
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
        
        logger.info("Proceso completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error en el proceso: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
