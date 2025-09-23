-- Script para crear tablas en Supabase
-- Ejecutar en el SQL Editor de Supabase

-- Crear tabla de archivos procesados
CREATE TABLE IF NOT EXISTS archivos_procesados (
    id SERIAL PRIMARY KEY,
    nombre_archivo VARCHAR(255) NOT NULL UNIQUE,
    fecha_procesamiento TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    registros_procesados INTEGER DEFAULT 0,
    estado VARCHAR(50) DEFAULT 'procesado',
    error_message TEXT,
    mes INTEGER,
    año INTEGER,
    hash_archivo VARCHAR(64) UNIQUE,
    tamaño_archivo INTEGER,
    algoritmo_usado VARCHAR(100) DEFAULT 'advanced_processing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de facturación
CREATE TABLE IF NOT EXISTS facturacion (
    id SERIAL PRIMARY KEY,
    fecha_factura DATE,
    serie_factura VARCHAR(50),
    folio_factura VARCHAR(50),
    cliente VARCHAR(255),
    monto_neto DECIMAL(15,2) DEFAULT 0,
    monto_total DECIMAL(15,2) DEFAULT 0,
    saldo_pendiente DECIMAL(15,2) DEFAULT 0,
    dias_credito INTEGER DEFAULT 30,
    uuid_factura VARCHAR(36),
    importe_cobrado DECIMAL(15,2) DEFAULT 0,
    fecha_cobro DATE,
    dias_cobro INTEGER,
    agente VARCHAR(255),
    condiciones_pago VARCHAR(255),
    archivo_id INTEGER REFERENCES archivos_procesados(id),
    mes INTEGER,
    año INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de cobranza
CREATE TABLE IF NOT EXISTS cobranza (
    id SERIAL PRIMARY KEY,
    fecha_pago DATE,
    serie_pago VARCHAR(50),
    folio_pago VARCHAR(50),
    cliente VARCHAR(255),
    moneda VARCHAR(10) DEFAULT 'MXN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1.0,
    parcialidad INTEGER DEFAULT 1,
    importe_pagado DECIMAL(15,2) DEFAULT 0,
    uuid_factura_relacionada VARCHAR(36),
    forma_pago VARCHAR(100),
    archivo_id INTEGER REFERENCES archivos_procesados(id),
    mes INTEGER,
    año INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de CFDI relacionados
CREATE TABLE IF NOT EXISTS cfdi_relacionado (
    id SERIAL PRIMARY KEY,
    uuid_factura VARCHAR(36),
    xml TEXT,
    cliente_receptor VARCHAR(255),
    tipo_relacion VARCHAR(100),
    importe_relacion DECIMAL(15,2) DEFAULT 0,
    uuid_factura_relacionada VARCHAR(36),
    archivo_id INTEGER REFERENCES archivos_procesados(id),
    mes INTEGER,
    año INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    folio_factura VARCHAR(50),
    pedido VARCHAR(100),
    kg DECIMAL(10,2) DEFAULT 0,
    precio_unitario DECIMAL(10,4) DEFAULT 0,
    importe_sin_iva DECIMAL(15,2) DEFAULT 0,
    material VARCHAR(255),
    dias_credito INTEGER DEFAULT 30,
    fecha_factura DATE,
    fecha_pago DATE,
    archivo_id INTEGER REFERENCES archivos_procesados(id),
    mes INTEGER,
    año INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_facturacion_fecha ON facturacion(fecha_factura);
CREATE INDEX IF NOT EXISTS idx_facturacion_cliente ON facturacion(cliente);
CREATE INDEX IF NOT EXISTS idx_facturacion_archivo ON facturacion(archivo_id);
CREATE INDEX IF NOT EXISTS idx_facturacion_uuid ON facturacion(uuid_factura);
CREATE INDEX IF NOT EXISTS idx_facturacion_mes_año ON facturacion(mes, año);

CREATE INDEX IF NOT EXISTS idx_cobranza_fecha ON cobranza(fecha_pago);
CREATE INDEX IF NOT EXISTS idx_cobranza_cliente ON cobranza(cliente);
CREATE INDEX IF NOT EXISTS idx_cobranza_archivo ON cobranza(archivo_id);
CREATE INDEX IF NOT EXISTS idx_cobranza_mes_año ON cobranza(mes, año);

CREATE INDEX IF NOT EXISTS idx_pedidos_folio ON pedidos(folio_factura);
CREATE INDEX IF NOT EXISTS idx_pedidos_material ON pedidos(material);
CREATE INDEX IF NOT EXISTS idx_pedidos_archivo ON pedidos(archivo_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_mes_año ON pedidos(mes, año);

-- Crear función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear triggers para actualizar updated_at
CREATE TRIGGER update_archivos_updated_at BEFORE UPDATE ON archivos_procesados FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_facturacion_updated_at BEFORE UPDATE ON facturacion FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cobranza_updated_at BEFORE UPDATE ON cobranza FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cfdi_updated_at BEFORE UPDATE ON cfdi_relacionado FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pedidos_updated_at BEFORE UPDATE ON pedidos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos de prueba (opcional)
INSERT INTO archivos_procesados (nombre_archivo, registros_procesados, estado, mes, año) 
VALUES ('test_archivo.xlsx', 0, 'procesado', 12, 2024)
ON CONFLICT (nombre_archivo) DO NOTHING;
