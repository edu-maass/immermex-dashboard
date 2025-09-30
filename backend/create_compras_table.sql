-- Script para crear tabla de compras en Supabase
-- Ejecutar en el SQL Editor de Supabase

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
    estado_pago VARCHAR(50) DEFAULT 'pendiente', -- pendiente, pagado, vencido
    centro_costo VARCHAR(100),
    proyecto VARCHAR(100),
    notas TEXT,
    archivo_origen VARCHAR(255), -- Nombre del archivo de OneDrive
    archivo_id INTEGER REFERENCES archivos_procesados(id),
    mes INTEGER,
    año INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de categorías de compras (opcional, para mejor organización)
CREATE TABLE IF NOT EXISTS categorias_compras (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    activa BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar categorías básicas
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

-- Crear índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha_compra);
CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON compras(proveedor);
CREATE INDEX IF NOT EXISTS idx_compras_categoria ON compras(categoria);
CREATE INDEX IF NOT EXISTS idx_compras_archivo ON compras(archivo_id);
CREATE INDEX IF NOT EXISTS idx_compras_mes_año ON compras(mes, año);
CREATE INDEX IF NOT EXISTS idx_compras_estado_pago ON compras(estado_pago);
CREATE INDEX IF NOT EXISTS idx_compras_fecha_vencimiento ON compras(fecha_vencimiento);

-- Crear trigger para actualizar updated_at
CREATE TRIGGER update_compras_updated_at 
    BEFORE UPDATE ON compras 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

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

-- Crear trigger para calcular estado de pago automáticamente
CREATE TRIGGER calcular_estado_pago_trigger
    BEFORE INSERT OR UPDATE ON compras
    FOR EACH ROW
    EXECUTE FUNCTION calcular_estado_pago();

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
