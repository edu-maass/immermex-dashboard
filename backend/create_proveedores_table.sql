-- Script para crear tabla de proveedores en Supabase
-- Ejecutar en el SQL Editor de Supabase

CREATE TABLE IF NOT EXISTS proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE,
    puerto_origen VARCHAR(255),
    dias_produccion_promedio INTEGER DEFAULT 30,
    dias_transporte_promedio INTEGER DEFAULT 21,
    pais VARCHAR(100),
    moneda_principal VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_proveedores_nombre ON proveedores(nombre);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_proveedores_updated_at 
    BEFORE UPDATE ON proveedores 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos de ejemplo (modificar según necesidades reales)
INSERT INTO proveedores (nombre, puerto_origen, dias_produccion_promedio, dias_transporte_promedio, pais, moneda_principal) 
VALUES 
    ('Proveedor Ejemplo 1', 'Shanghai, China', 30, 21, 'China', 'USD'),
    ('Proveedor Ejemplo 2', 'Hong Kong', 25, 18, 'China', 'USD'),
    ('Proveedor Ejemplo 3', 'Busan, South Korea', 28, 20, 'Corea del Sur', 'USD')
ON CONFLICT (nombre) DO NOTHING;

-- Comentarios de la tabla
COMMENT ON TABLE proveedores IS 'Catálogo de proveedores con datos de importación';
COMMENT ON COLUMN proveedores.puerto_origen IS 'Puerto de origen de las mercancías';
COMMENT ON COLUMN proveedores.dias_produccion_promedio IS 'Días promedio de producción para calcular fecha_salida_estimada';
COMMENT ON COLUMN proveedores.dias_transporte_promedio IS 'Días promedio de transporte para calcular fecha_arribo_estimada';

