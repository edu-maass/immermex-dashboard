-- SQL para agregar columnas dias_transporte y dias_puerto_planta a compras_v2
-- Ejecutar en el SQL Editor de Supabase

-- Agregar columna dias_transporte (días entre fecha_salida_real y fecha_arribo_real)
ALTER TABLE compras_v2 
ADD COLUMN IF NOT EXISTS dias_transporte INTEGER;

-- Agregar columna dias_puerto_planta (días entre fecha_arribo_real y fecha_planta_real)
ALTER TABLE compras_v2 
ADD COLUMN IF NOT EXISTS dias_puerto_planta INTEGER;

-- Calcular valores existentes para registros que ya tienen las fechas
UPDATE compras_v2 
SET dias_transporte = (fecha_arribo_real - fecha_salida_real)
WHERE fecha_salida_real IS NOT NULL 
  AND fecha_arribo_real IS NOT NULL;

UPDATE compras_v2 
SET dias_puerto_planta = (fecha_planta_real - fecha_arribo_real)
WHERE fecha_arribo_real IS NOT NULL 
  AND fecha_planta_real IS NOT NULL;

-- Crear índices para mejorar el rendimiento de consultas
CREATE INDEX IF NOT EXISTS idx_compras_v2_dias_transporte ON compras_v2(dias_transporte);
CREATE INDEX IF NOT EXISTS idx_compras_v2_dias_puerto_planta ON compras_v2(dias_puerto_planta);

-- Comentarios para documentación
COMMENT ON COLUMN compras_v2.dias_transporte IS 'Días entre fecha_salida_real y fecha_arribo_real. NULL si alguna fecha no está disponible';
COMMENT ON COLUMN compras_v2.dias_puerto_planta IS 'Días entre fecha_arribo_real y fecha_planta_real. NULL si alguna fecha no está disponible';

