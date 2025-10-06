-- Script SQL para agregar columnas a la tabla proveedores existente
-- Agrega las columnas:
-- - promedio_dias_produccion
-- - promedio_dias_transporte_maritimo

-- Verificar si las columnas ya existen antes de agregarlas
DO $$
BEGIN
    -- Agregar columna promedio_dias_produccion si no existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'proveedores' 
        AND column_name = 'promedio_dias_produccion'
    ) THEN
        ALTER TABLE proveedores 
        ADD COLUMN promedio_dias_produccion DECIMAL(10,2) DEFAULT 0.0;
        
        RAISE NOTICE 'Columna promedio_dias_produccion agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna promedio_dias_produccion ya existe, omitiendo';
    END IF;

    -- Agregar columna promedio_dias_transporte_maritimo si no existe
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'proveedores' 
        AND column_name = 'promedio_dias_transporte_maritimo'
    ) THEN
        ALTER TABLE proveedores 
        ADD COLUMN promedio_dias_transporte_maritimo DECIMAL(10,2) DEFAULT 0.0;
        
        RAISE NOTICE 'Columna promedio_dias_transporte_maritimo agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna promedio_dias_transporte_maritimo ya existe, omitiendo';
    END IF;
END $$;

-- Verificar que las columnas se agregaron correctamente
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'proveedores' 
AND column_name IN ('promedio_dias_produccion', 'promedio_dias_transporte_maritimo')
ORDER BY column_name;
