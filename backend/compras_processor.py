"""
Procesador específico para archivos de compras de Immermex
Maneja la estructura específica del archivo de compras e importaciones
Version: 2.0 - Refactorizado completo sin errores de pandas
"""

import pandas as pd
import io
from datetime import datetime
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def process_compras_excel_from_bytes(content: bytes, filename: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Procesa un archivo Excel de compras desde bytes en memoria
    
    Args:
        content: Contenido del archivo en bytes
        filename: Nombre del archivo
        
    Returns:
        Tuple con (datos_procesados, kpis)
    """
    try:
        logger.info(f"Iniciando procesamiento de archivo de compras: {filename}")
        
        # Leer el archivo Excel
        excel_file = io.BytesIO(content)
        
        # Intentar leer la pestaña "Resumen Compras"
        try:
            df = pd.read_excel(excel_file, sheet_name="Resumen Compras")
            logger.info(f"Pestaña 'Resumen Compras' encontrada con {len(df)} filas")
        except Exception as e:
            logger.warning(f"No se pudo leer la pestaña 'Resumen Compras': {e}")
            # Intentar con la primera pestaña
            excel_file.seek(0)
            df = pd.read_excel(excel_file, sheet_name=0)
            logger.info(f"Usando primera pestaña con {len(df)} filas")
        
        # Limpiar datos
        df = clean_compras_data(df)
        
        # Procesar datos específicos de compras
        processed_data = process_compras_data(df)
        
        # Generar KPIs específicos de compras
        kpis = generate_compras_kpis(processed_data)
        
        logger.info(f"Procesamiento completado: {len(processed_data)} registros de compras")
        
        return processed_data, kpis
        
    except Exception as e:
        logger.error(f"Error procesando archivo de compras {filename}: {str(e)}")
        raise Exception(f"Error procesando archivo de compras: {str(e)}")

def clean_compras_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y prepara los datos de compras"""
    logger.info("Iniciando limpieza de datos de compras")
    
    # Eliminar filas completamente vacías
    df = df.dropna(how='all')
    
    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how='all')
    
    # Limpiar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()
    
    # Buscar la fila de encabezados (puede estar en diferentes filas)
    header_row = find_header_row(df)
    if header_row > 0:
        df = df.iloc[header_row:].reset_index(drop=True)
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    
    logger.info(f"Datos limpios: {len(df)} filas, {len(df.columns)} columnas")
    logger.info(f"Columnas encontradas: {list(df.columns)}")
    
    return df

def find_header_row(df: pd.DataFrame) -> int:
    """Encuentra la fila que contiene los encabezados"""
    # Buscar filas que contengan palabras clave de encabezados
    keywords = ['IMI', 'Proveedor', 'Material', 'Kilogramos', 'PU', 'DIVISA']
    
    for i in range(min(10, len(df))):  # Buscar en las primeras 10 filas
        row_values = df.iloc[i].astype(str).str.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in ' '.join(row_values))
        if matches >= 3:  # Si encuentra al menos 3 palabras clave
            return i
    
    return 0  # Si no encuentra, usar la primera fila

def safe_clean_moneda(val):
    """Limpia y valida el campo moneda"""
    if pd.isna(val):
        return 'USD'
    val_str = str(val).strip().upper()
    # Si es un número, devolver USD por defecto
    try:
        float(val_str)
        return 'USD'
    except:
        # Si es un string válido, buscar moneda conocida
        valid_currencies = ['USD', 'MXN', 'EUR', 'DLLS', 'PESOS']
        for currency in valid_currencies:
            if currency in val_str:
                return currency[:10]
        return 'USD'

def safe_fill_concepto(row):
    """Llena el campo concepto con IMI o valor por defecto"""
    concepto = row.get('concepto', '')
    imi = row.get('imi', '')
    
    # Si concepto está vacío o es NaN
    if pd.isna(concepto) or concepto == '':
        # Usar IMI si está disponible, sino usar valor por defecto
        if imi and not pd.isna(imi) and imi != '':
            return str(imi)
        else:
            return 'Material importado'
    else:
        return str(concepto)

