"""
Procesador de archivos Excel para Immermex Dashboard
Limpia y normaliza datos de archivos Excel mensuales según especificaciones
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

class ImmermexExcelProcessor:
    """
    Procesador especializado para archivos Excel de Immermex
    """
    
    def __init__(self):
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
            
            for idx, row in preview.iterrows():
                row_str = ' '.join(row.astype(str).fillna(''))
                if any(keyword.lower() in row_str.lower() for keyword in keywords):
                    logger.info(f"Encabezados encontrados en fila {idx} para hoja '{sheet_name}'")
                    return idx
            
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
    
    def clean_facturacion(self, path: str) -> pd.DataFrame:
        """
        Limpia y normaliza datos de facturación
        
        Args:
            path: Ruta del archivo Excel
            
        Returns:
            DataFrame limpio de facturación
        """
        try:
            # Detectar fila de encabezados
            keywords = ['fecha', 'serie', 'folio', 'cliente', 'razón social']
            header_row = self.detect_header_row(path, "facturacion", keywords)
            
            # Leer datos
            df = pd.read_excel(path, sheet_name="facturacion", header=header_row)
            logger.info(f"Facturación: {len(df)} registros leídos")
            
            # Mapeo de columnas (flexible para diferentes formatos)
            column_mapping = {
                # Fecha
                'fecha': 'fecha_factura',
                'fecha de factura': 'fecha_factura',
                'fecha_factura': 'fecha_factura',
                
                # Serie y Folio
                'serie': 'serie_factura',
                'serie factura': 'serie_factura',
                'serie_factura': 'serie_factura',
                
                'folio': 'folio_factura',
                'folio factura': 'folio_factura',
                'folio_factura': 'folio_factura',
                
                # Cliente
                'cliente': 'cliente',
                'razón social': 'cliente',
                'razon social': 'cliente',
                'nombre cliente': 'cliente',
                
                # Montos
                'neto': 'monto_neto',
                'monto neto': 'monto_neto',
                'monto_neto': 'monto_neto',
                'subtotal': 'monto_neto',
                
                'total': 'monto_total',
                'monto total': 'monto_total',
                'monto_total': 'monto_total',
                'importe total': 'monto_total',
                
                'pendiente': 'saldo_pendiente',
                'saldo pendiente': 'saldo_pendiente',
                'saldo_pendiente': 'saldo_pendiente',
                'pendiente de pago': 'saldo_pendiente',
                
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
                'folio fiscal': 'uuid_factura'
            }
            
            # Renombrar columnas
            df_renamed = df.copy()
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df_renamed = df_renamed.rename(columns={old_name: new_name})
            
            # Crear DataFrame con columnas estándar
            clean_df = pd.DataFrame()
            
            # Fecha de factura
            clean_df['fecha_factura'] = pd.to_datetime(
                df_renamed.get('fecha_factura', ''), errors='coerce'
            )
            
            # Serie y folio
            clean_df['serie_factura'] = self.clean_string_column(
                df_renamed.get('serie_factura', '')
            )
            clean_df['folio_factura'] = self.clean_string_column(
                df_renamed.get('folio_factura', '')
            )
            
            # Cliente
            clean_df['cliente'] = self.clean_string_column(
                df_renamed.get('cliente', '')
            )
            
            # Montos numéricos
            for col in ['monto_neto', 'monto_total', 'saldo_pendiente']:
                clean_df[col] = pd.to_numeric(
                    df_renamed.get(col, 0), errors='coerce'
                ).fillna(0)
            
            # Condiciones de pago (extraer días de crédito)
            condiciones = df_renamed.get('condiciones_pago', '')
            clean_df['dias_credito'] = pd.to_numeric(
                condiciones.astype(str).str.extract(r'(\d+)')[0], errors='coerce'
            ).fillna(30)  # Default 30 días
            
            # Agente
            clean_df['agente'] = self.clean_string_column(
                df_renamed.get('agente', '')
            )
            
            # UUID
            clean_df['uuid_factura'] = self.clean_uuid(
                df_renamed.get('uuid_factura', '')
            )
            
            # Eliminar filas completamente vacías
            clean_df = clean_df.dropna(how='all')
            
            # Eliminar duplicados por UUID
            clean_df = clean_df.drop_duplicates(subset=['uuid_factura'], keep='first')
            
            logger.info(f"Facturación limpia: {len(clean_df)} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error procesando facturación: {str(e)}")
            return pd.DataFrame()
    
    def clean_cobranza(self, path: str) -> pd.DataFrame:
        """
        Limpia y normaliza datos de cobranza
        
        Args:
            path: Ruta del archivo Excel
            
        Returns:
            DataFrame limpio de cobranza
        """
        try:
            # Detectar fila de encabezados
            keywords = ['fecha', 'pago', 'cliente', 'importe', 'uuid']
            header_row = self.detect_header_row(path, "cobranza", keywords)
            
            # Leer datos
            df = pd.read_excel(path, sheet_name="cobranza", header=header_row)
            logger.info(f"Cobranza: {len(df)} registros leídos")
            
            # Mapeo de columnas
            column_mapping = {
                'fecha de pago': 'fecha_pago',
                'fecha_pago': 'fecha_pago',
                'fecha pago': 'fecha_pago',
                
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
                
                'uuid factura relacionada': 'uuid_factura_relacionada',
                'uuid_factura_relacionada': 'uuid_factura_relacionada',
                'uuid relacionada': 'uuid_factura_relacionada',
                'folio fiscal relacionado': 'uuid_factura_relacionada'
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
            
            logger.info(f"Cobranza limpia: {len(clean_df)} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error procesando cobranza: {str(e)}")
            return pd.DataFrame()
    
    def clean_cfdi(self, path: str) -> pd.DataFrame:
        """
        Limpia y normaliza datos de CFDI relacionados
        
        Args:
            path: Ruta del archivo Excel
            
        Returns:
            DataFrame limpio de CFDI
        """
        try:
            # Detectar fila de encabezados
            keywords = ['xml', 'cliente', 'tipo', 'relacion', 'importe', 'uuid']
            header_row = self.detect_header_row(path, "cfdi relacionados", keywords)
            
            # Leer datos
            df = pd.read_excel(path, sheet_name="cfdi relacionados", header=header_row)
            logger.info(f"CFDI: {len(df)} registros leídos")
            
            # Mapeo de columnas
            column_mapping = {
                'xml': 'xml',
                'uuid cfdi': 'xml',
                'uuid_cfdi': 'xml',
                'folio fiscal': 'xml',
                
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
                
                'uuid factura relacionada': 'uuid_factura_relacionada',
                'uuid_factura_relacionada': 'uuid_factura_relacionada',
                'uuid relacionada': 'uuid_factura_relacionada',
                'folio fiscal relacionado': 'uuid_factura_relacionada'
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
            
            logger.info(f"CFDI limpio: {len(clean_df)} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error procesando CFDI: {str(e)}")
            return pd.DataFrame()
    
    def clean_pedidos(self, path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Limpia y normaliza datos de pedidos
        
        Args:
            path: Ruta del archivo Excel
            sheet_name: Nombre de la hoja de pedidos (se detecta automáticamente si es None)
            
        Returns:
            DataFrame limpio de pedidos
        """
        try:
            # Detectar hoja de pedidos si no se especifica
            if sheet_name is None:
                excel_file = pd.ExcelFile(path)
                pedido_sheets = [s for s in excel_file.sheet_names 
                               if any(keyword in s.lower() for keyword in ['pedido', 'sep', 'oct', 'nov', 'dic'])]
                if pedido_sheets:
                    sheet_name = pedido_sheets[0]
                    logger.info(f"Hoja de pedidos detectada: {sheet_name}")
                else:
                    logger.warning("No se encontró hoja de pedidos")
                    return pd.DataFrame()
            
            # Detectar fila de encabezados
            keywords = ['factura', 'pedido', 'kg', 'precio', 'material']
            header_row = self.detect_header_row(path, sheet_name, keywords)
            
            # Leer datos
            df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
            logger.info(f"Pedidos: {len(df)} registros leídos")
            
            # Mapeo de columnas
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
            
            logger.info(f"Pedidos limpios: {len(clean_df)} registros")
            return clean_df
            
        except Exception as e:
            logger.error(f"Error procesando pedidos: {str(e)}")
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
    
    def load_and_clean_excel(self, path: str) -> Dict[str, pd.DataFrame]:
        """
        Función principal que carga y limpia el archivo Excel completo
        
        Args:
            path: Ruta del archivo Excel
            
        Returns:
            Diccionario con DataFrames limpios
        """
        try:
            logger.info(f"Iniciando procesamiento de archivo: {path}")
            
            # Verificar que el archivo existe
            if not Path(path).exists():
                raise FileNotFoundError(f"Archivo no encontrado: {path}")
            
            # Procesar cada hoja
            facturacion_clean = self.clean_facturacion(path)
            cobranza_clean = self.clean_cobranza(path)
            cfdi_clean = self.clean_cfdi(path)
            pedidos_compras_clean = self.clean_pedidos(path)
            
            # Calcular relaciones
            if not facturacion_clean.empty and not cobranza_clean.empty:
                facturacion_clean = self.calculate_relationships(facturacion_clean, cobranza_clean)
            
            # Preparar resultado
            result = {
                "facturacion_clean": facturacion_clean,
                "cobranza_clean": cobranza_clean,
                "cfdi_clean": cfdi_clean,
                "pedidos_compras_clean": pedidos_compras_clean
            }
            
            # Log de resumen
            logger.info("Procesamiento completado:")
            for key, df in result.items():
                logger.info(f"  {key}: {len(df)} registros")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en procesamiento principal: {str(e)}")
            return {
                "facturacion_clean": pd.DataFrame(),
                "cobranza_clean": pd.DataFrame(),
                "cfdi_clean": pd.DataFrame(),
                "pedidos_compras_clean": pd.DataFrame()
            }


# Función de conveniencia para uso directo
def load_and_clean_excel(path: str) -> Dict[str, pd.DataFrame]:
    """
    Función de conveniencia para cargar y limpiar archivo Excel
    
    Args:
        path: Ruta del archivo Excel
        
    Returns:
        Diccionario con DataFrames limpios
    """
    processor = ImmermexExcelProcessor()
    return processor.load_and_clean_excel(path)


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python excel_processor.py <archivo_excel>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        # Configurar logging para ejemplo
        logging.basicConfig(level=logging.INFO)
        
        # Procesar archivo
        data = load_and_clean_excel(file_path)
        
        print("\n=== RESUMEN DE PROCESAMIENTO ===")
        for key, df in data.items():
            print(f"{key}: {len(df)} registros")
            if not df.empty:
                print(f"  Columnas: {list(df.columns)}")
                print(f"  Muestra de datos:")
                print(df.head(2).to_string())
                print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
