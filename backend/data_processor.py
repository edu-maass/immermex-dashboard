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
            
            # Condiciones de pago (extraer días de crédito)
            condiciones = df_renamed.get('condiciones_pago', pd.Series())
            if isinstance(condiciones, str):
                condiciones = pd.Series([condiciones])
            clean_df['dias_credito'] = pd.to_numeric(
                condiciones.astype(str).str.extract(r'(\d+)')[0], errors='coerce'
            ).fillna(30)  # Default 30 días
            
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
                    self.normalize_facturacion(df, file_path)
                elif 'cobranza' in sheet_lower:
                    self.normalize_cobranza(df, file_path)
                elif 'cfdi' in sheet_lower or 'relacionado' in sheet_lower:
                    self.normalize_cfdi_relacionados(df, file_path)
                elif any(month in sheet_lower for month in ['sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago']):
                    # Hoja de pedidos por mes
                    self.normalize_pedidos(df, file_path, sheet_name)
                elif any(keyword in sheet_lower for keyword in ['pedido', 'material', 'kg']):
                    # Otra hoja de pedidos
                    self.normalize_pedidos(df, file_path, sheet_name)
                elif 'inventario' in sheet_lower:
                    # Hoja de inventario
                    self.normalize_inventario(df)
            
            # Calcular relaciones entre facturación y cobranza
            if self.facturacion_df is not None and self.cobranza_df is not None:
                self.facturacion_df = self.calculate_relationships(self.facturacion_df, self.cobranza_df)
            
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

def _map_facturacion_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de facturación a nombres estándar usando el mapeo original que funcionaba"""
    df_mapped = df.copy()
    
    # Mapeo de columnas flexible y completo (copiado del método original)
    column_mapping = {
        # Fecha
        'fecha': 'fecha_factura',
        'fecha de factura': 'fecha_factura',
        'fecha_factura': 'fecha_factura',
        'todos los documentos': 'fecha_factura',
        'Fecha': 'fecha_factura',
        
        # Serie y Folio
        'serie': 'serie_factura',
        'serie factura': 'serie_factura',
        'serie_factura': 'serie_factura',
        'unnamed: 1': 'serie_factura',
        'Serie': 'serie_factura',
        'folio': 'folio_factura',
        'folio factura': 'folio_factura',
        'folio_factura': 'folio_factura',
        'unnamed: 2': 'folio_factura',
        'Folio': 'folio_factura',
        
        # Cliente
        'cliente': 'cliente',
        'razón social': 'cliente',
        'razon social': 'cliente',
        'nombre cliente': 'cliente',
        'unnamed: 3': 'cliente',
        'Razón Social': 'cliente',
        
        # Montos
        'neto': 'monto_neto',
        'monto neto': 'monto_neto',
        'monto_neto': 'monto_neto',
        'subtotal': 'monto_neto',
        'unnamed: 4': 'monto_neto',
        'Neto': 'monto_neto',
        'total': 'monto_total',
        'monto total': 'monto_total',
        'monto_total': 'monto_total',
        'importe total': 'monto_total',
        'unnamed: 5': 'monto_total',
        'Total': 'monto_total',
        
        # Pendiente
        'pendiente': 'saldo_pendiente',
        'saldo pendiente': 'saldo_pendiente',
        'saldo_pendiente': 'saldo_pendiente',
        'unnamed: 6': 'saldo_pendiente',
        'Pendiente': 'saldo_pendiente',
        
        # Agente
        'agente': 'agente',
        'nombre del agente': 'agente',
        'vendedor': 'agente',
        'Nombre del agente': 'agente',
        
        # UUID
        'uuid': 'uuid_factura',
        'uuid_factura': 'uuid_factura',
        'unnamed: 13': 'uuid_factura',
        'UUID': 'uuid_factura'
    }
    
    # Renombrar columnas que existen (case-insensitive)
    for old_name, new_name in column_mapping.items():
        # Buscar coincidencia exacta o case-insensitive
        for col in df_mapped.columns:
            # Verificar que la columna sea string antes de hacer .lower()
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
    return df_mapped

def _map_cobranza_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de cobranza a nombres estándar usando el mapeo original"""
    df_mapped = df.copy()
    
    # Manejar columnas especiales (datetime, etc.)
    for col in df_mapped.columns:
        if isinstance(col, datetime.datetime):
            # Mapear columnas datetime a fecha_pago
            df_mapped['fecha_pago'] = df_mapped[col]
            break
    
    # Mapeo de columnas flexible y completo (copiado del método original)
    column_mapping = {
        'fecha de pago': 'fecha_pago',
        'fecha_pago': 'fecha_pago',
        'fecha pago': 'fecha_pago',
        'fecha cobro': 'fecha_pago',
        'Fecha': 'fecha_pago',
        
        'serie pago': 'serie_pago',
        'serie_pago': 'serie_pago',
        'serie': 'serie_pago',
        'Serie': 'serie_pago',
        
        'folio pago': 'folio_pago',
        'folio_pago': 'folio_pago',
        'folio': 'folio_pago',
        'Folio': 'folio_pago',
        
        'cliente': 'cliente',
        'razón social': 'cliente',
        'razon social': 'cliente',
        'Cliente': 'cliente',
        
        'moneda': 'moneda',
        'tipo de cambio': 'tipo_cambio',
        'tipo_cambio': 'tipo_cambio',
        
        'forma de pago': 'forma_pago',
        'forma_pago': 'forma_pago',
        'método de pago': 'metodo_pago',
        'metodo_pago': 'metodo_pago',
        
        'importe pagado': 'importe_pagado',
        'importe_pagado': 'importe_pagado',
        'importe': 'importe_pagado',
        'Importe': 'importe_pagado',
        'monto': 'importe_pagado',
        'total': 'importe_pagado',
        
        'uuid': 'uuid_pago',
        'uuid_pago': 'uuid_pago',
        'UUID': 'uuid_pago'
    }
    
    # Renombrar columnas que existen (case-insensitive)
    for old_name, new_name in column_mapping.items():
        for col in df_mapped.columns:
            # Verificar que la columna sea string antes de hacer .lower()
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
    return df_mapped

