"""
Mapeo personalizado para compras de importación Immermex
Basado en el análisis del archivo mejorado 'IMM-Compras de importacion (Compartido).xlsx'
"""

import pandas as pd
from datetime import datetime

# Mapeo completo para compras de importación
IMMERMEX_COMPRAS_MAPPING = {
    # Información básica de la compra
    'fecha_compra': 'Fecha Pedido',  # Fecha del pedido
    'numero_factura': 'fac prov',  # Número de factura del proveedor
    'proveedor': 'Proveedor',  # Nombre del proveedor
    'concepto': 'Material',  # Material/producto comprado
    'categoria': 'IMI',  # Identificador de importación (IMI)
    
    # Información de cantidad y precios
    'cantidad': 'Kilogramos',  # Cantidad en kilogramos
    'unidad': 'KG',  # Unidad fija (kilogramos)
    'precio_unitario': 'PU',  # Precio unitario en USD
    'precio_unitario_mxn': 'P.U. MXN',  # Precio unitario en MXN
    'subtotal': 'PRECIO DLLS',  # Subtotal en USD
    'subtotal_mxn': 'PRECIO MXN',  # Subtotal en MXN
    'total': 'COSTO TOTAL',  # Costo total incluyendo gastos aduanales
    'iva': 'IVA',  # IVA pagado
    
    # Información de moneda y cambio
    'moneda': 'DIVISA',  # Moneda (USD)
    'tipo_cambio': 'XR',  # Tipo de cambio usado
    'tipo_cambio_anticipo': 'Tipo de Cambio ANTICIPO',
    'tipo_cambio_factura': 'Tipo de Cambio FACTURA',
    
    # Información de pagos y crédito
    'dias_credito': 'Dias Credito',  # Días de crédito
    'forma_pago': 'Financiera',  # Financiera utilizada
    'porcentaje_anticipo': '% Anticipo',  # Porcentaje de anticipo
    'anticipo_usd': 'ANTICIPO DLLS',  # Anticipo en USD
    'fecha_anticipo': 'FECHA ANTICIPO',  # Fecha del anticipo
    'fecha_vencimiento': 'FECHA VENCIMIENTO FACTURA',  # Fecha de vencimiento
    'fecha_pago': 'FECHA PAGO FACTURA',  # Fecha de pago
    'pago_usd': 'PAGO FACTURA DLLS',  # Pago en USD
    
    # Información aduanal
    'puerto_origen': 'Puerto Origen',  # Puerto de origen
    'fecha_salida_puerto': 'Fecha Salida Puerto Origen (ETD/BL)',  # Fecha de salida
    'fecha_arribo_puerto': 'FECHA ARRIBO A PUERTO (ETA)',  # Fecha de arribo
    'fecha_entrada_inmermex': 'FECHA ENTRADA IMMERMEX',  # Fecha de entrada a Immermex
    'fecha_entrada_aduana': 'FECHA ENTRADA ADUANA',  # Fecha de entrada a aduana
    'fecha_salida_aduana': 'FECHA SALIDA ADUANA',  # Fecha de salida de aduana
    'pedimento': 'Pedimento',  # Número de pedimento
    'gastos_aduanales': 'Gastos aduanales',  # Gastos aduanales
    'porcentaje_gastos_aduanales': '% Gastos aduanales',  # Porcentaje de gastos aduanales
    'fecha_pago_impuestos': 'FECHA PAGO IMPUESTOS',  # Fecha de pago de impuestos
    'dias_en_puerto': 'DIAS EN PUERTO',  # Días en puerto
    
    # Información adicional
    'agente': 'Agente',  # Agente aduanal
    'factura_agente': 'fac agente',  # Factura del agente
    'porcentaje_imi': 'Porcentaje de la IMI',  # Porcentaje de la importación
    'precio_total_unitario': 'P.U. Total',  # Precio total unitario
}

# Campos adicionales específicos para importaciones
IMPORTACION_FIELDS = {
    'tipo_operacion': 'IMPORTACION',  # Tipo de operación fijo
    'origen': 'EXTRANJERO',  # Origen fijo
    'destino': 'MEXICO',  # Destino fijo
    'modalidad': 'MARITIMA',  # Modalidad de transporte (inferida del puerto)
}