def process_compras_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Procesa los datos específicos de compras"""
    logger.info("Procesando datos específicos de compras")
    
    # Mapear columnas del Excel a campos estándar
    column_mapping = {
        'IMI': 'imi',
        'Proveedor': 'proveedor',
        'Material': 'concepto',
        'fac prov': 'numero_factura',
        'Kilogramos': 'cantidad',
        'PU': 'precio_unitario',
        'DIVISA': 'moneda',
        'Fecha Pedido': 'fecha_compra',
        'Puerto Origen': 'puerto_origen',
        'Fecha Salida Puerto Origen (ETD/BL)': 'fecha_salida_puerto',
        'FECHA ARRIBO A PUERTO (ETA)': 'fecha_arribo_puerto',
        'FECHA ENTRADA IMMERMEX': 'fecha_entrada_inmermex',
        'PRECIO DLLS': 'precio_dlls',
        'XR': 'tipo_cambio',
        'Dias Credito': 'dias_credito',
        'Financiera': 'financiera',
        '% Anticipo': 'porcentaje_anticipo',
        'FECHA ANTICIPO': 'fecha_anticipo',
        'ANTICIPO DLLS': 'anticipo_dlls',
        'Tipo de Cambio ANTICIPO': 'tipo_cambio_anticipo',
        'FECHA VENCIMIENTO FACTURA': 'fecha_vencimiento',
        'FECHA PAGO FACTURA': 'fecha_pago',
        'PAGO FACTURA DLLS': 'pago_factura_dlls',
        'Tipo de Cambio FACTURA': 'tipo_cambio_factura',
        'P.U. MXN': 'pu_mxn',
        'PRECIO MXN': 'precio_mxn',
        'Porcentaje de la IMI': 'porcentaje_imi',
        'FECHA ENTRADA ADUANA': 'fecha_entrada_aduana',
        'Pedimento': 'pedimento',
        'Gastos aduanales': 'gastos_aduanales',
        'COSTO TOTAL': 'costo_total',
        '% Gastos aduanales': 'porcentaje_gastos_aduanales',
        'P.U. Total': 'pu_total',
        'FECHA PAGO IMPUESTOS': 'fecha_pago_impuestos',
        'IVA': 'iva',
        'FECHA SALIDA ADUANA': 'fecha_salida_aduana',
        'DIAS EN PUERTO': 'dias_en_puerto',
        'Agente': 'agente',
        'fac agente': 'fac_agente'
    }
    
    # Crear DataFrame con columnas mapeadas
    mapped_df = pd.DataFrame()
    
    for excel_col, db_field in column_mapping.items():
        if excel_col in df.columns:
            mapped_df[db_field] = df[excel_col]
        else:
            mapped_df[db_field] = None
    
    # Procesar fechas PRIMERO (antes de calcular mes y año)
    date_columns = [
        'fecha_compra', 'fecha_anticipo', 'fecha_vencimiento', 'fecha_pago',
        'fecha_salida_puerto', 'fecha_arribo_puerto', 'fecha_entrada_inmermex',
        'fecha_entrada_aduana', 'fecha_salida_aduana', 'fecha_pago_impuestos'
    ]
    
    for col in date_columns:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_datetime(mapped_df[col], errors='coerce', dayfirst=True)
    
    # Calcular campos derivados de fechas
    mapped_df['mes'] = mapped_df['fecha_compra'].dt.month
    mapped_df['año'] = mapped_df['fecha_compra'].dt.year
    
    # Limpiar valores numéricos ANTES de limpiar moneda
    numeric_columns = [
        'cantidad', 'precio_unitario', 'precio_dlls', 'tipo_cambio',
        'porcentaje_anticipo', 'anticipo_dlls', 'tipo_cambio_anticipo',
        'pago_factura_dlls', 'tipo_cambio_factura', 'pu_mxn', 'precio_mxn',
        'porcentaje_imi', 'gastos_aduanales', 'costo_total',
        'porcentaje_gastos_aduanales', 'pu_total', 'iva', 'dias_en_puerto'
    ]
    
    for col in numeric_columns:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_numeric(mapped_df[col], errors='coerce').fillna(0)
    
    # Limpiar campo moneda - asegurar que sea un string válido
    if 'moneda' in mapped_df.columns:
        mapped_df['moneda'] = mapped_df['moneda'].apply(safe_clean_moneda)
    else:
        mapped_df['moneda'] = 'USD'
    
    # Agregar campos adicionales
    mapped_df['categoria'] = 'Importación'
    mapped_df['unidad'] = 'KG'
    
    # Calcular subtotal y total
    if 'subtotal' not in mapped_df.columns or mapped_df['subtotal'].isna().all():
        mapped_df['subtotal'] = mapped_df['cantidad'] * mapped_df['precio_unitario']
    
    if 'total' not in mapped_df.columns or mapped_df['total'].isna().all():
        mapped_df['total'] = mapped_df['costo_total'].fillna(mapped_df['subtotal'])
    
    # Asegurar que concepto tenga un valor
    if 'concepto' in mapped_df.columns:
        mapped_df['concepto'] = mapped_df.apply(safe_fill_concepto, axis=1)
    else:
        mapped_df['concepto'] = 'Material importado'
    
    # Determinar estado de pago
    def determine_payment_status(row):
        if pd.notna(row.get('fecha_pago')):
            return 'pagado'
        elif pd.notna(row.get('fecha_vencimiento')):
            vencimiento = row['fecha_vencimiento']
            
            # Convertir a datetime.date si es un Timestamp de pandas
            if isinstance(vencimiento, pd.Timestamp):
                vencimiento = vencimiento.date()
            elif isinstance(vencimiento, datetime):
                vencimiento = vencimiento.date()
            
            # Comparar fechas
            if hasattr(vencimiento, '__gt__'):
                try:
                    if vencimiento < datetime.now().date():
                        return 'vencido'
                    else:
                        return 'pendiente'
                except:
                    return 'pendiente'
            else:
                return 'pendiente'
        else:
            return 'pendiente'
    
    mapped_df['estado_pago'] = mapped_df.apply(determine_payment_status, axis=1)
    
    # Convertir a lista de diccionarios
    compras_data = mapped_df.to_dict('records')
    
    # Filtrar registros válidos (que tengan fecha_compra, proveedor y cantidad)
    compras_data = [
        record for record in compras_data 
        if pd.notna(record.get('fecha_compra')) and 
           pd.notna(record.get('proveedor')) and 
           record.get('cantidad', 0) > 0
    ]
    
    logger.info(f"Datos de compras procesados: {len(compras_data)} registros válidos")
    
    return {
        'compras': compras_data
    }

def generate_compras_kpis(processed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera KPIs específicos para compras"""
    logger.info("Generando KPIs de compras")
    
    compras = processed_data.get('compras', [])
    
    if not compras:
        return {
            'total_compras': 0,
            'total_proveedores': 0,
            'total_kilogramos': 0,
            'total_costo_usd': 0,
            'total_costo_mxn': 0,
            'compras_pagadas': 0,
            'compras_pendientes': 0,
            'compras_vencidas': 0
        }
    
    df = pd.DataFrame(compras)
    
    kpis = {
        'total_compras': len(compras),
        'total_proveedores': df['proveedor'].nunique() if 'proveedor' in df.columns else 0,
        'total_kilogramos': df['cantidad'].sum() if 'cantidad' in df.columns else 0,
        'total_costo_usd': df['precio_dlls'].sum() if 'precio_dlls' in df.columns else 0,
        'total_costo_mxn': df['precio_mxn'].sum() if 'precio_mxn' in df.columns else 0,
        'compras_pagadas': len(df[df['estado_pago'] == 'pagado']) if 'estado_pago' in df.columns else 0,
        'compras_pendientes': len(df[df['estado_pago'] == 'pendiente']) if 'estado_pago' in df.columns else 0,
        'compras_vencidas': len(df[df['estado_pago'] == 'vencido']) if 'estado_pago' in df.columns else 0
    }
    
    logger.info(f"KPIs generados: {kpis}")
    
    return kpis
