-- Script SQL para actualizar fechas estimadas en compras_v2
-- Ejecutar en la base de datos de producción

-- 1. Agregar columna fecha_planta_estimada si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'compras_v2' 
        AND column_name = 'fecha_planta_estimada'
    ) THEN
        ALTER TABLE compras_v2 ADD COLUMN fecha_planta_estimada DATE;
        RAISE NOTICE 'Columna fecha_planta_estimada agregada';
    ELSE
        RAISE NOTICE 'Columna fecha_planta_estimada ya existe';
    END IF;
END $$;

-- 2. Actualizar fechas estimadas para todos los registros existentes
UPDATE compras_v2 
SET 
    fecha_salida_estimada = fecha_pedido + INTERVAL '1 day' * COALESCE(
        (SELECT promedio_dias_produccion FROM "Proveedores" WHERE "Nombre" = compras_v2.proveedor), 
        0
    ),
    fecha_arribo_estimada = fecha_pedido + INTERVAL '1 day' * COALESCE(
        (SELECT promedio_dias_produccion + promedio_dias_transporte_maritimo 
         FROM "Proveedores" WHERE "Nombre" = compras_v2.proveedor), 
        0
    ),
    fecha_planta_estimada = fecha_pedido + INTERVAL '1 day' * COALESCE(
        (SELECT promedio_dias_produccion + promedio_dias_transporte_maritimo + 15 
         FROM "Proveedores" WHERE "Nombre" = compras_v2.proveedor), 
        15
    ),
    updated_at = NOW()
WHERE fecha_pedido IS NOT NULL;

-- 3. Mostrar resumen de cambios
SELECT 
    COUNT(*) as total_registros,
    COUNT(CASE WHEN fecha_planta_estimada IS NOT NULL THEN 1 END) as con_fecha_planta,
    MIN(fecha_pedido) as fecha_pedido_minima,
    MAX(fecha_pedido) as fecha_pedido_maxima,
    MIN(fecha_planta_estimada) as fecha_planta_minima,
    MAX(fecha_planta_estimada) as fecha_planta_maxima
FROM compras_v2 
WHERE fecha_pedido IS NOT NULL;
