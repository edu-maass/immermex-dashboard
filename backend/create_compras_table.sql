-- Script para crear la tabla de compras en Supabase
-- Ejecutar este script en el SQL Editor de Supabase

-- Crear tabla de compras
CREATE TABLE IF NOT EXISTS compras (
    id SERIAL PRIMARY KEY,
    fecha_compra DATE NOT NULL,
    numero_factura VARCHAR(255),
    proveedor VARCHAR(255) NOT NULL,
    concepto TEXT,
    categoria VARCHAR(100),
    subcategoria VARCHAR(100),
    cantidad DECIMAL(15,4) DEFAULT 0,
    unidad VARCHAR(50) DEFAULT 'KG',
    precio_unitario DECIMAL(15,4) DEFAULT 0,
    subtotal DECIMAL(15,2) DEFAULT 0,
    iva DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) DEFAULT 0,
    moneda VARCHAR(10) DEFAULT 'USD',
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
    
    -- Campos específicos de importación
    imi VARCHAR(100),
    puerto_origen VARCHAR(100),
    fecha_salida_puerto DATE,
    fecha_arribo_puerto DATE,
    fecha_entrada_inmermex DATE,
    precio_dlls DECIMAL(15,4),
    xr DECIMAL(10,4),
    financiera VARCHAR(100),
    porcentaje_anticipo DECIMAL(5,2),
    fecha_anticipo DATE,
    anticipo_dlls DECIMAL(15,2),
    tipo_cambio_anticipo DECIMAL(10,4),
    pago_factura_dlls DECIMAL(15,2),
    tipo_cambio_factura DECIMAL(10,4),
    pu_mxn DECIMAL(15,4),
    precio_mxn DECIMAL(15,2),
    porcentaje_imi DECIMAL(5,4),
    fecha_entrada_aduana DATE,
    pedimento VARCHAR(100),
    gastos_aduanales DECIMAL(15,2),
    costo_total DECIMAL(15,2),
    porcentaje_gastos_aduanales DECIMAL(5,4),
    pu_total DECIMAL(15,4),
    fecha_pago_impuestos DATE,
    fecha_salida_aduana DATE,
    dias_en_puerto INTEGER,
    agente VARCHAR(255),
    fac_agente VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha_compra);
CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON compras(proveedor);
CREATE INDEX IF NOT EXISTS idx_compras_archivo ON compras(archivo_id);
CREATE INDEX IF NOT EXISTS idx_compras_mes_año ON compras(mes, año);
CREATE INDEX IF NOT EXISTS idx_compras_estado_pago ON compras(estado_pago);
CREATE INDEX IF NOT EXISTS idx_compras_numero_factura ON compras(numero_factura);

-- Crear trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_compras_updated_at 
    BEFORE UPDATE ON compras 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios en la tabla
COMMENT ON TABLE compras IS 'Tabla para almacenar datos de compras e importaciones';
COMMENT ON COLUMN compras.imi IS 'Identificador del material importado';
COMMENT ON COLUMN compras.puerto_origen IS 'Puerto de origen de la importación';
COMMENT ON COLUMN compras.pedimento IS 'Número de pedimento aduanal';
COMMENT ON COLUMN compras.gastos_aduanales IS 'Gastos asociados a la importación';
COMMENT ON COLUMN compras.agente IS 'Agente aduanal responsable';
