"""
Script para crear la tabla de compras en Supabase
Ejecuta el SQL de creación de tablas y configuración inicial
"""

import asyncio
import logging
import os
import sys
from database_service_refactored import DatabaseService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_compras_table():
    """Crea la tabla de compras y tablas relacionadas en Supabase"""
    try:
        db_service = DatabaseService()
        
        # SQL para crear tabla de compras
        create_compras_sql = """
        -- Crear tabla de compras
        CREATE TABLE IF NOT EXISTS compras (
            id SERIAL PRIMARY KEY,
            fecha_compra DATE,
            numero_factura VARCHAR(100),
            proveedor VARCHAR(255),
            concepto VARCHAR(500),
            categoria VARCHAR(100),
            subcategoria VARCHAR(100),
            cantidad DECIMAL(15,4) DEFAULT 0,
            unidad VARCHAR(50),
            precio_unitario DECIMAL(15,4) DEFAULT 0,
            subtotal DECIMAL(15,2) DEFAULT 0,
            iva DECIMAL(15,2) DEFAULT 0,
            total DECIMAL(15,2) DEFAULT 0,
            moneda VARCHAR(10) DEFAULT 'MXN',
            tipo_cambio DECIMAL(10,4) DEFAULT 1.0,
            forma_pago VARCHAR(100),
            dias_credito INTEGER DEFAULT 0,
            fecha_vencimiento DATE,
            fecha_pago DATE,
            estado_pago VARCHAR(50) DEFAULT 'pendiente',
            centro_costo VARCHAR(100),
            proyecto VARCHAR(100),
            notas TEXT,
            archivo_origen VARCHAR(255),
            archivo_id INTEGER REFERENCES archivos_procesados(id),
            mes INTEGER,
            año INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # SQL para crear tabla de categorías
        create_categorias_sql = """
        -- Crear tabla de categorías de compras
        CREATE TABLE IF NOT EXISTS categorias_compras (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            descripcion TEXT,
            activa BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # SQL para insertar categorías básicas
        insert_categorias_sql = """
        INSERT INTO categorias_compras (nombre, descripcion) VALUES 
            ('Materias Primas', 'Materiales utilizados en la producción'),
            ('Servicios', 'Servicios contratados'),
            ('Equipos y Maquinaria', 'Equipos y maquinaria para producción'),
            ('Mantenimiento', 'Servicios de mantenimiento'),
            ('Administrativos', 'Gastos administrativos'),
            ('Marketing', 'Gastos de marketing y publicidad'),
            ('Capacitación', 'Cursos y capacitaciones'),
            ('Otros', 'Otros gastos no categorizados')
        ON CONFLICT (nombre) DO NOTHING;
        """
        
        # SQL para crear índices
        create_indexes_sql = """
        -- Crear índices para mejorar rendimiento
        CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha_compra);
        CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON compras(proveedor);
        CREATE INDEX IF NOT EXISTS idx_compras_categoria ON compras(categoria);
        CREATE INDEX IF NOT EXISTS idx_compras_archivo ON compras(archivo_id);
        CREATE INDEX IF NOT EXISTS idx_compras_mes_año ON compras(mes, año);
        CREATE INDEX IF NOT EXISTS idx_compras_estado_pago ON compras(estado_pago);
        CREATE INDEX IF NOT EXISTS idx_compras_fecha_vencimiento ON compras(fecha_vencimiento);
        """
        
        # SQL para crear función de estado de pago
        create_function_sql = """
        -- Crear función para calcular estado de pago automáticamente
        CREATE OR REPLACE FUNCTION calcular_estado_pago()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Si tiene fecha de pago, está pagado
            IF NEW.fecha_pago IS NOT NULL THEN
                NEW.estado_pago = 'pagado';
            -- Si tiene fecha de vencimiento y ya pasó, está vencido
            ELSIF NEW.fecha_vencimiento IS NOT NULL AND NEW.fecha_vencimiento < CURRENT_DATE THEN
                NEW.estado_pago = 'vencido';
            -- Si no tiene fecha de pago pero tiene fecha de vencimiento futura, está pendiente
            ELSIF NEW.fecha_vencimiento IS NOT NULL AND NEW.fecha_vencimiento >= CURRENT_DATE THEN
                NEW.estado_pago = 'pendiente';
            ELSE
                NEW.estado_pago = 'pendiente';
            END IF;
            
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        
        # SQL para crear triggers
        create_triggers_sql = """
        -- Crear trigger para calcular estado de pago automáticamente
        DROP TRIGGER IF EXISTS calcular_estado_pago_trigger ON compras;
        CREATE TRIGGER calcular_estado_pago_trigger
            BEFORE INSERT OR UPDATE ON compras
            FOR EACH ROW
            EXECUTE FUNCTION calcular_estado_pago();
        
        -- Crear trigger para actualizar updated_at
        DROP TRIGGER IF EXISTS update_compras_updated_at ON compras;
        CREATE TRIGGER update_compras_updated_at 
            BEFORE UPDATE ON compras 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        # SQL para crear vistas
        create_views_sql = """
        -- Crear vista para resumen de compras por mes
        CREATE OR REPLACE VIEW resumen_compras_mensual AS
        SELECT 
            mes,
            año,
            COUNT(*) as total_compras,
            SUM(total) as total_monto,
            SUM(CASE WHEN estado_pago = 'pagado' THEN total ELSE 0 END) as monto_pagado,
            SUM(CASE WHEN estado_pago = 'pendiente' THEN total ELSE 0 END) as monto_pendiente,
            SUM(CASE WHEN estado_pago = 'vencido' THEN total ELSE 0 END) as monto_vencido,
            COUNT(CASE WHEN estado_pago = 'pagado' THEN 1 END) as compras_pagadas,
            COUNT(CASE WHEN estado_pago = 'pendiente' THEN 1 END) as compras_pendientes,
            COUNT(CASE WHEN estado_pago = 'vencido' THEN 1 END) as compras_vencidas
        FROM compras
        GROUP BY mes, año
        ORDER BY año DESC, mes DESC;
        
        -- Crear vista para resumen por proveedor
        CREATE OR REPLACE VIEW resumen_compras_proveedor AS
        SELECT 
            proveedor,
            COUNT(*) as total_compras,
            SUM(total) as total_monto,
            AVG(total) as promedio_compra,
            MAX(fecha_compra) as ultima_compra,
            COUNT(CASE WHEN estado_pago = 'vencido' THEN 1 END) as compras_vencidas
        FROM compras
        GROUP BY proveedor
        ORDER BY total_monto DESC;
        """
        
        logger.info("Creando tabla de compras...")
        await db_service.execute_query(create_compras_sql)
        logger.info("✓ Tabla de compras creada")
        
        logger.info("Creando tabla de categorías...")
        await db_service.execute_query(create_categorias_sql)
        logger.info("✓ Tabla de categorías creada")
        
        logger.info("Insertando categorías básicas...")
        await db_service.execute_query(insert_categorias_sql)
        logger.info("✓ Categorías básicas insertadas")
        
        logger.info("Creando índices...")
        await db_service.execute_query(create_indexes_sql)
        logger.info("✓ Índices creados")
        
        logger.info("Creando función de estado de pago...")
        await db_service.execute_query(create_function_sql)
        logger.info("✓ Función creada")
        
        logger.info("Creando triggers...")
        await db_service.execute_query(create_triggers_sql)
        logger.info("✓ Triggers creados")
        
        logger.info("Creando vistas...")
        await db_service.execute_query(create_views_sql)
        logger.info("✓ Vistas creadas")
        
        logger.info("="*60)
        logger.info("✓ TABLA DE COMPRAS CREADA EXITOSAMENTE")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando tabla de compras: {e}")
        return False

async def verify_table_creation():
    """Verifica que la tabla se creó correctamente"""
    try:
        db_service = DatabaseService()
        
        # Verificar que la tabla existe
        check_table_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'compras'
        """
        
        result = await db_service.execute_query(check_table_sql)
        
        if result:
            logger.info("✓ Tabla 'compras' existe en la base de datos")
            
            # Verificar estructura de la tabla
            check_columns_sql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'compras'
            ORDER BY ordinal_position
            """
            
            columns = await db_service.execute_query(check_columns_sql)
            logger.info(f"✓ Tabla tiene {len(columns)} columnas")
            
            # Verificar categorías
            check_categorias_sql = "SELECT COUNT(*) as total FROM categorias_compras"
            categorias_result = await db_service.execute_query(check_categorias_sql)
            logger.info(f"✓ {categorias_result[0]['total']} categorías creadas")
            
            return True
        else:
            logger.error("❌ Tabla 'compras' no encontrada")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando tabla: {e}")
        return False

async def main():
    """Función principal"""
    logger.info("="*60)
    logger.info("CREACIÓN DE TABLA DE COMPRAS EN SUPABASE")
    logger.info("="*60)
    
    # Verificar conexión a base de datos
    try:
        db_service = DatabaseService()
        test_result = await db_service.execute_query("SELECT 1 as test")
        logger.info("✓ Conexión a Supabase establecida")
    except Exception as e:
        logger.error(f"❌ Error conectando a Supabase: {e}")
        return False
    
    # Crear tabla
    success = await create_compras_table()
    
    if success:
        # Verificar creación
        verify_success = await verify_table_creation()
        
        if verify_success:
            logger.info("="*60)
            logger.info("✓ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("="*60)
            logger.info("La tabla de compras está lista para usar.")
            logger.info("Puedes comenzar a importar datos desde OneDrive.")
            return True
    
    logger.error("❌ Error en la configuración")
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
