"""
Script de limpieza y normalización de datos para Immermex Dashboard
Procesa archivos Excel mensuales y extrae datos según el diccionario de extracción
Integrado con algoritmo avanzado de limpieza de datos
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import re
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImmermexDataProcessor:
    """
    Procesador de datos para archivos Excel de Immermex
    Integrado con algoritmo avanzado de limpieza y detección automática
    """
    
    def __init__(self):
        self.facturacion_df = None
        self.cobranza_df = None
        self.cfdi_relacionados_df = None
        self.inventario_df = None
        self.pedidos_df = None
        self.maestro_df = None
        self.processed_data = {}
    
    def detect_header_row(self, path: str, sheet_name: str, keywords: list) -> int:
        """
        Detecta dinámicamente la fila de encabezados basándose en palabras clave
        
        Args:
            path: Ruta del archivo Excel
            sheet_name: Nombre de la hoja
            keywords: Lista de palabras clave para identificar encabezados
            
        Returns:
            Número de fila donde están los encabezados
        """
        try:
            # Leer las primeras 20 filas para buscar encabezados
            preview = pd.read_excel(path, sheet_name=sheet_name, nrows=20, header=None)
            
            # Buscar la fila que contenga más palabras clave
            best_match = (0, 0)  # (fila, número_de_coincidencias)
            
            for idx, row in preview.iterrows():
                row_str = ' '.join(row.astype(str).fillna(''))
                matches = sum(1 for keyword in keywords if keyword.lower() in row_str.lower())
                if matches > best_match[1]:
                    best_match = (idx, matches)
            
            if best_match[1] >= 3:  # Al menos 3 coincidencias
                logger.info(f"Encabezados encontrados en fila {best_match[0]} para hoja '{sheet_name}' ({best_match[1]} coincidencias)")
                return best_match[0]
            else:
                logger.warning(f"No se encontraron encabezados en hoja '{sheet_name}', usando fila 0")
                return 0
            
        except Exception as e:
            logger.error(f"Error detectando encabezados en hoja '{sheet_name}': {str(e)}")
            return 0
    
    def clean_string_column(self, series: pd.Series) -> pd.Series:
        """Limpia columnas de texto"""
        return series.astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    
    def clean_uuid(self, series: pd.Series) -> pd.Series:
        """Limpia y valida UUIDs"""
        cleaned = series.astype(str).str.strip().str.upper()
        # Filtrar UUIDs válidos (formato básico)
        uuid_pattern = r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$'
        cleaned = cleaned.where(cleaned.str.match(uuid_pattern), '')
        return cleaned.replace(['NAN', 'NONE', ''], np.nan)
        
    def load_excel_file(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Carga archivo Excel y extrae todas las hojas
        """
        try:
            logger.info(f"Cargando archivo: {file_path}")
            
            # Leer todas las hojas del Excel
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            logger.info(f"Hojas encontradas: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                logger.info(f"Procesando hoja: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheets_data[sheet_name] = df
                logger.info(f"Hoja '{sheet_name}' cargada: {df.shape[0]} filas, {df.shape[1]} columnas")
                
                # Debug: mostrar columnas y primeras filas
                logger.info(f"  Columnas: {list(df.columns)}")
                if not df.empty:
                    logger.info(f"  Primera fila: {df.iloc[0].to_dict()}")
                    # Buscar filas con datos de facturación
                    for i in range(min(5, len(df))):
                        row_str = ' '.join(df.iloc[i].astype(str).fillna(''))
                        if any(keyword in row_str.lower() for keyword in ['fecha', 'cliente', 'monto', 'total']):
                            logger.info(f"  Fila {i} parece tener datos: {df.iloc[i].to_dict()}")
                            break
            
            return sheets_data
            
        except Exception as e:
            logger.error(f"Error cargando archivo Excel: {str(e)}")
            raise
    
    def normalize_facturacion(self, df: pd.DataFrame, file_path: str = None) -> pd.DataFrame:
        """
        Normaliza datos de facturación con detección automática de encabezados
        """
        logger.info("Normalizando datos de facturación...")
        
        try:
            # Si se proporciona file_path, detectar encabezados automáticamente
            if file_path:
                keywords = ['fecha', 'serie', 'folio', 'cliente', 'razón social', 'neto', 'total']
                header_row = self.detect_header_row(file_path, "facturacion", keywords)
                if header_row > 0:
                    df = pd.read_excel(file_path, sheet_name="facturacion", header=header_row)
                    logger.info(f"Releyendo facturación con encabezados en fila {header_row}")
            
            # Mapeo de columnas flexible y completo
            column_mapping = {
                # Fecha
                'fecha': 'fecha_factura',
                'fecha de factura': 'fecha_factura',
                'fecha_factura': 'fecha_factura',
                'todos los documentos': 'fecha_factura',  # Columna específica del archivo
                
                # Serie y Folio
                'serie': 'serie_factura',
                'serie factura': 'serie_factura',
                'serie_factura': 'serie_factura',
                'unnamed: 1': 'serie_factura',  # Columna específica del archivo
                'folio': 'folio_factura',
                'folio factura': 'folio_factura',
                'folio_factura': 'folio_factura',
                'unnamed: 2': 'folio_factura',  # Columna específica del archivo
                
                # Cliente
                'cliente': 'cliente',
                'razón social': 'cliente',
                'razon social': 'cliente',
                'nombre cliente': 'cliente',
                'unnamed: 3': 'cliente',  # Columna específica del archivo
                
                # Montos
                'neto': 'monto_neto',
                'monto neto': 'monto_neto',
                'monto_neto': 'monto_neto',
                'subtotal': 'monto_neto',
                'unnamed: 4': 'monto_neto',  # Columna específica del archivo
                'total': 'monto_total',
                'monto total': 'monto_total',
                'monto_total': 'monto_total',
                'importe total': 'monto_total',
                'unnamed: 5': 'monto_total',  # Columna específica del archivo
                'pendiente': 'saldo_pendiente',
                'saldo pendiente': 'saldo_pendiente',
                'saldo_pendiente': 'saldo_pendiente',
                'pendiente de pago': 'saldo_pendiente',
                'unnamed: 6': 'saldo_pendiente',  # Columna específica del archivo
                
                # Condiciones
                'referencia': 'condiciones_pago',
                'condiciones de pago': 'condiciones_pago',
                'condiciones_pago': 'condiciones_pago',
                'días crédito': 'condiciones_pago',
                'dias credito': 'condiciones_pago',
                
                # Agente
                'agente': 'agente',
                'nombre del agente': 'agente',
                'vendedor': 'agente',
                'agente comercial': 'agente',
                
                # UUID
                'uuid': 'uuid_factura',
                'uuid factura': 'uuid_factura',
                'uuid_factura': 'uuid_factura',
                'folio fiscal': 'uuid_factura',
                'unnamed: 13': 'uuid_factura'  # Columna específica del archivo
            }
            
            # Renombrar columnas
            df_renamed = df.copy()
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df_renamed = df_renamed.rename(columns={old_name: new_name})
            
            # Crear DataFrame con columnas estándar
            clean_df = pd.DataFrame()
            
            # Fecha de factura
            fecha_col = df_renamed.get('fecha_factura', pd.Series())
            if isinstance(fecha_col, str):
                fecha_col = pd.Series([fecha_col])
            clean_df['fecha_factura'] = pd.to_datetime(fecha_col, errors='coerce')
            
            # Serie y folio
            serie_col = df_renamed.get('serie_factura', pd.Series())
            if isinstance(serie_col, str):
                serie_col = pd.Series([serie_col])
            clean_df['serie_factura'] = self.clean_string_column(serie_col)
            
            folio_col = df_renamed.get('folio_factura', pd.Series())
            if isinstance(folio_col, str):
                folio_col = pd.Series([folio_col])
            clean_df['folio_factura'] = self.clean_string_column(folio_col)
            
            # Cliente
            cliente_col = df_renamed.get('cliente', pd.Series())
            if isinstance(cliente_col, str):
                cliente_col = pd.Series([cliente_col])
            clean_df['cliente'] = self.clean_string_column(cliente_col)
            
            # Montos numéricos
            for col in ['monto_neto', 'monto_total', 'saldo_pendiente']:
                col_data = df_renamed.get(col, pd.Series())
                if isinstance(col_data, str):
                    col_data = pd.Series([col_data])
                clean_df[col] = pd.to_numeric(col_data, errors='coerce').fillna(0)
            
            # Días de crédito - usar la misma lógica que pedidos
            # Primero intentar obtener de la columna dias_credito directamente
            dias_credito_col = df_renamed.get('dias_credito', pd.Series())
            if isinstance(dias_credito_col, str):
                dias_credito_col = pd.Series([dias_credito_col])
            
            # Si no hay columna dias_credito, extraer de condiciones_pago
            if dias_credito_col.empty or dias_credito_col.isna().all():
                condiciones = df_renamed.get('condiciones_pago', pd.Series())
                if isinstance(condiciones, str):
                    condiciones = pd.Series([condiciones])
                clean_df['dias_credito'] = pd.to_numeric(
                    condiciones.astype(str).str.extract(r'(\d+)')[0], errors='coerce'
                ).fillna(30)  # Default 30 días
            else:
                # Usar la columna dias_credito directamente
                clean_df['dias_credito'] = pd.to_numeric(
                    dias_credito_col, errors='coerce'
                ).fillna(30)
            
            # Agente
            agente_col = df_renamed.get('agente', pd.Series())
            if isinstance(agente_col, str):
                agente_col = pd.Series([agente_col])
            clean_df['agente'] = self.clean_string_column(agente_col)
            
            # UUID
            uuid_col = df_renamed.get('uuid_factura', pd.Series())
            if isinstance(uuid_col, str):
                uuid_col = pd.Series([uuid_col])
            clean_df['uuid_factura'] = self.clean_uuid(uuid_col)
            
            # Campos calculados
            if not clean_df.empty and 'fecha_factura' in clean_df.columns:
                clean_df['mes'] = clean_df['fecha_factura'].dt.month
                clean_df['año'] = clean_df['fecha_factura'].dt.year
            
            # Eliminar filas completamente vacías
            clean_df = clean_df.dropna(how='all')
            
            # Eliminar duplicados por UUID
            clean_df = clean_df.drop_duplicates(subset=['uuid_factura'], keep='first')
            
            self.facturacion_df = clean_df
            logger.info(f"Facturación normalizada: {clean_df.shape[0]} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error normalizando facturación: {str(e)}")
            return pd.DataFrame()
    
    def normalize_cobranza(self, df: pd.DataFrame, file_path: str = None) -> pd.DataFrame:
        """
        Normaliza datos de cobranza con detección automática de encabezados
        """
        logger.info("Normalizando datos de cobranza...")
        
        try:
            # Si se proporciona file_path, detectar encabezados automáticamente
            if file_path:
                keywords = ['fecha', 'pago', 'cliente', 'importe', 'uuid']
                header_row = self.detect_header_row(file_path, "cobranza", keywords)
                if header_row > 0:
                    df = pd.read_excel(file_path, sheet_name="cobranza", header=header_row)
                    logger.info(f"Releyendo cobranza con encabezados en fila {header_row}")
            
            # Mapeo de columnas flexible y completo
            column_mapping = {
                'fecha de pago': 'fecha_pago',
                'fecha_pago': 'fecha_pago',
                'fecha pago': 'fecha_pago',
                'fecha cobro': 'fecha_pago',
                
                'serie pago': 'serie_pago',
                'serie_pago': 'serie_pago',
                'serie': 'serie_pago',
                
                'folio pago': 'folio_pago',
                'folio_pago': 'folio_pago',
                'folio': 'folio_pago',
                
                'cliente': 'cliente',
                'razón social': 'cliente',
                'razon social': 'cliente',
                
                'moneda': 'moneda',
                'tipo de cambio': 'tipo_cambio',
                'tipo_cambio': 'tipo_cambio',
                
                'forma de pago': 'forma_pago',
                'forma_pago': 'forma_pago',
                'forma pago': 'forma_pago',
                
                'parcialidad': 'parcialidad',
                'no. parcialidad': 'parcialidad',
                'numero parcialidad': 'parcialidad',
                
                'importe pagado': 'importe_pagado',
                'importe_pagado': 'importe_pagado',
                'importe': 'importe_pagado',
                'monto pagado': 'importe_pagado',
                'importe cobrado': 'importe_pagado',
                
                'uuid factura relacionada': 'uuid_factura_relacionada',
                'uuid_factura_relacionada': 'uuid_factura_relacionada',
                'uuid relacionada': 'uuid_factura_relacionada',
                'folio fiscal relacionado': 'uuid_factura_relacionada',
                'uuid': 'uuid_factura_relacionada'
            }
            
            # Renombrar columnas
            df_renamed = df.copy()
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df_renamed = df_renamed.rename(columns={old_name: new_name})
            
            # Detectar automáticamente columnas datetime que no fueron mapeadas
            logger.info(f"Columnas después del mapeo manual: {list(df_renamed.columns)}")
            logger.info(f"Tipos de datos de las columnas: {df_renamed.dtypes.to_dict()}")
            
            for col in df_renamed.columns:
                # Verificar si la columna contiene objetos datetime y no es fecha_pago ya
                if col != 'fecha_pago' and (df_renamed[col].dtype == 'datetime64[ns]' or any(isinstance(val, pd.Timestamp) for val in df_renamed[col].dropna().head(5))):
                    logger.info(f"Detectada columna datetime automáticamente: {col} -> fecha_pago")
                    df_renamed = df_renamed.rename(columns={col: 'fecha_pago'})
                    break  # Solo tomar la primera columna datetime encontrada
            
            # Crear DataFrame con columnas estándar
            clean_df = pd.DataFrame()
            
            # Fecha de pago
            clean_df['fecha_pago'] = pd.to_datetime(
                df_renamed.get('fecha_pago', ''), errors='coerce'
            )
            
            # Serie y folio
            clean_df['serie_pago'] = self.clean_string_column(
                df_renamed.get('serie_pago', '')
            )
            clean_df['folio_pago'] = self.clean_string_column(
                df_renamed.get('folio_pago', '')
            )
            
            # Cliente
            clean_df['cliente'] = self.clean_string_column(
                df_renamed.get('cliente', '')
            )
            
            # Moneda y tipo de cambio
            clean_df['moneda'] = self.clean_string_column(
                df_renamed.get('moneda', 'MXN')
            )
            clean_df['tipo_cambio'] = pd.to_numeric(
                df_renamed.get('tipo_cambio', 1), errors='coerce'
            ).fillna(1)
            
            # Forma de pago
            clean_df['forma_pago'] = self.clean_string_column(
                df_renamed.get('forma_pago', '')
            )
            
            # Parcialidad
            clean_df['parcialidad'] = pd.to_numeric(
                df_renamed.get('parcialidad', 1), errors='coerce'
            ).fillna(1)
            
            # Importe pagado
            clean_df['importe_pagado'] = pd.to_numeric(
                df_renamed.get('importe_pagado', 0), errors='coerce'
            ).fillna(0)
            
            # UUID factura relacionada
            clean_df['uuid_factura_relacionada'] = self.clean_uuid(
                df_renamed.get('uuid_factura_relacionada', '')
            )
            
            # Eliminar filas completamente vacías
            clean_df = clean_df.dropna(how='all')
            
            # Eliminar duplicados por UUID de factura relacionada
            clean_df = clean_df.drop_duplicates(subset=['uuid_factura_relacionada'], keep='first')
            
            self.cobranza_df = clean_df
            logger.info(f"Cobranza normalizada: {clean_df.shape[0]} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error normalizando cobranza: {str(e)}")
            return pd.DataFrame()
    
    def normalize_cfdi_relacionados(self, df: pd.DataFrame, file_path: str = None) -> pd.DataFrame:
        """
        Normaliza datos de CFDIs relacionados (anticipos/notas de crédito)
        """
        logger.info("Normalizando datos de CFDIs relacionados...")
        
        try:
            # Si se proporciona file_path, detectar encabezados automáticamente
            if file_path:
                keywords = ['xml', 'cliente', 'tipo', 'relacion', 'importe', 'uuid']
                header_row = self.detect_header_row(file_path, "cfdi relacionados", keywords)
                if header_row > 0:
                    df = pd.read_excel(file_path, sheet_name="cfdi relacionados", header=header_row)
                    logger.info(f"Releyendo CFDI con encabezados en fila {header_row}")
            
            # Mapeo de columnas flexible y completo
            column_mapping = {
                'xml': 'xml',
                'uuid cfdi': 'xml',
                'uuid_cfdi': 'xml',
                'folio fiscal': 'xml',
                'uuid': 'xml',
                
                'cliente receptor': 'cliente_receptor',
                'cliente_receptor': 'cliente_receptor',
                'cliente': 'cliente_receptor',
                'razón social': 'cliente_receptor',
                
                'tipo relación': 'tipo_relacion',
                'tipo_relacion': 'tipo_relacion',
                'tipo': 'tipo_relacion',
                'concepto': 'tipo_relacion',
                
                'importe relación': 'importe_relacion',
                'importe_relacion': 'importe_relacion',
                'importe': 'importe_relacion',
                'monto': 'importe_relacion',
                'importe cfdi': 'importe_relacion',
                
                'uuid factura relacionada': 'uuid_factura_relacionada',
                'uuid_factura_relacionada': 'uuid_factura_relacionada',
                'uuid relacionada': 'uuid_factura_relacionada',
                'folio fiscal relacionado': 'uuid_factura_relacionada',
                'folio relacionado': 'uuid_factura_relacionada'
            }
            
            # Renombrar columnas
            df_renamed = df.copy()
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df_renamed = df_renamed.rename(columns={old_name: new_name})
            
            # Crear DataFrame con columnas estándar
            clean_df = pd.DataFrame()
            
            # XML/UUID
            clean_df['xml'] = self.clean_uuid(
                df_renamed.get('xml', '')
            )
            
            # Cliente receptor
            clean_df['cliente_receptor'] = self.clean_string_column(
                df_renamed.get('cliente_receptor', '')
            )
            
            # Tipo de relación
            clean_df['tipo_relacion'] = self.clean_string_column(
                df_renamed.get('tipo_relacion', '')
            )
            
            # Importe
            clean_df['importe_relacion'] = pd.to_numeric(
                df_renamed.get('importe_relacion', 0), errors='coerce'
            ).fillna(0)
            
            # UUID factura relacionada
            clean_df['uuid_factura_relacionada'] = self.clean_uuid(
                df_renamed.get('uuid_factura_relacionada', '')
            )
            
            # Filtrar solo anticipos y notas de crédito
            clean_df = clean_df[
                clean_df['tipo_relacion'].str.contains(
                    'anticipo|nota.*crédito|nota.*credito', 
                    case=False, na=False
                )
            ]
            
            # Eliminar filas completamente vacías
            clean_df = clean_df.dropna(how='all')
            
            self.cfdi_relacionados_df = clean_df
            logger.info(f"CFDIs relacionados normalizados: {clean_df.shape[0]} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error normalizando CFDI: {str(e)}")
            return pd.DataFrame()
    
    def normalize_pedidos(self, df: pd.DataFrame, file_path: str = None, sheet_name: str = None) -> pd.DataFrame:
        """
        Normaliza datos de pedidos con detección automática de encabezados
        """
        logger.info("Normalizando datos de pedidos...")
        
        try:
            # Si se proporciona file_path, detectar encabezados automáticamente
            if file_path and sheet_name:
                keywords = ['factura', 'pedido', 'kg', 'precio', 'material']
                header_row = self.detect_header_row(file_path, sheet_name, keywords)
                if header_row > 0:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
                    logger.info(f"Releyendo pedidos con encabezados en fila {header_row}")
            
            # Mapeo de columnas flexible y completo
            column_mapping = {
                'no de factura': 'folio_factura',
                'folio factura': 'folio_factura',
                'folio_factura': 'folio_factura',
                'factura': 'folio_factura',
                'numero factura': 'folio_factura',
                
                'pedido': 'pedido',
                'numero pedido': 'pedido',
                'numero_pedido': 'pedido',
                'no pedido': 'pedido',
                
                'kgs': 'kg',
                'kg': 'kg',
                'kilogramos': 'kg',
                'peso': 'kg',
                'cantidad': 'kg',
                
                'precio unitario': 'precio_unitario',
                'precio_unitario': 'precio_unitario',
                'precio': 'precio_unitario',
                'costo unitario': 'precio_unitario',
                
                'importe mxn sin iva': 'importe_sin_iva',
                'importe_sin_iva': 'importe_sin_iva',
                'importe sin iva': 'importe_sin_iva',
                'subtotal': 'importe_sin_iva',
                'importe': 'importe_sin_iva',
                
                'material': 'material',
                'producto': 'material',
                'descripcion': 'material',
                
                'dias de credito': 'dias_credito',
                'dias_credito': 'dias_credito',
                'dias credito': 'dias_credito',
                'condiciones': 'dias_credito',
                
                'fecha factura': 'fecha_factura',
                'fecha_factura': 'fecha_factura',
                'fecha de factura': 'fecha_factura',
                
                'fecha de pago': 'fecha_pago',
                'fecha_pago': 'fecha_pago',
                'fecha pago': 'fecha_pago'
            }
            
            # Renombrar columnas
            df_renamed = df.copy()
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df_renamed = df_renamed.rename(columns={old_name: new_name})
            
            # Crear DataFrame con columnas estándar
            clean_df = pd.DataFrame()
            
            # Folio de factura
            clean_df['folio_factura'] = self.clean_string_column(
                df_renamed.get('folio_factura', '')
            )
            
            # Pedido
            clean_df['pedido'] = self.clean_string_column(
                df_renamed.get('pedido', '')
            )
            
            # Datos numéricos
            for col in ['kg', 'precio_unitario', 'importe_sin_iva']:
                clean_df[col] = pd.to_numeric(
                    df_renamed.get(col, 0), errors='coerce'
                ).fillna(0)
            
            # Material
            clean_df['material'] = self.clean_string_column(
                df_renamed.get('material', '')
            )
            
            # Días de crédito
            clean_df['dias_credito'] = pd.to_numeric(
                df_renamed.get('dias_credito', 30), errors='coerce'
            ).fillna(30)
            
            # Fechas
            clean_df['fecha_factura'] = pd.to_datetime(
                df_renamed.get('fecha_factura', ''), errors='coerce'
            )
            clean_df['fecha_pago'] = pd.to_datetime(
                df_renamed.get('fecha_pago', ''), errors='coerce'
            )
            
            # Eliminar filas completamente vacías
            clean_df = clean_df.dropna(how='all')
            
            self.pedidos_df = clean_df
            logger.info(f"Pedidos normalizados: {clean_df.shape[0]} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error normalizando pedidos: {str(e)}")
            return pd.DataFrame()
    
    def ensure_credit_days_consistency(self, facturacion_df: pd.DataFrame, pedidos_df: pd.DataFrame) -> tuple:
        """
        Garantiza que los días de crédito sean congruentes entre facturas y pedidos relacionados.
        Usa la factura como fuente de verdad para los días de crédito.
        
        Args:
            facturacion_df: DataFrame de facturación
            pedidos_df: DataFrame de pedidos
            
        Returns:
            tuple: (facturacion_df_corregida, pedidos_df_corregida, discrepancias_corregidas)
        """
        try:
            if facturacion_df.empty or pedidos_df.empty:
                logger.info("No hay datos para verificar congruencia de días de crédito")
                return facturacion_df, pedidos_df, 0
            
            # Crear una copia para trabajar
            facturacion_corregida = facturacion_df.copy()
            pedidos_corregidos = pedidos_df.copy()
            
            # Crear un diccionario de días de crédito por folio de factura
            dias_credito_por_folio = {}
            
            # Usar facturas como fuente de verdad
            for _, factura in facturacion_corregida.iterrows():
                folio = factura.get('folio_factura')
                dias_credito = factura.get('dias_credito')
                
                if folio and pd.notna(dias_credito):
                    dias_credito_por_folio[folio] = dias_credito
            
            logger.info(f"Se encontraron {len(dias_credito_por_folio)} facturas con días de crédito definidos")
            
            # Corregir días de crédito en pedidos
            discrepancias_corregidas = 0
            
            for idx, pedido in pedidos_corregidos.iterrows():
                folio = pedido.get('folio_factura')
                dias_credito_pedido = pedido.get('dias_credito')
                
                if folio in dias_credito_por_folio:
                    dias_credito_factura = dias_credito_por_folio[folio]
                    
                    # Si hay discrepancia, corregir usando la factura como fuente de verdad
                    if pd.notna(dias_credito_pedido) and dias_credito_pedido != dias_credito_factura:
                        pedidos_corregidos.at[idx, 'dias_credito'] = dias_credito_factura
                        discrepancias_corregidas += 1
                        
                        logger.debug(f"Corregido pedido {pedido.get('pedido', 'N/A')} "
                                   f"(folio {folio}): {dias_credito_pedido} → {dias_credito_factura}")
                    
                    # Si el pedido no tiene días de crédito, usar el de la factura
                    elif pd.isna(dias_credito_pedido):
                        pedidos_corregidos.at[idx, 'dias_credito'] = dias_credito_factura
                        discrepancias_corregidas += 1
                        
                        logger.debug(f"Asignado días de crédito a pedido {pedido.get('pedido', 'N/A')} "
                                   f"(folio {folio}): {dias_credito_factura}")
            
            if discrepancias_corregidas > 0:
                logger.info(f"✅ Se corrigieron {discrepancias_corregidas} discrepancias de días de crédito")
            else:
                logger.info("✅ Los días de crédito ya eran congruentes entre pedidos y facturas")
            
            return facturacion_corregida, pedidos_corregidos, discrepancias_corregidas
            
        except Exception as e:
            logger.error(f"Error garantizando congruencia de días de crédito: {str(e)}")
            return facturacion_df, pedidos_df, 0
    
    def fill_pedidos_fecha_factura(self, facturacion_df: pd.DataFrame, pedidos_df: pd.DataFrame) -> int:
        """
        Llena automáticamente la columna fecha_factura en pedidos usando la fecha de la factura asociada.
        
        Args:
            facturacion_df: DataFrame de facturación
            pedidos_df: DataFrame de pedidos
            
        Returns:
            int: Número de fechas asignadas
        """
        try:
            if facturacion_df.empty or pedidos_df.empty:
                logger.info("No hay datos para asignar fechas de factura")
                return 0
            
            # Crear un diccionario de fechas de factura por folio
            fechas_por_folio = {}
            
            for _, factura in facturacion_df.iterrows():
                folio = factura.get('folio_factura')
                fecha_factura = factura.get('fecha_factura')
                
                if folio and pd.notna(fecha_factura):
                    fechas_por_folio[folio] = fecha_factura
            
            logger.info(f"Se encontraron {len(fechas_por_folio)} facturas con fechas definidas")
            
            # Asignar fechas a pedidos
            fechas_asignadas = 0
            
            for idx, pedido in pedidos_df.iterrows():
                folio = pedido.get('folio_factura')
                fecha_actual = pedido.get('fecha_factura')
                
                if folio in fechas_por_folio:
                    fecha_factura = fechas_por_folio[folio]
                    
                    # Si el pedido no tiene fecha_factura o es diferente, asignar la de la factura
                    if pd.isna(fecha_actual) or fecha_actual != fecha_factura:
                        pedidos_df.at[idx, 'fecha_factura'] = fecha_factura
                        fechas_asignadas += 1
                        
                        logger.debug(f"Asignada fecha de factura a pedido {pedido.get('pedido', 'N/A')} "
                                   f"(folio {folio}): {fecha_factura}")
            
            if fechas_asignadas > 0:
                logger.info(f"✅ Se asignaron {fechas_asignadas} fechas de factura a pedidos")
            else:
                logger.info("✅ Las fechas de factura ya estaban asignadas correctamente")
            
            return fechas_asignadas
            
        except Exception as e:
            logger.error(f"Error asignando fechas de factura a pedidos: {str(e)}")
            return 0
    
    def calculate_relationships(self, facturacion: pd.DataFrame, cobranza: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula relaciones entre facturación y cobranza
        
        Args:
            facturacion: DataFrame de facturación
            cobranza: DataFrame de cobranza
            
        Returns:
            DataFrame de facturación con relaciones calculadas
        """
        try:
            facturacion_rel = facturacion.copy()
            
            # Agregar columnas de relación
            facturacion_rel['importe_cobrado'] = 0.0
            facturacion_rel['fecha_cobro'] = pd.NaT
            facturacion_rel['dias_cobro'] = 0
            
            # Relacionar por UUID
            for idx, factura in facturacion_rel.iterrows():
                uuid_factura = factura['uuid_factura']
                if pd.notna(uuid_factura) and uuid_factura != '':
                    cobranzas_relacionadas = cobranza[
                        cobranza['uuid_factura_relacionada'] == uuid_factura
                    ]
                    
                    if not cobranzas_relacionadas.empty:
                        facturacion_rel.at[idx, 'importe_cobrado'] = cobranzas_relacionadas['importe_pagado'].sum()
                        facturacion_rel.at[idx, 'fecha_cobro'] = cobranzas_relacionadas['fecha_pago'].max()
                        
                        # Calcular días de cobro
                        if pd.notna(factura['fecha_factura']) and pd.notna(facturacion_rel.at[idx, 'fecha_cobro']):
                            dias = (facturacion_rel.at[idx, 'fecha_cobro'] - factura['fecha_factura']).days
                            facturacion_rel.at[idx, 'dias_cobro'] = max(0, dias)
            
            # Recalcular saldo pendiente
            facturacion_rel['saldo_pendiente'] = facturacion_rel['monto_total'] - facturacion_rel['importe_cobrado']
            
            logger.info("Relaciones calculadas exitosamente")
            return facturacion_rel
            
        except Exception as e:
            logger.error(f"Error calculando relaciones: {str(e)}")
            return facturacion
    
    def normalize_inventario(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza datos de inventario
        """
        logger.info("Normalizando datos de inventario...")
        
        column_mapping = {
            'Material': 'material',
            'Cantidad Inicial': 'cantidad_inicial',
            'Entradas': 'entradas',
            'Salidas': 'salidas',
            'Cantidad Final': 'cantidad_final',
            'Costo Unitario': 'costo_unitario',
            'Valor Inventario': 'valor_inventario'
        }
        
        df_clean = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_clean.columns:
                df_clean = df_clean.rename(columns={old_col: new_col})
        
        # Normalizar cantidades y costos
        numeric_columns = ['cantidad_inicial', 'entradas', 'salidas', 'cantidad_final', 'costo_unitario', 'valor_inventario']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        self.inventario_df = df_clean
        logger.info(f"Inventario normalizado: {df_clean.shape[0]} registros")
        return df_clean
    
    def create_master_dataframe(self) -> pd.DataFrame:
        """
        Crea DataFrame maestro uniendo todas las tablas
        """
        logger.info("Creando DataFrame maestro...")
        
        if self.facturacion_df is None:
            raise ValueError("Debe procesar facturación primero")
        
        # Empezar con facturación como base
        master_df = self.facturacion_df.copy()
        
        # Unir con cobranza por folio y UUID
        if self.cobranza_df is not None:
            cobranza_agg = self.cobranza_df.groupby(['folio', 'uuid']).agg({
                'importe_cobrado': 'sum',
                'fecha_cobro': 'max'
            }).reset_index()
            
            master_df = master_df.merge(
                cobranza_agg,
                on=['folio', 'uuid'],
                how='left',
                suffixes=('', '_cobro')
            )
        
        # Unir con CFDIs relacionados por UUID
        if self.cfdi_relacionados_df is not None:
            cfdi_anticipos = self.cfdi_relacionados_df[
                self.cfdi_relacionados_df['tipo_cfdi'].str.contains('anticipo', case=False, na=False)
            ].groupby('uuid').agg({
                'importe_cfdi': 'sum'
            }).reset_index()
            cfdi_anticipos.columns = ['uuid', 'anticipos']
            
            master_df = master_df.merge(cfdi_anticipos, on='uuid', how='left')
        
        # Agregar métricas calculadas
        if 'fecha_cobro' in master_df.columns and 'fecha_factura' in master_df.columns:
            master_df['dias_vencimiento'] = (master_df['fecha_cobro'] - master_df['fecha_factura']).dt.days
        else:
            master_df['dias_vencimiento'] = 0
            
        if not master_df.empty:
            master_df['estado_cobro'] = master_df.apply(self._determinar_estado_cobro, axis=1)
        master_df['margen'] = master_df['total'] - master_df.get('anticipos', 0)
        
        self.maestro_df = master_df
        logger.info(f"DataFrame maestro creado: {master_df.shape[0]} registros")
        return master_df
    
    def _determinar_estado_cobro(self, row) -> str:
        """
        Determina el estado de cobro basado en fechas
        """
        if pd.isna(row.get('fecha_cobro')):
            dias_vencido = (datetime.now() - row['fecha_factura']).days
            if dias_vencido <= 30:
                return '0-30 días'
            elif dias_vencido <= 60:
                return '31-60 días'
            elif dias_vencido <= 90:
                return '61-90 días'
            else:
                return '90+ días'
        else:
            return 'Cobrado'
    
    def calculate_kpis(self) -> Dict:
        """
        Calcula KPIs principales del dashboard
        """
        if self.maestro_df is None:
            raise ValueError("Debe crear el DataFrame maestro primero")
        
        df = self.maestro_df
        
        # KPIs básicos
        facturacion_total = df['total'].sum() if 'total' in df.columns else 0
        cobranza_total = df['importe_cobrado'].sum() if 'importe_cobrado' in df.columns else 0
        anticipos_total = df['anticipos'].sum() if 'anticipos' in df.columns else 0
        
        # Porcentaje cobrado
        porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
        
        # Aging de cartera
        aging = df[df['estado_cobro'] != 'Cobrado']['estado_cobro'].value_counts().to_dict()
        
        # Top clientes
        top_clientes = df.groupby('cliente')['total'].sum().sort_values(ascending=False).head(10).to_dict()
        
        # Consumo por material
        consumo_material = df.groupby('material')['cantidad_kg'].sum().sort_values(ascending=False).head(10).to_dict()
        
        # Rotación de inventario (simplificada)
        if self.inventario_df is not None:
            rotacion_inventario = self.inventario_df['salidas'].sum() / self.inventario_df['cantidad_inicial'].sum() if self.inventario_df['cantidad_inicial'].sum() > 0 else 0
        else:
            rotacion_inventario = 0
        
        kpis = {
            'facturacion_total': facturacion_total,
            'cobranza_total': cobranza_total,
            'anticipos_total': anticipos_total,
            'porcentaje_cobrado': round(porcentaje_cobrado, 2),
            'aging_cartera': aging,
            'top_clientes': top_clientes,
            'consumo_material': consumo_material,
            'rotacion_inventario': round(rotacion_inventario, 2),
            'total_facturas': len(df),
            'clientes_unicos': df['cliente'].nunique() if 'cliente' in df.columns else 0
        }
        
        logger.info("KPIs calculados exitosamente")
        return kpis
    
    def process_file(self, file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Procesa archivo completo con detección automática de encabezados
        """
        logger.info(f"Iniciando procesamiento avanzado de archivo: {file_path}")
        
        try:
            # Cargar archivo
            sheets_data = self.load_excel_file(file_path)
            
            # Procesar cada hoja con detección automática de encabezados
            for sheet_name, df in sheets_data.items():
                sheet_lower = sheet_name.lower()
                logger.info(f"Procesando hoja: {sheet_name}")
                
                if 'facturacion' in sheet_lower:
                    processed_df = self.normalize_facturacion(df, file_path)
                    if not processed_df.empty:
                        self.facturacion_clean = processed_df
                elif 'cobranza' in sheet_lower:
                    processed_df = self.normalize_cobranza(df, file_path)
                    if not processed_df.empty:
                        self.cobranza_clean = processed_df
                elif 'cfdi' in sheet_lower or 'relacionado' in sheet_lower:
                    processed_df = self.normalize_cfdi_relacionados(df, file_path)
                    if not processed_df.empty:
                        self.cfdi_clean = processed_df
                elif any(month in sheet_lower for month in ['sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago']):
                    # Hoja de pedidos por mes
                    processed_df = self.normalize_pedidos(df, file_path, sheet_name)
                    if not processed_df.empty:
                        self.pedidos_clean = processed_df
                elif any(keyword in sheet_lower for keyword in ['pedido', 'material', 'kg']):
                    # Otra hoja de pedidos
                    processed_df = self.normalize_pedidos(df, file_path, sheet_name)
                    if not processed_df.empty:
                        self.pedidos_clean = processed_df
                elif 'inventario' in sheet_lower:
                    # Hoja de inventario
                    self.normalize_inventario(df)
            
            # Calcular relaciones entre facturación y cobranza
            if self.facturacion_df is not None and self.cobranza_df is not None:
                self.facturacion_df = self.calculate_relationships(self.facturacion_df, self.cobranza_df)
            
            # Garantizar congruencia de días de crédito entre facturas y pedidos
            if self.facturacion_df is not None and self.pedidos_df is not None:
                logger.info("🔍 Verificando congruencia de días de crédito...")
                self.facturacion_df, self.pedidos_df, discrepancias_corregidas = self.ensure_credit_days_consistency(
                    self.facturacion_df, self.pedidos_df
                )
                
                if discrepancias_corregidas > 0:
                    logger.info(f"✅ Se corrigieron {discrepancias_corregidas} discrepancias de días de crédito durante el procesamiento")
                else:
                    logger.info("✅ Los días de crédito ya eran congruentes")
                
                # Llenar automáticamente fecha_factura en pedidos usando la fecha de la factura asociada
                logger.info("📅 Llenando fecha_factura en pedidos usando datos de facturas...")
                fechas_asignadas = self.fill_pedidos_fecha_factura(self.facturacion_df, self.pedidos_df)
                logger.info(f"✅ Se asignaron {fechas_asignadas} fechas de factura a pedidos")
            
            # Crear DataFrame maestro
            master_df = self.create_master_dataframe()
            
            # Calcular KPIs
            kpis = self.calculate_kpis()
            
            # Guardar datos procesados
            self.processed_data = {
                "facturacion_clean": self.facturacion_df,
                "cobranza_clean": self.cobranza_df,
                "cfdi_clean": self.cfdi_relacionados_df,
                "pedidos_clean": self.pedidos_df,
                "inventario_clean": self.inventario_df
            }
            
            logger.info("Procesamiento completado exitosamente")
            return master_df, kpis
            
        except Exception as e:
            logger.error(f"Error en procesamiento de archivo: {str(e)}")
            raise
    
    def get_processed_data(self) -> Dict[str, pd.DataFrame]:
        """
        Retorna los datos procesados en formato estándar
        """
        return self.processed_data
    
    def export_to_json(self, output_path: str):
        """
        Exporta datos procesados a JSON
        """
        if self.maestro_df is None:
            raise ValueError("No hay datos para exportar")
        
        # Convertir fechas a string para JSON
        df_export = self.maestro_df.copy()
        for col in df_export.columns:
            if df_export[col].dtype == 'datetime64[ns]':
                df_export[col] = df_export[col].dt.strftime('%Y-%m-%d')
        
        df_export.to_json(output_path, orient='records', date_format='iso')
        logger.info(f"Datos exportados a: {output_path}")

# Función de utilidad para uso directo
def process_immermex_file(file_path: str, output_path: str = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Función de utilidad para procesar archivo de Immermex
    """
    processor = ImmermexDataProcessor()
    master_df, kpis = processor.process_file(file_path)
    
    if output_path:
        processor.export_to_json(output_path)
    
    return master_df, kpis

def process_excel_from_bytes(file_bytes: bytes, filename: str) -> Tuple[Dict[str, pd.DataFrame], Dict]:
    """
    Procesa archivo Excel desde bytes en memoria (compatible con Vercel)
    Versión simplificada que evita errores de normalización
    """
    logger.info(f"Procesando archivo desde bytes: {filename}")
    
    try:
        import io
        
        # Crear archivo temporal en memoria usando BytesIO
        file_like = io.BytesIO(file_bytes)
        
        # Leer Excel directamente desde bytes
        excel_data = pd.read_excel(file_like, sheet_name=None, engine='openpyxl')
        logger.info(f"Hojas encontradas: {list(excel_data.keys())}")
        
        processed_data = {
            "facturacion_clean": pd.DataFrame(),
            "cobranza_clean": pd.DataFrame(), 
            "cfdi_clean": pd.DataFrame(),
            "pedidos_clean": pd.DataFrame()
        }
        
            # Procesar cada hoja de forma básica (sin normalización compleja)
        for sheet_name, df in excel_data.items():
            logger.info(f"Procesando hoja: {sheet_name} con {len(df)} filas")
            logger.info(f"Columnas en {sheet_name}: {list(df.columns)}")
            
            if df.empty:
                continue
            
            # Limpiar datos básicos
            df_clean = df.copy()
            
            # Eliminar filas completamente vacías
            df_clean = df_clean.dropna(how='all')
            
            # Eliminar columnas completamente vacías
            df_clean = df_clean.dropna(axis=1, how='all')
            
            # Mapear columnas según el tipo de hoja
            if 'facturacion' in sheet_name.lower():
                df_clean = _map_facturacion_columns(df_clean)
            elif 'cobranza' in sheet_name.lower():
                df_clean = _map_cobranza_columns(df_clean)
            elif 'cfdi' in sheet_name.lower() or 'relacionado' in sheet_name.lower():
                df_clean = _map_cfdi_columns(df_clean)
            else:
                df_clean = _map_pedidos_columns(df_clean)
            
            # Log de mapeo para debugging
            logger.info(f"Columnas mapeadas en {sheet_name}: {[col for col in df_clean.columns if col in ['fecha_factura', 'serie_factura', 'folio_factura', 'cliente', 'monto_total', 'fecha_pago', 'importe_pagado', 'pedido', 'material']]}")
            
            # Agregar información de la hoja
            df_clean['hoja_origen'] = sheet_name
            df_clean['archivo_origen'] = filename
            
            # Clasificar según el tipo de hoja
            if 'facturacion' in sheet_name.lower():
                processed_data["facturacion_clean"] = pd.concat([processed_data["facturacion_clean"], df_clean], ignore_index=True)
            elif 'cobranza' in sheet_name.lower():
                processed_data["cobranza_clean"] = pd.concat([processed_data["cobranza_clean"], df_clean], ignore_index=True)
            elif 'cfdi' in sheet_name.lower() or 'relacionado' in sheet_name.lower():
                processed_data["cfdi_clean"] = pd.concat([processed_data["cfdi_clean"], df_clean], ignore_index=True)
            else:
                # Asumir que es una hoja de pedidos por mes
                processed_data["pedidos_clean"] = pd.concat([processed_data["pedidos_clean"], df_clean], ignore_index=True)
        
        # Convertir DataFrames a listas de diccionarios para la base de datos
        processed_data_dict = {}
        for key, df in processed_data.items():
            if not df.empty:
                # Convertir DataFrame a lista de diccionarios
                processed_data_dict[key] = df.to_dict('records')
                logger.info(f"{key}: {len(processed_data_dict[key])} registros convertidos")
            else:
                processed_data_dict[key] = []
        
        # Calcular KPIs básicos
        kpis = {
            "total_facturas": len(processed_data_dict["facturacion_clean"]),
            "total_cobranzas": len(processed_data_dict["cobranza_clean"]),
            "total_cfdi": len(processed_data_dict["cfdi_clean"]),
            "total_pedidos": len(processed_data_dict["pedidos_clean"]),
            "fecha_procesamiento": datetime.now().isoformat(),
            "archivo": filename,
            "hojas_procesadas": list(excel_data.keys())
        }
        
        logger.info(f"Procesamiento desde bytes completado - Facturas: {kpis['total_facturas']}, Pedidos: {kpis['total_pedidos']}")
        return processed_data_dict, kpis
        
    except Exception as e:
        logger.error(f"Error procesando archivo desde bytes: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def _convert_dias_credito(value):
    """Convierte valores de texto de días de crédito a números"""
    if pd.isna(value) or value is None:
        return 0
    
    # Convertir a string si no lo es
    str_value = str(value).strip().lower()
    
    # Si dice "contado", retornar 0 días
    if 'contado' in str_value:
        return 0
    
    # Extraer solo números del texto
    import re
    numbers = re.findall(r'\d+', str_value)
    
    if numbers:
        return int(numbers[0])  # Tomar el primer número encontrado
    
    return 0

def _map_facturacion_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de facturación usando enfoque híbrido: nombre + posición"""
    logger.info(f"=== INICIANDO MAPEO FACTURACION ===")
    logger.info(f"Columnas originales: {list(df.columns)}")
    df_mapped = df.copy()
    
    # Mapeo por nombre de columna (flexible)
    column_mapping = {
        # Fecha - múltiples variaciones
        'fecha': 'fecha_factura',
        'fecha de factura': 'fecha_factura',
        'fecha_factura': 'fecha_factura',
        'todos los documentos': 'fecha_factura',
        'Todos los Documentos': 'fecha_factura',
        'TODOS LOS DOCUMENTOS': 'fecha_factura',
        'todos los documentos.': 'fecha_factura',
        'Todos los Documentos.': 'fecha_factura',
        'Fecha': 'fecha_factura',
        
        # Serie y Folio
        'serie': 'serie_factura',
        'serie factura': 'serie_factura',
        'serie_factura': 'serie_factura',
        'Serie': 'serie_factura',
        'folio': 'folio_factura',
        'folio factura': 'folio_factura',
        'folio_factura': 'folio_factura',
        'Folio': 'folio_factura',
        
        # Cliente - múltiples variaciones
        'cliente': 'cliente',
        'razón social': 'cliente',
        'razon social': 'cliente',
        'nombre cliente': 'cliente',
        'Razón Social': 'cliente',
        
        # Montos
        'neto': 'monto_neto',
        'monto neto': 'monto_neto',
        'monto_neto': 'monto_neto',
        'subtotal': 'monto_neto',
        'Neto': 'monto_neto',
        'total': 'monto_total',
        'monto total': 'monto_total',
        'monto_total': 'monto_total',
        'importe total': 'monto_total',
        'Total': 'monto_total',
        
        # Pendiente
        'pendiente': 'saldo_pendiente',
        'saldo pendiente': 'saldo_pendiente',
        'saldo_pendiente': 'saldo_pendiente',
        'Pendiente': 'saldo_pendiente',
        
        # UUID
        'uuid': 'uuid_factura',
        'uuid_factura': 'uuid_factura',
        'UUID': 'uuid_factura',
        
        # Días de crédito
        'dias_credito': 'dias_credito',
        'dias credito': 'dias_credito',
        'días de crédito': 'dias_credito',
        'días de credito': 'dias_credito',
        'credito': 'dias_credito',
        'crédito': 'dias_credito'
    }
    
    # Mapeo por nombre (case-insensitive)
    for old_name, new_name in column_mapping.items():
        for col in df_mapped.columns:
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
    # Mapeo por posición como fallback (solo si no se encontró por nombre)
    columns = list(df_mapped.columns)
    
    if 'fecha_factura' not in df_mapped.columns and len(columns) >= 1:
        df_mapped['fecha_factura'] = df_mapped.iloc[:, 0]
    if 'serie_factura' not in df_mapped.columns and len(columns) >= 2:
        df_mapped['serie_factura'] = df_mapped.iloc[:, 1]
    if 'folio_factura' not in df_mapped.columns and len(columns) >= 3:
        df_mapped['folio_factura'] = df_mapped.iloc[:, 2]
    if 'cliente' not in df_mapped.columns and len(columns) >= 4:
        df_mapped['cliente'] = df_mapped.iloc[:, 3]
    if 'monto_neto' not in df_mapped.columns and len(columns) >= 5:
        df_mapped['monto_neto'] = df_mapped.iloc[:, 4]
    if 'monto_total' not in df_mapped.columns and len(columns) >= 6:
        df_mapped['monto_total'] = df_mapped.iloc[:, 5]
    if 'saldo_pendiente' not in df_mapped.columns and len(columns) >= 7:
        df_mapped['saldo_pendiente'] = df_mapped.iloc[:, 6]
    if 'dias_credito' not in df_mapped.columns and len(columns) >= 8:
        df_mapped['dias_credito'] = df_mapped.iloc[:, 7]    # Columna H
    if 'agente' not in df_mapped.columns and len(columns) >= 11:
        df_mapped['agente'] = df_mapped.iloc[:, 10]        # 'Unnamed: 10'
    if 'uuid_factura' not in df_mapped.columns and len(columns) >= 14:
        df_mapped['uuid_factura'] = df_mapped.iloc[:, 13]
    
    # Convertir días de crédito de texto a número
    if 'dias_credito' in df_mapped.columns:
        df_mapped['dias_credito'] = df_mapped['dias_credito'].apply(_convert_dias_credito)
    
    # Log para debugging
    mapped_cols = [col for col in df_mapped.columns if col in ['fecha_factura', 'serie_factura', 'folio_factura', 'cliente', 'monto_neto', 'monto_total', 'saldo_pendiente', 'dias_credito', 'agente', 'uuid_factura']]
    logger.info(f"Mapeo final facturación: {len(mapped_cols)} columnas mapeadas: {mapped_cols}")
    
    # Log de muestra de datos para debugging
    if 'fecha_factura' in df_mapped.columns:
        sample_dates = df_mapped['fecha_factura'].head(3).tolist()
        logger.info(f"Muestra de fechas factura: {sample_dates}")
    if 'dias_credito' in df_mapped.columns:
        sample_credito = df_mapped['dias_credito'].head(3).tolist()
        logger.info(f"Muestra de días crédito: {sample_credito}")
    
    logger.info(f"=== FINALIZANDO MAPEO FACTURACION ===")
    return df_mapped

def _map_cobranza_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de cobranza basado en estructura visual: Documentos Relacionados al Pago"""
    logger.info("=== EJECUTANDO _map_cobranza_columns ===")
    logger.info(f"Columnas originales en _map_cobranza_columns: {list(df.columns)}")
    
    df_mapped = df.copy()
    
    # Filtrar filas de encabezado que contienen texto descriptivo
    logger.info(f"Total filas antes del filtro: {len(df_mapped)}")
    
    # Identificar filas que contienen texto de encabezado
    header_keywords = [
        'documentos relacionados al pago',
        'recibo electrónico',
        'recibo electronico de pago',
        'contpaq',
        'immermex',
        'del:',
        'al:',
        'fecha',
        'periodo',
        'reporte',
        'resumen',
        'encabezado xml',
        'documento relacionado',
        'xml',
        'encabezado'
    ]
    
    # Filtrar filas que contienen texto de encabezado en cualquier columna
    mask = pd.Series([True] * len(df_mapped))
    
    for col in df_mapped.columns:
        if df_mapped[col].dtype == 'object':  # Solo columnas de texto
            # Filtro por keywords
            col_mask = df_mapped[col].astype(str).str.lower().str.contains(
                '|'.join(header_keywords), 
                na=False, 
                regex=True
            )
            mask = mask & ~col_mask  # Excluir filas que contienen keywords de encabezado
            
            # Filtro adicional para fechas de período (ej: "Del: 01/SEP/2025 Al: 28/SEP/2025")
            period_mask = df_mapped[col].astype(str).str.contains(
                r'del:\s*\d{1,2}/[a-z]{3}/\d{4}\s*al:\s*\d{1,2}/[a-z]{3}/\d{4}',
                na=False,
                regex=True,
                case=False
            )
            mask = mask & ~period_mask  # Excluir filas con fechas de período
    
    df_mapped = df_mapped[mask]
    logger.info(f"Filas después del filtro de encabezados: {len(df_mapped)}")
    
    # Filtro adicional: eliminar filas que contienen múltiples valores de encabezado
    # (indica que es una fila de encabezado con múltiples columnas de texto)
    header_count_threshold = 3  # Si una fila tiene 3+ valores que parecen encabezados, eliminarla
    
    additional_mask = pd.Series([True] * len(df_mapped))
    
    for idx, row in df_mapped.iterrows():
        header_count = 0
        for col in df_mapped.columns:
            if df_mapped[col].dtype == 'object':  # Solo columnas de texto
                cell_value = str(row[col]).lower().strip()
                # Contar si el valor parece un encabezado (texto descriptivo, no datos)
                if (cell_value and 
                    cell_value not in ['nan', 'none', 'null', ''] and
                    any(keyword in cell_value for keyword in ['recibo', 'documento', 'encabezado', 'xml', 'relacionado', 'electronico'])):
                    header_count += 1
        
        # Si tiene muchos valores que parecen encabezados, eliminarla
        if header_count >= header_count_threshold:
            additional_mask.loc[idx] = False
    
    df_mapped = df_mapped[additional_mask]
    logger.info(f"Filas después del filtro adicional de encabezados múltiples: {len(df_mapped)}")
    
    # Manejar columnas especiales (datetime, etc.)
    datetime_found = False
    for col in df_mapped.columns:
        if isinstance(col, datetime):
            # Mapear columnas datetime a fecha_pago
            logger.info(f"✅ Detectada columna datetime en _map_cobranza_columns: {col} -> fecha_pago")
            df_mapped['fecha_pago'] = df_mapped[col]
            datetime_found = True
            break
    
    if not datetime_found:
        logger.info("⚠️ No se encontraron columnas datetime en _map_cobranza_columns")
    
    # Mapeo completo basado en la referencia visual
    # RECIBO ELECTRÓNICO DE PAGO section
    column_mapping = {
        # Sección RECIBO ELECTRÓNICO DE PAGO
        'fecha pago': 'fecha_pago',
        'Fecha Pago': 'fecha_pago',
        'fecha_pago': 'fecha_pago',
        'fecha de pago': 'fecha_pago',
        'fecha cobro': 'fecha_pago',
        
        'serie pago': 'serie_pago', 
        'Serie Pago': 'serie_pago',
        'serie_pago': 'serie_pago',
        'serie de pago': 'serie_pago',
        'serie': 'serie_pago',
        
        'folio pago': 'folio_pago',
        'Folio Pago': 'folio_pago',
        'folio_pago': 'folio_pago',
        'folio de pago': 'folio_pago',
        'folio': 'folio_pago',
        
        'concepto pago': 'concepto_pago',
        'Concepto Pago': 'concepto_pago',
        'concepto_pago': 'concepto_pago',
        'concepto de pago': 'concepto_pago',
        
        'uuid del pago': 'uuid_pago',
        'UUID del Pago': 'uuid_pago',
        'uuid_pago': 'uuid_pago',
        'uuid de pago': 'uuid_pago',
        
        'cliente': 'cliente',
        'Cliente': 'cliente',
        'razón social': 'cliente',
        'razon social': 'cliente',
        
        'moneda': 'moneda',
        'Moneda': 'moneda',
        
        'tipo cambio': 'tipo_cambio',
        'Tipo Cambio': 'tipo_cambio',
        'tipo_cambio': 'tipo_cambio',
        'tipo de cambio': 'tipo_cambio',
        
        'forma pago': 'forma_pago',
        'Forma Pago': 'forma_pago',
        'forma_pago': 'forma_pago',
        'forma de pago': 'forma_pago',
        
        'no. de parciali': 'numero_parcialidades',
        'No. de Parciali': 'numero_parcialidades',
        'numero_parcialidades': 'numero_parcialidades',
        'numero de parcialidades': 'numero_parcialidades',
        'parcialidades': 'numero_parcialidades',
        
        'importe pagado': 'importe_pagado',
        'Importe Pagado': 'importe_pagado',
        'importe_pagado': 'importe_pagado',
        'importe de pago': 'importe_pagado',
        'importe': 'importe_pagado',
        'monto': 'importe_pagado',
        'total': 'importe_pagado',
        
        'número operación': 'numero_operacion',
        'Número Operación': 'numero_operacion',
        'numero_operacion': 'numero_operacion',
        'numero de operacion': 'numero_operacion',
        'operacion': 'numero_operacion',
        
        # Sección ENCABEZADO XML
        'fecha emisión': 'fecha_emision',
        'Fecha Emisión': 'fecha_emision',
        'fecha_emision': 'fecha_emision',
        'fecha de emision': 'fecha_emision',
        
        'estatus': 'estatus',
        'Estatus': 'estatus',
        'status': 'estatus',
        
        # Sección DOCUMENTO RELACIONADO
        'fecha': 'fecha_relacionado',
        'Fecha': 'fecha_relacionado',
        'fecha relacionado': 'fecha_relacionado',
        
        'serie': 'serie_relacionado',
        'Serie': 'serie_relacionado',
        'serie relacionado': 'serie_relacionado',
        
        'folio': 'folio_relacionado',
        'Folio': 'folio_relacionado',
        'folio relacionado': 'folio_relacionado',
        
        'concepto': 'concepto_relacionado',
        'Concepto': 'concepto_relacionado',
        'concepto relacionado': 'concepto_relacionado',
        
        'uuid': 'uuid_relacionado',
        'UUID': 'uuid_relacionado',
        'uuid relacionado': 'uuid_relacionado',
        'uuid factura relacionada': 'uuid_relacionado',
        'uuid_factura_relacionada': 'uuid_relacionado'
    }
    
    # Mapeo por nombre (case-insensitive)
    for old_name, new_name in column_mapping.items():
        for col in df_mapped.columns:
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
    # Mapeo por posición basado en la estructura visual
    columns = list(df_mapped.columns)
    
    # RECIBO ELECTRÓNICO DE PAGO (columnas 0-11)
    if 'fecha_pago' not in df_mapped.columns and len(columns) >= 1:
        df_mapped['fecha_pago'] = df_mapped.iloc[:, 0]  # "Fecha Pago"
    if 'serie_pago' not in df_mapped.columns and len(columns) >= 2:
        df_mapped['serie_pago'] = df_mapped.iloc[:, 1]  # "Serie Pago"
    if 'folio_pago' not in df_mapped.columns and len(columns) >= 3:
        df_mapped['folio_pago'] = df_mapped.iloc[:, 2]  # "Folio Pago"
    if 'concepto_pago' not in df_mapped.columns and len(columns) >= 4:
        df_mapped['concepto_pago'] = df_mapped.iloc[:, 3]  # "Concepto Pago"
    if 'uuid_pago' not in df_mapped.columns and len(columns) >= 5:
        df_mapped['uuid_pago'] = df_mapped.iloc[:, 4]  # "UUID del Pago"
    if 'cliente' not in df_mapped.columns and len(columns) >= 6:
        df_mapped['cliente'] = df_mapped.iloc[:, 5]  # "Cliente"
    if 'moneda' not in df_mapped.columns and len(columns) >= 7:
        df_mapped['moneda'] = df_mapped.iloc[:, 6]  # "Moneda"
    if 'tipo_cambio' not in df_mapped.columns and len(columns) >= 8:
        df_mapped['tipo_cambio'] = df_mapped.iloc[:, 7]  # "Tipo Cambio"
    if 'forma_pago' not in df_mapped.columns and len(columns) >= 9:
        df_mapped['forma_pago'] = df_mapped.iloc[:, 8]  # "Forma Pago"
    if 'numero_parcialidades' not in df_mapped.columns and len(columns) >= 10:
        df_mapped['numero_parcialidades'] = df_mapped.iloc[:, 9]  # "No. de Parciali"
    if 'importe_pagado' not in df_mapped.columns and len(columns) >= 11:
        df_mapped['importe_pagado'] = df_mapped.iloc[:, 10]  # "Importe Pagado"
    if 'numero_operacion' not in df_mapped.columns and len(columns) >= 12:
        df_mapped['numero_operacion'] = df_mapped.iloc[:, 11]  # "Número Operación"
    
    # ENCABEZADO XML (columnas 12-13)
    if 'fecha_emision' not in df_mapped.columns and len(columns) >= 13:
        df_mapped['fecha_emision'] = df_mapped.iloc[:, 12]  # "Fecha Emisión"
    if 'estatus' not in df_mapped.columns and len(columns) >= 14:
        df_mapped['estatus'] = df_mapped.iloc[:, 13]  # "Estatus"
    
    # DOCUMENTO RELACIONADO (columnas 14-18)
    if 'fecha_relacionado' not in df_mapped.columns and len(columns) >= 15:
        df_mapped['fecha_relacionado'] = df_mapped.iloc[:, 14]  # "Fecha"
    if 'serie_relacionado' not in df_mapped.columns and len(columns) >= 16:
        df_mapped['serie_relacionado'] = df_mapped.iloc[:, 15]  # "Serie"
    if 'folio_relacionado' not in df_mapped.columns and len(columns) >= 17:
        df_mapped['folio_relacionado'] = df_mapped.iloc[:, 16]  # "Folio"
    if 'concepto_relacionado' not in df_mapped.columns and len(columns) >= 18:
        df_mapped['concepto_relacionado'] = df_mapped.iloc[:, 17]  # "Concepto"
    if 'uuid_relacionado' not in df_mapped.columns and len(columns) >= 19:
        df_mapped['uuid_relacionado'] = df_mapped.iloc[:, 18]  # "UUID"
    
    # Valores por defecto para campos no encontrados
    default_values = {
        'fecha_pago': None,
        'serie_pago': '',
        'folio_pago': '',
        'concepto_pago': '',
        'uuid_pago': '',
        'cliente': '',
        'moneda': 'MXN',
        'tipo_cambio': 1.0,
        'forma_pago': '',
        'numero_parcialidades': 1,
        'importe_pagado': 0.0,
        'numero_operacion': '',
        'fecha_emision': None,
        'estatus': '',
        'fecha_relacionado': None,
        'serie_relacionado': '',
        'folio_relacionado': '',
        'concepto_relacionado': '',
        'uuid_relacionado': ''
    }
    
    for field, default_value in default_values.items():
        if field not in df_mapped.columns:
            df_mapped[field] = default_value
    
    # Log para debugging
    mapped_cols = [col for col in df_mapped.columns if col in default_values.keys()]
    logger.info(f"Mapeo final cobranza: {len(mapped_cols)} columnas mapeadas: {mapped_cols}")
    
    return df_mapped

def _map_cfdi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de CFDI a nombres estándar"""
    df_mapped = df.copy()
    
    # Mapeo completo para CFDI
    column_mapping = {
        'xml': 'xml',
        'XML': 'xml',
        'Fecha': 'fecha_cfdi',
        'Total': 'importe_relacion',
        'UUID': 'uuid_factura_relacionada',
        'Nombre Receptor': 'cliente_receptor',
        'Tipo Relación': 'tipo_relacion'
    }
    
    # Mapeo por nombre (case-insensitive)
    for old_name, new_name in column_mapping.items():
        for col in df_mapped.columns:
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
    # Mapeo por posición como fallback
    columns = list(df_mapped.columns)
    if 'xml' not in df_mapped.columns and len(columns) >= 1:
        df_mapped['xml'] = df_mapped.iloc[:, 0]             # 'XML'
    if 'fecha_cfdi' not in df_mapped.columns and len(columns) >= 14:
        df_mapped['fecha_cfdi'] = df_mapped.iloc[:, 13]     # 'Fecha'
    if 'importe_relacion' not in df_mapped.columns and len(columns) >= 21:
        df_mapped['importe_relacion'] = df_mapped.iloc[:, 20] # 'Total'
    if 'uuid_factura_relacionada' not in df_mapped.columns and len(columns) >= 22:
        df_mapped['uuid_factura_relacionada'] = df_mapped.iloc[:, 21] # 'UUID'
    if 'cliente_receptor' not in df_mapped.columns and len(columns) >= 7:
        df_mapped['cliente_receptor'] = df_mapped.iloc[:, 6] # 'Nombre Receptor'
    if 'tipo_relacion' not in df_mapped.columns and len(columns) >= 34:
        df_mapped['tipo_relacion'] = df_mapped.iloc[:, 33]  # 'Tipo Relación'
    
    # Valores por defecto
    if 'xml' not in df_mapped.columns:
        df_mapped['xml'] = ''
    if 'importe_relacion' not in df_mapped.columns:
        df_mapped['importe_relacion'] = 0.0
    if 'cliente_receptor' not in df_mapped.columns:
        df_mapped['cliente_receptor'] = ''
    if 'tipo_relacion' not in df_mapped.columns:
        df_mapped['tipo_relacion'] = ''
    if 'uuid_factura_relacionada' not in df_mapped.columns:
        df_mapped['uuid_factura_relacionada'] = ''
    
    # Log para debugging
    logger.info(f"Mapeo final CFDI: {len([col for col in df_mapped.columns if col in ['xml', 'fecha_cfdi', 'importe_relacion', 'cliente_receptor', 'tipo_relacion', 'uuid_factura_relacionada']])} columnas mapeadas")
    
    return df_mapped

def _map_pedidos_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de pedidos a nombres estándar usando estructura real de Excel"""
    df_mapped = df.copy()
    
    # Mapeo completo para pedidos basado en la estructura real
    column_mapping = {
        'no de factura': 'folio_factura',
        'No de factura': 'folio_factura',
        'pedido': 'pedido',
        'Pedido': 'pedido',
        'kgs': 'kg',
        'KGS': 'kg',
        'precio unitario': 'precio_unitario',
        'Precio unitario': 'precio_unitario',
        'importe mxn sin iva': 'importe_sin_iva',
        'Importe mxn sin iva': 'importe_sin_iva',
        'material': 'material',
        'Matertial': 'material',  # Con el typo que aparece en Excel
        'nombre de cliente': 'cliente',
        'nom,bre de cliente': 'cliente',  # Con el typo que aparece en Excel
        'dias de credito': 'dias_credito',
        'dias de crédito': 'dias_credito',
        'fecha factura': 'fecha_factura',
        'fecha_factura': 'fecha_factura'
    }
    
    # Mapeo por nombre (case-insensitive)
    for old_name, new_name in column_mapping.items():
        for col in df_mapped.columns:
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
    # Mapeo por posición como fallback basado en la estructura real
    columns = list(df_mapped.columns)
    
    # Mapeo por posición según la estructura real de Excel
    if 'folio_factura' not in df_mapped.columns and len(columns) >= 1:
        df_mapped['folio_factura'] = df_mapped.iloc[:, 0]  # A6: "No de factura"
    if 'pedido' not in df_mapped.columns and len(columns) >= 3:
        df_mapped['pedido'] = df_mapped.iloc[:, 2]         # C6: "Pedido"
    if 'kg' not in df_mapped.columns and len(columns) >= 4:
        df_mapped['kg'] = df_mapped.iloc[:, 3]             # D6: "KGS"
    if 'precio_unitario' not in df_mapped.columns and len(columns) >= 5:
        df_mapped['precio_unitario'] = df_mapped.iloc[:, 4] # E6: "Precio unitario"
    if 'importe_sin_iva' not in df_mapped.columns and len(columns) >= 6:
        df_mapped['importe_sin_iva'] = df_mapped.iloc[:, 5] # F6: "Importe mxn sin iva"
    if 'material' not in df_mapped.columns and len(columns) >= 7:
        df_mapped['material'] = df_mapped.iloc[:, 6]       # G6: "Matertial"
    if 'cliente' not in df_mapped.columns and len(columns) >= 8:
        df_mapped['cliente'] = df_mapped.iloc[:, 7]        # H6: "nom,bre de cliente"
    if 'dias_credito' not in df_mapped.columns and len(columns) >= 9:
        df_mapped['dias_credito'] = df_mapped.iloc[:, 8]   # I6: "dias de credito"
    if 'fecha_factura' not in df_mapped.columns and len(columns) >= 10:
        df_mapped['fecha_factura'] = df_mapped.iloc[:, 9]  # J6: "fecha factura"
    
    # Valores por defecto para campos no encontrados
    if 'folio_factura' not in df_mapped.columns:
        df_mapped['folio_factura'] = ''
    if 'pedido' not in df_mapped.columns:
        df_mapped['pedido'] = ''
    if 'kg' not in df_mapped.columns:
        df_mapped['kg'] = 0.0
    if 'precio_unitario' not in df_mapped.columns:
        df_mapped['precio_unitario'] = 0.0
    if 'importe_sin_iva' not in df_mapped.columns:
        df_mapped['importe_sin_iva'] = 0.0
    if 'material' not in df_mapped.columns:
        df_mapped['material'] = ''
    if 'cliente' not in df_mapped.columns:
        df_mapped['cliente'] = ''
    if 'dias_credito' not in df_mapped.columns:
        df_mapped['dias_credito'] = 30
    if 'fecha_factura' not in df_mapped.columns:
        df_mapped['fecha_factura'] = None
    
    # Log para debugging
    logger.info(f"Mapeo final pedidos: {len([col for col in df_mapped.columns if col in ['folio_factura', 'pedido', 'kg', 'precio_unitario', 'importe_sin_iva', 'material', 'cliente', 'dias_credito', 'fecha_factura']])} columnas mapeadas")
    
    return df_mapped

def load_and_clean_excel(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Función de conveniencia que integra el procesador avanzado
    Compatible con el excel_processor.py original
    """
    processor = ImmermexDataProcessor()
    processor.process_file(file_path)
    return processor.get_processed_data()

def process_immermex_file_advanced(file_path: str) -> Tuple[Dict[str, pd.DataFrame], Dict]:
    """
    Función avanzada que retorna tanto datos procesados como KPIs
    """
    processor = ImmermexDataProcessor()
    master_df, kpis = processor.process_file(file_path)
    processed_data = processor.get_processed_data()
    
    return processed_data, kpis

if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python data_processor.py <archivo_excel> [archivo_salida.json]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        master_df, kpis = process_immermex_file(file_path, output_path)
        print(f"Procesamiento exitoso: {len(master_df)} registros")
        print(f"KPIs calculados: {len(kpis)} métricas")
    except Exception as e:
        print(f"Error en el procesamiento: {str(e)}")
        sys.exit(1)