def apply_immermex_mapping(df):
    """Aplica el mapeo específico para compras de importación Immermex"""
    
    mapped_df = pd.DataFrame()
    
    # Mapear campos principales
    for target_field, source_column in IMMERMEX_COMPRAS_MAPPING.items():
        if source_column in df.columns:
            mapped_df[target_field] = df[source_column]
        else:
            mapped_df[target_field] = None
    
    # Agregar campos específicos de importación
    for field, value in IMPORTACION_FIELDS.items():
        mapped_df[field] = value
    
    # Procesar fechas
    date_columns = [
        'fecha_compra', 'fecha_anticipo', 'fecha_vencimiento', 'fecha_pago',
        'fecha_salida_puerto', 'fecha_arribo_puerto', 'fecha_entrada_inmermex',
        'fecha_entrada_aduana', 'fecha_salida_aduana', 'fecha_pago_impuestos'
    ]
    
    for col in date_columns:
        if col in mapped_df.columns:
            # Intentar diferentes formatos de fecha
            mapped_df[col] = pd.to_datetime(mapped_df[col], errors='coerce', dayfirst=True)
    
    # Calcular campos derivados
    mapped_df['mes'] = mapped_df['fecha_compra'].dt.month
    mapped_df['año'] = mapped_df['fecha_compra'].dt.year
    
    # Determinar estado de pago
    def determine_payment_status(row):
        if pd.notna(row['fecha_pago']):
            return 'pagado'
        elif pd.notna(row['fecha_vencimiento']):
            # Convertir a fecha si es necesario
            vencimiento = row['fecha_vencimiento']
            if hasattr(vencimiento, 'date'):
                vencimiento = vencimiento.date()
            if vencimiento < datetime.now().date():
                return 'vencido'
            else:
                return 'pendiente'
        else:
            return 'pendiente'
    
    mapped_df['estado_pago'] = mapped_df.apply(determine_payment_status, axis=1)
    
    # Limpiar valores numéricos
    numeric_columns = [
        'cantidad', 'precio_unitario', 'precio_unitario_mxn', 'subtotal', 
        'subtotal_mxn', 'total', 'iva', 'tipo_cambio', 'dias_credito',
        'porcentaje_anticipo', 'anticipo_usd', 'pago_usd', 'gastos_aduanales',
        'porcentaje_gastos_aduanales', 'dias_en_puerto', 'porcentaje_imi',
        'precio_total_unitario'
    ]
    
    for col in numeric_columns:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_numeric(mapped_df[col], errors='coerce').fillna(0)
    
    # Limpiar texto
    text_columns = [
        'numero_factura', 'proveedor', 'concepto', 'categoria', 'moneda',
        'forma_pago', 'puerto_origen', 'pedimento', 'agente', 'factura_agente'
    ]
    
    for col in text_columns:
        if col in mapped_df.columns:
            mapped_df[col] = mapped_df[col].astype(str).str.strip()
            mapped_df[col] = mapped_df[col].replace('nan', None)
    
    return mapped_df

def get_import_summary(df):
    """Genera resumen de importaciones"""
    
    summary = {
        'total_importaciones': len(df),
        'total_proveedores': df['proveedor'].nunique(),
        'total_materiales': df['concepto'].nunique(),
        'total_kilogramos': df['cantidad'].sum(),
        'total_costo_usd': df['subtotal'].sum(),
        'total_costo_mxn': df['subtotal_mxn'].sum(),
        'total_costo_final': df['total'].sum(),
        'total_iva': df['iva'].sum(),
        'importaciones_pagadas': len(df[df['estado_pago'] == 'pagado']),
        'importaciones_pendientes': len(df[df['estado_pago'] == 'pendiente']),
        'importaciones_vencidas': len(df[df['estado_pago'] == 'vencido']),
    }
    
    return summary

# Configuración para el servicio de importación
IMMERMEX_COLUMN_MAPPING = IMMERMEX_COMPRAS_MAPPING

# Campos requeridos para validación
REQUIRED_FIELDS = [
    'fecha_compra', 'proveedor', 'concepto', 'cantidad', 'total'
]

# Campos opcionales
OPTIONAL_FIELDS = [
    'numero_factura', 'precio_unitario', 'iva', 'dias_credito',
    'fecha_vencimiento', 'fecha_pago', 'moneda', 'tipo_cambio'
]