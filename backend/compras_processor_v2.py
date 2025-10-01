"""
Procesador de compras v2 - Version limpia sin cache
"""

import pandas as pd
import io
from datetime import datetime
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def process_compras_v2(content: bytes, filename: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Procesa archivo Excel de compras - Version 2.0"""
    try:
        logger.info(f"[V2] Procesando: {filename}")
        
        # Leer Excel
        excel_file = io.BytesIO(content)
        try:
            df = pd.read_excel(excel_file, sheet_name="Resumen Compras")
            logger.info(f"[V2] Encontradas {len(df)} filas")
        except:
            excel_file.seek(0)
            df = pd.read_excel(excel_file, sheet_name=0)
        
        # Limpiar
        df = df.dropna(how='all').dropna(axis=1, how='all')
        df.columns = df.columns.astype(str).str.strip()
        
        logger.info(f"[V2] Columnas: {list(df.columns)[:10]}")
        
        # Mapear columnas
        result_df = pd.DataFrame()
        
        mapping = {
            'IMI': 'imi', 'Proveedor': 'proveedor', 'Material': 'concepto',
            'fac prov': 'numero_factura', 'Kilogramos': 'cantidad',
            'PU': 'precio_unitario', 'DIVISA': 'moneda',
            'Fecha Pedido': 'fecha_compra', 'Puerto Origen': 'puerto_origen',
            'PRECIO DLLS': 'precio_dlls', 'XR': 'tipo_cambio',
            'Dias Credito': 'dias_credito', 'COSTO TOTAL': 'costo_total',
            'IVA': 'iva', 'PRECIO MXN': 'precio_mxn',
            'FECHA VENCIMIENTO FACTURA': 'fecha_vencimiento',
            'FECHA PAGO FACTURA': 'fecha_pago',
            'Pedimento': 'pedimento', 'Gastos aduanales': 'gastos_aduanales',
            'Agente': 'agente', 'fac agente': 'fac_agente'
        }
        
        for excel_col, db_col in mapping.items():
            if excel_col in df.columns:
                result_df[db_col] = df[excel_col]
        
        # Procesar fechas
        date_cols = ['fecha_compra', 'fecha_vencimiento', 'fecha_pago']
        for col in date_cols:
            if col in result_df.columns:
                result_df[col] = pd.to_datetime(result_df[col], errors='coerce', dayfirst=True)
        
        # Derivar mes y año
        result_df['mes'] = result_df['fecha_compra'].dt.month
        result_df['año'] = result_df['fecha_compra'].dt.year
        
        # Limpiar numéricos
        num_cols = ['cantidad', 'precio_unitario', 'precio_dlls', 'tipo_cambio', 
                    'costo_total', 'iva', 'precio_mxn', 'gastos_aduanales', 'dias_credito']
        for col in num_cols:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
        
        # Limpiar moneda
        if 'moneda' in result_df.columns:
            result_df['moneda'] = result_df['moneda'].astype(str).apply(
                lambda x: 'USD' if pd.isna(x) or x == 'nan' or x.replace('.', '').replace(',', '').isdigit() else x[:10]
            )
        else:
            result_df['moneda'] = 'USD'
        
        # Llenar concepto
        if 'concepto' not in result_df.columns or result_df['concepto'].isna().all():
            if 'imi' in result_df.columns:
                result_df['concepto'] = result_df['imi']
            else:
                result_df['concepto'] = 'Material importado'
        
        result_df['concepto'] = result_df['concepto'].fillna('Material importado')
        
        # Campos fijos
        result_df['categoria'] = 'Importación'
        result_df['unidad'] = 'KG'
        result_df['subtotal'] = result_df['cantidad'] * result_df['precio_unitario']
        result_df['total'] = result_df.get('costo_total', result_df['subtotal'])
        
        # Estado de pago
        def get_estado(row):
            if pd.notna(row.get('fecha_pago')):
                return 'pagado'
            if pd.notna(row.get('fecha_vencimiento')):
                try:
                    venc = row['fecha_vencimiento']
                    if hasattr(venc, 'date'):
                        venc = venc.date()
                    if venc < datetime.now().date():
                        return 'vencido'
                except:
                    pass
            return 'pendiente'
        
        result_df['estado_pago'] = result_df.apply(get_estado, axis=1)
        
        # Filtrar válidos
        compras = result_df.to_dict('records')
        compras = [c for c in compras if pd.notna(c.get('fecha_compra')) and 
                  pd.notna(c.get('proveedor')) and c.get('cantidad', 0) > 0]
        
        logger.info(f"[V2] Procesados: {len(compras)} registros")
        
        # KPIs
        kpis = {
            'total_compras': len(compras),
            'total_proveedores': len(set(c['proveedor'] for c in compras if c.get('proveedor'))),
            'total_kilogramos': sum(c.get('cantidad', 0) for c in compras),
            'total_costo_usd': sum(c.get('precio_dlls', 0) for c in compras),
            'total_costo_mxn': sum(c.get('precio_mxn', 0) for c in compras),
            'compras_pagadas': sum(1 for c in compras if c.get('estado_pago') == 'pagado'),
            'compras_pendientes': sum(1 for c in compras if c.get('estado_pago') == 'pendiente'),
            'compras_vencidas': sum(1 for c in compras if c.get('estado_pago') == 'vencido')
        }
        
        return {'compras': compras}, kpis
        
    except Exception as e:
        logger.error(f"[V2] Error: {str(e)}")
        raise