def _map_cfdi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de CFDI a nombres estándar"""
    df_mapped = df.copy()
    
    # Mapeo básico para CFDI
    column_mapping = {
        'Fecha': 'fecha_cfdi',
        'Total': 'importe_relacion',
        'UUID': 'uuid_cfdi'
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in df_mapped.columns:
            df_mapped[new_name] = df_mapped[old_name]
    
    return df_mapped

def _map_pedidos_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas de pedidos a nombres estándar usando el mapeo original"""
    df_mapped = df.copy()
    
    # Mapeo de columnas flexible y completo (copiado del método original)
    column_mapping = {
        'no de factura': 'folio_factura',
        'folio factura': 'folio_factura',
        'folio_factura': 'folio_factura',
        'factura': 'folio_factura',
        'numero factura': 'folio_factura',
        'Fecha': 'fecha_factura',
        
        'pedido': 'pedido',
        'numero pedido': 'pedido',
        'numero_pedido': 'pedido',
        'no pedido': 'pedido',
        'Pedido': 'pedido',
        'unnamed: 0': 'pedido',
        
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
        'monto_total': 'importe_sin_iva',
        'Total': 'importe_sin_iva',
        
        'material': 'material',
        'producto': 'material',
        'descripcion': 'material',
        
        'dias de credito': 'dias_credito',
        'dias_credito': 'dias_credito',
        
        'cliente': 'cliente',
        'Cliente': 'cliente',
        'CONTPAQ i': 'cliente',
        'razón social': 'cliente',
        'razon social': 'cliente'
    }
    
    # Renombrar columnas que existen (case-insensitive)
    for old_name, new_name in column_mapping.items():
        for col in df_mapped.columns:
            # Verificar que la columna sea string antes de hacer .lower()
            if isinstance(col, str) and col.lower() == old_name.lower():
                df_mapped[new_name] = df_mapped[col]
                break
    
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
