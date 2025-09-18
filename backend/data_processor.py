"""
Script de limpieza y normalización de datos para Immermex Dashboard
Procesa archivos Excel mensuales y extrae datos según el diccionario de extracción
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
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
    """
    
    def __init__(self):
        self.facturacion_df = None
        self.cobranza_df = None
        self.cfdi_relacionados_df = None
        self.inventario_df = None
        self.maestro_df = None
        
    def load_excel_file(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Carga archivo Excel y extrae todas las hojas
        """
        try:
            logger.info(f"Cargando archivo: {file_path}")
            
            # Leer todas las hojas del Excel
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                logger.info(f"Procesando hoja: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheets_data[sheet_name] = df
                logger.info(f"Hoja '{sheet_name}' cargada: {df.shape[0]} filas, {df.shape[1]} columnas")
            
            return sheets_data
            
        except Exception as e:
            logger.error(f"Error cargando archivo Excel: {str(e)}")
            raise
    
    def normalize_facturacion(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza datos de facturación según diccionario de extracción
        """
        logger.info("Normalizando datos de facturación...")
        
        # Mapeo de columnas esperadas (ajustar según diccionario real)
        column_mapping = {
            'Folio': 'folio',
            'Fecha': 'fecha_factura',
            'Cliente': 'cliente',
            'Agente': 'agente',
            'Importe': 'importe_factura',
            'UUID': 'uuid',
            'Pedido': 'numero_pedido',
            'Material': 'material',
            'Cantidad': 'cantidad_kg',
            'Precio Unitario': 'precio_unitario',
            'Subtotal': 'subtotal',
            'IVA': 'iva',
            'Total': 'total'
        }
        
        # Renombrar columnas si existen
        df_clean = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_clean.columns:
                df_clean = df_clean.rename(columns={old_col: new_col})
        
        # Normalizar fechas
        if 'fecha_factura' in df_clean.columns:
            df_clean['fecha_factura'] = pd.to_datetime(df_clean['fecha_factura'], errors='coerce')
        
        # Normalizar importes numéricos
        numeric_columns = ['importe_factura', 'cantidad_kg', 'precio_unitario', 'subtotal', 'iva', 'total']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Limpiar UUIDs
        if 'uuid' in df_clean.columns:
            df_clean['uuid'] = df_clean['uuid'].astype(str).str.strip()
            df_clean['uuid'] = df_clean['uuid'].replace('nan', None)
        
        # Limpiar folios
        if 'folio' in df_clean.columns:
            df_clean['folio'] = df_clean['folio'].astype(str).str.strip()
            df_clean['folio'] = df_clean['folio'].replace('nan', None)
        
        # Agregar campos calculados
        df_clean['mes'] = df_clean['fecha_factura'].dt.month if 'fecha_factura' in df_clean.columns else None
        df_clean['año'] = df_clean['fecha_factura'].dt.year if 'fecha_factura' in df_clean.columns else None
        
        self.facturacion_df = df_clean
        logger.info(f"Facturación normalizada: {df_clean.shape[0]} registros")
        return df_clean
    
    def normalize_cobranza(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza datos de cobranza
        """
        logger.info("Normalizando datos de cobranza...")
        
        column_mapping = {
            'Folio': 'folio',
            'Fecha Cobro': 'fecha_cobro',
            'Cliente': 'cliente',
            'Importe Cobrado': 'importe_cobrado',
            'Forma Pago': 'forma_pago',
            'Referencia': 'referencia_pago',
            'UUID': 'uuid'
        }
        
        df_clean = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_clean.columns:
                df_clean = df_clean.rename(columns={old_col: new_col})
        
        # Normalizar fechas
        if 'fecha_cobro' in df_clean.columns:
            df_clean['fecha_cobro'] = pd.to_datetime(df_clean['fecha_cobro'], errors='coerce')
        
        # Normalizar importes
        if 'importe_cobrado' in df_clean.columns:
            df_clean['importe_cobrado'] = pd.to_numeric(df_clean['importe_cobrado'], errors='coerce')
        
        # Limpiar UUIDs y folios
        for col in ['uuid', 'folio']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                df_clean[col] = df_clean[col].replace('nan', None)
        
        self.cobranza_df = df_clean
        logger.info(f"Cobranza normalizada: {df_clean.shape[0]} registros")
        return df_clean
    
    def normalize_cfdi_relacionados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza datos de CFDIs relacionados (anticipos/notas de crédito)
        """
        logger.info("Normalizando datos de CFDIs relacionados...")
        
        column_mapping = {
            'UUID': 'uuid',
            'Tipo': 'tipo_cfdi',
            'Fecha': 'fecha_cfdi',
            'Cliente': 'cliente',
            'Importe': 'importe_cfdi',
            'Folio Relacionado': 'folio_relacionado',
            'Concepto': 'concepto'
        }
        
        df_clean = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_clean.columns:
                df_clean = df_clean.rename(columns={old_col: new_col})
        
        # Normalizar fechas
        if 'fecha_cfdi' in df_clean.columns:
            df_clean['fecha_cfdi'] = pd.to_datetime(df_clean['fecha_cfdi'], errors='coerce')
        
        # Normalizar importes
        if 'importe_cfdi' in df_clean.columns:
            df_clean['importe_cfdi'] = pd.to_numeric(df_clean['importe_cfdi'], errors='coerce')
        
        # Limpiar UUIDs
        if 'uuid' in df_clean.columns:
            df_clean['uuid'] = df_clean['uuid'].astype(str).str.strip()
            df_clean['uuid'] = df_clean['uuid'].replace('nan', None)
        
        self.cfdi_relacionados_df = df_clean
        logger.info(f"CFDIs relacionados normalizados: {df_clean.shape[0]} registros")
        return df_clean
    
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
        master_df['dias_vencimiento'] = (master_df['fecha_cobro'] - master_df['fecha_factura']).dt.days
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
        Procesa archivo completo y retorna DataFrame maestro y KPIs
        """
        logger.info(f"Iniciando procesamiento de archivo: {file_path}")
        
        # Cargar archivo
        sheets_data = self.load_excel_file(file_path)
        
        # Procesar cada hoja según su nombre
        for sheet_name, df in sheets_data.items():
            sheet_lower = sheet_name.lower()
            
            if 'facturacion' in sheet_lower:
                self.normalize_facturacion(df)
            elif 'cobranza' in sheet_lower:
                self.normalize_cobranza(df)
            elif 'cfdi' in sheet_lower or 'relacionado' in sheet_lower:
                self.normalize_cfdi_relacionados(df)
            elif any(month in sheet_lower for month in ['sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago']):
                # Hoja de inventario por mes
                self.normalize_inventario(df)
        
        # Crear DataFrame maestro
        master_df = self.create_master_dataframe()
        
        # Calcular KPIs
        kpis = self.calculate_kpis()
        
        logger.info("Procesamiento completado exitosamente")
        return master_df, kpis
    
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
