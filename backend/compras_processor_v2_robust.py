"""
Procesador robusto para compras_v2 y compras_v2_materiales
Version optimizada con manejo robusto de columnas y calculos automaticos
"""

import pandas as pd
import io
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
import logging
from decimal import Decimal
import re

logger = logging.getLogger(__name__)

class ComprasV2Processor:
    """
    Procesador robusto para archivos Excel de compras
    Optimizado para compras_v2 y compras_v2_materiales
    """
    
    def __init__(self):
        self.proveedores_data = None
        self.load_proveedores_data()
    
    def load_production_config(self):
        """Carga la configuración desde production.env"""
        env_file = "production.env"
        
        if not os.path.exists(env_file):
            logger.error(f"Archivo {env_file} no encontrado")
            return None
        
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        
        return config
    
    def get_supabase_connection(self):
        """Obtiene conexión a Supabase usando la configuración de production.env"""
        try:
            config = self.load_production_config()
            if not config:
                return None
            
            database_url = config.get("DATABASE_URL")
            
            if not database_url:
                logger.error("DATABASE_URL no encontrada en production.env")
                return None
            
            conn = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor,
                sslmode='require',
                connect_timeout=30
            )
            
            return conn
            
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {str(e)}")
            return None
    
    def load_proveedores_data(self):
        """Carga datos de proveedores para cálculos automáticos"""
        conn = self.get_supabase_connection()
        if not conn:
            self.proveedores_data = {}
            return
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    "Nombre",
                    promedio_dias_produccion,
                    promedio_dias_transporte_maritimo,
                    "Puerto"
                FROM "Proveedores"
            """)
            
            proveedores = cursor.fetchall()
            
            # Convertir a diccionario para fácil acceso
            self.proveedores_data = {}
            for p in proveedores:
                self.proveedores_data[p['Nombre']] = {
                    'promedio_dias_produccion': float(p['promedio_dias_produccion'] or 0.0),
                    'promedio_dias_transporte_maritimo': float(p['promedio_dias_transporte_maritimo'] or 0.0),
                    'puerto': p['Puerto'] or 'N/A'
                }
            
            logger.info(f"Cargados datos de {len(self.proveedores_data)} proveedores")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error cargando datos de proveedores: {str(e)}")
            self.proveedores_data = {}
            try:
                conn.close()
            except:
                pass
    
    def safe_float(self, value, default=0.0):
        """Convierte un valor a float de forma segura"""
        if value is None or pd.isna(value):
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, Decimal):
            return float(value)
        
        if isinstance(value, str):
            # Limpiar string de caracteres no numéricos excepto punto y coma
            cleaned = re.sub(r'[^\d.,\-]', '', value)
            if cleaned:
                # Reemplazar coma por punto para decimales
                cleaned = cleaned.replace(',', '.')
                try:
                    return float(cleaned)
                except:
                    pass
        
        try:
            return float(value)
        except:
            return default
    
    def safe_date(self, value):
        """Convierte un valor a fecha de forma segura"""
        if value is None or pd.isna(value):
            return None
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, pd.Timestamp):
            return value.date()
        
        try:
            # Intentar diferentes formatos de fecha
            if isinstance(value, str):
                # Limpiar string
                cleaned = value.strip()
                if cleaned:
                    # Intentar formato YYYY-MM-DD
                    try:
                        return datetime.strptime(cleaned, '%Y-%m-%d').date()
                    except:
                        pass
                    
                    # Intentar formato DD/MM/YYYY
                    try:
                        return datetime.strptime(cleaned, '%d/%m/%Y').date()
                    except:
                        pass
                    
                    # Intentar formato MM/DD/YYYY
                    try:
                        return datetime.strptime(cleaned, '%m/%d/%Y').date()
                    except:
                        pass
            
            # Usar pandas para conversión automática
            return pd.to_datetime(value, errors='coerce').date()
            
        except:
            return None
    
    def safe_string(self, value, default=''):
        """Convierte un valor a string de forma segura"""
        if value is None or pd.isna(value):
            return default
        
        return str(value).strip()
    
    def detect_header_row(self, df: pd.DataFrame, keywords: List[str]) -> int:
        """Detecta dinámicamente la fila de encabezados"""
        best_match = (0, 0)  # (fila, número_de_coincidencias)
        
        for idx, row in df.iterrows():
            if idx > 20:  # Limitar búsqueda a las primeras 20 filas
                break
            
            matches = 0
            row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
            
            for keyword in keywords:
                if keyword.lower() in row_str:
                    matches += 1
            
            if matches > best_match[1]:
                best_match = (idx, matches)
        
        return best_match[0]
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nombres de columnas con mapeo robusto"""
        
        # Mapeo robusto de columnas
        column_mapping = {
            # Compras_v2
            'imi': ['imi', 'IMI', 'Imi', 'numero_imi', 'Numero IMI', 'numero imi'],
            'proveedor': ['proveedor', 'Proveedor', 'PROVEEDOR', 'supplier', 'Supplier', 'proveedor nombre'],
            'fecha_pedido': ['fecha_pedido', 'Fecha Pedido', 'FECHA PEDIDO', 'fecha_compra', 'Fecha Compra', 'fecha pedido'],
            'moneda': ['moneda', 'Moneda', 'MONEDA', 'currency', 'Currency', 'divisa', 'Divisa'],
            'dias_credito': ['dias_credito', 'Dias Credito', 'DIAS CREDITO', 'credit_days', 'Credit Days', 'dias credito'],
            'anticipo_pct': ['anticipo_pct', 'Anticipo %', 'ANTICIPO PCT', 'advance_pct', 'Advance %', 'anticipo %'],
            'anticipo_monto': ['anticipo_monto', 'Anticipo Monto', 'ANTICIPO MONTO', 'advance_amount', 'Advance Amount', 'anticipo monto'],
            'fecha_anticipo': ['fecha_anticipo', 'Fecha Anticipo', 'FECHA ANTICIPO', 'advance_date', 'Advance Date', 'fecha anticipo'],
            'fecha_pago_factura': ['fecha_pago_factura', 'Fecha Pago Factura', 'FECHA PAGO FACTURA', 'payment_date', 'Payment Date', 'fecha pago factura'],
            'tipo_cambio_estimado': ['tipo_cambio_estimado', 'Tipo Cambio Estimado', 'TC ESTIMADO', 'estimated_rate', 'Estimated Rate', 'tipo cambio estimado'],
            'tipo_cambio_real': ['tipo_cambio_real', 'Tipo Cambio Real', 'TC REAL', 'actual_rate', 'Actual Rate', 'tipo cambio real'],
            'gastos_importacion_divisa': ['gastos_importacion_divisa', 'Gastos Importacion Divisa', 'GASTOS IMP DIVISA', 'import_costs', 'Import Costs', 'gastos importacion divisa'],
            
            # Compras_v2_materiales
            'material_codigo': ['material_codigo', 'Material Codigo', 'MATERIAL CODIGO', 'material_code', 'Material Code', 'concepto', 'Concepto', 'material codigo'],
            'kg': ['kg', 'KG', 'kilogramos', 'Kilogramos', 'KILOGRAMOS', 'quantity', 'Quantity', 'cantidad', 'Cantidad'],
            'pu_divisa': ['pu_divisa', 'PU Divisa', 'PU DIVISA', 'unit_price', 'Unit Price', 'precio_unitario', 'Precio Unitario', 'pu divisa'],
            'costo_total_divisa': ['costo_total_divisa', 'Costo Total Divisa', 'COSTO TOTAL DIVISA', 'total_cost', 'Total Cost', 'costo total divisa'],
            'costo_total_mxn': ['costo_total_mxn', 'Costo Total MXN', 'COSTO TOTAL MXN', 'costo total mxn'],
            'iva': ['iva', 'IVA', 'tax', 'Tax']
        }
        
        # Normalizar nombres de columnas
        df_normalized = df.copy()
        df_normalized.columns = df_normalized.columns.astype(str).str.strip()
        
        # Aplicar mapeo
        for standard_name, variations in column_mapping.items():
            for variation in variations:
                if variation in df_normalized.columns:
                    df_normalized = df_normalized.rename(columns={variation: standard_name})
                    break
        
        return df_normalized
    
    def process_compras_generales(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Procesa la hoja de compras generales"""
        compras = []
        
        for _, row in df.iterrows():
            try:
                # Validar campos obligatorios
                imi = int(self.safe_float(row.get('imi', 0)))
                proveedor = self.safe_string(row.get('proveedor', ''))
                fecha_pedido = self.safe_date(row.get('fecha_pedido'))
                
                if imi <= 0 or not proveedor or not fecha_pedido:
                    logger.warning(f"Saltando fila con datos incompletos: IMI={imi}, Proveedor={proveedor}, Fecha={fecha_pedido}")
                    continue
                
                # Obtener datos del proveedor
                proveedor_data = self.proveedores_data.get(proveedor, {
                    'promedio_dias_produccion': 0.0,
                    'promedio_dias_transporte_maritimo': 0.0,
                    'puerto': 'N/A'
                })
                
                # Calcular fechas estimadas
                fecha_salida_estimada = fecha_pedido + timedelta(days=proveedor_data['promedio_dias_produccion'])
                fecha_arribo_estimada = fecha_salida_estimada + timedelta(days=proveedor_data['promedio_dias_transporte_maritimo'])
                
                # Crear registro de compra
                compra = {
                    'imi': imi,
                    'proveedor': proveedor,
                    'fecha_pedido': fecha_pedido,
                    'puerto_origen': proveedor_data['puerto'],
                    'fecha_salida_estimada': fecha_salida_estimada,
                    'fecha_arribo_estimada': fecha_arribo_estimada,
                    'moneda': self.safe_string(row.get('moneda', 'USD')),
                    'dias_credito': int(self.safe_float(row.get('dias_credito', 30))),
                    'anticipo_pct': self.safe_float(row.get('anticipo_pct', 0.0)),
                    'anticipo_monto': self.safe_float(row.get('anticipo_monto', 0.0)),
                    'fecha_anticipo': self.safe_date(row.get('fecha_anticipo')),
                    'fecha_pago_factura': self.safe_date(row.get('fecha_pago_factura')),
                    'tipo_cambio_estimado': self.safe_float(row.get('tipo_cambio_estimado', 1.0)),
                    'tipo_cambio_real': self.safe_float(row.get('tipo_cambio_real', 0.0)),
                    'gastos_importacion_divisa': self.safe_float(row.get('gastos_importacion_divisa', 0.0))
                }
                
                # Calcular campos derivados
                tipo_cambio = compra['tipo_cambio_estimado']
                compra['gastos_importacion_mxn'] = compra['gastos_importacion_divisa'] * tipo_cambio
                
                # Calcular fecha de planta automáticamente (15 días después de fecha arribo para proveedores no MX)
                fecha_arribo_real = self.safe_date(row.get('fecha_arribo_real'))
                if fecha_arribo_real and proveedor_data['puerto'] != 'MX':
                    compra['fecha_planta_real'] = fecha_arribo_real + timedelta(days=15)
                else:
                    compra['fecha_planta_real'] = self.safe_date(row.get('fecha_planta_real'))
                
                # Calcular total con gastos de importación en MXN
                # Esto se calculará después de procesar los materiales
                compra['total_con_gastos_mxn'] = 0.0  # Se calculará después
                compra['iva_monto_mxn'] = 0.0  # Se calculará después
                compra['total_con_iva_mxn'] = 0.0  # Se calculará después
                
                compras.append(compra)
                
            except Exception as e:
                logger.warning(f"Error procesando fila de compras: {str(e)}")
                continue
        
        return compras
    
    def process_materiales_detalle(self, df: pd.DataFrame, compras_dict: Dict[int, Dict]) -> List[Dict[str, Any]]:
        """Procesa la hoja de materiales detalle"""
        materiales = []
        
        for _, row in df.iterrows():
            try:
                # Validar campos obligatorios
                imi = int(self.safe_float(row.get('imi', 0)))
                material_codigo = self.safe_string(row.get('material_codigo', ''))
                kg = self.safe_float(row.get('kg', 0))
                pu_divisa = self.safe_float(row.get('pu_divisa', 0))
                
                if imi <= 0 or not material_codigo or kg <= 0:
                    logger.warning(f"Saltando material con datos incompletos: IMI={imi}, Material={material_codigo}, KG={kg}")
                    continue
                
                # Obtener datos de la compra
                compra = compras_dict.get(imi)
                if not compra:
                    logger.warning(f"No se encontró compra con IMI {imi}")
                    continue
                
                # Calcular campos derivados automáticamente
                # PU MXN = PU_divisa * TC_real (o TC_estimado si no hay TC_real)
                tipo_cambio = compra['tipo_cambio_real'] if compra['tipo_cambio_real'] > 0 else compra['tipo_cambio_estimado']
                pu_mxn = pu_divisa * tipo_cambio
                
                # Costo total en divisa = PU_divisa * KG
                costo_total_divisa = pu_divisa * kg
                
                # Costo total en MXN = PU_MXN * KG
                costo_total_mxn = pu_mxn * kg
                
                # Total con gastos de importación en MXN
                costo_total_mxn_con_gastos = costo_total_mxn + compra['gastos_importacion_mxn']
                
                # Calcular IVA automáticamente (16% del total con gastos)
                iva = costo_total_mxn_con_gastos * 0.16
                
                # Total con IVA
                costo_total_con_iva = costo_total_mxn_con_gastos + iva
                
                # Actualizar totales de la compra
                compra['total_con_gastos_mxn'] += costo_total_mxn_con_gastos
                compra['iva_monto_mxn'] += iva
                compra['total_con_iva_mxn'] += costo_total_con_iva
                
                # Crear registro de material
                material = {
                    'compra_id': imi,
                    'material_codigo': material_codigo,
                    'kg': kg,
                    'pu_divisa': pu_divisa,
                    'pu_mxn': pu_mxn,
                    'costo_total_divisa': costo_total_divisa,
                    'costo_total_mxn': costo_total_mxn,
                    'costo_total_mxn_con_gastos': costo_total_mxn_con_gastos,
                    'iva': iva,
                    'costo_total_con_iva': costo_total_con_iva,
                    'compra_imi': imi
                }
                
                materiales.append(material)
                
            except Exception as e:
                logger.warning(f"Error procesando fila de materiales: {str(e)}")
                continue
        
        return materiales
    
    def process_excel_file(self, content: bytes, filename: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Procesa archivo Excel de compras con estructura optimizada"""
        try:
            logger.info(f"Procesando archivo: {filename}")
            
            # Leer Excel
            excel_file = io.BytesIO(content)
            
            # Intentar leer diferentes hojas
            compras_df = None
            materiales_df = None
            
            try:
                # Intentar leer hoja de compras generales
                compras_df = pd.read_excel(excel_file, sheet_name="Compras Generales")
                logger.info("Encontrada hoja 'Compras Generales'")
            except:
                try:
                    excel_file.seek(0)
                    compras_df = pd.read_excel(excel_file, sheet_name=0)
                    logger.info("Usando primera hoja para compras")
                except:
                    logger.error("No se pudo leer ninguna hoja del Excel")
                    return {}, {}
            
            try:
                # Intentar leer hoja de materiales
                excel_file.seek(0)
                materiales_df = pd.read_excel(excel_file, sheet_name="Materiales Detalle")
                logger.info("Encontrada hoja 'Materiales Detalle'")
            except:
                logger.warning("No se encontró hoja 'Materiales Detalle', usando datos de compras")
                materiales_df = compras_df.copy()
            
            # Detectar fila de encabezados
            keywords = ['imi', 'proveedor', 'fecha', 'material', 'kg', 'precio']
            header_row = self.detect_header_row(compras_df, keywords)
            
            if header_row > 0:
                compras_df = compras_df.iloc[header_row:].reset_index(drop=True)
                compras_df.columns = compras_df.iloc[0]
                compras_df = compras_df.iloc[1:].reset_index(drop=True)
                logger.info(f"Detectada fila de encabezados en posición {header_row}")
            
            # Limpiar datos
            compras_df = compras_df.dropna(how='all').dropna(axis=1, how='all')
            materiales_df = materiales_df.dropna(how='all').dropna(axis=1, how='all')
            
            # Normalizar nombres de columnas
            compras_df = self.normalize_column_names(compras_df)
            materiales_df = self.normalize_column_names(materiales_df)
            
            logger.info(f"Columnas de compras: {list(compras_df.columns)}")
            logger.info(f"Columnas de materiales: {list(materiales_df.columns)}")
            
            # Procesar compras
            compras = self.process_compras_generales(compras_df)
            
            # Crear diccionario de compras para materiales
            compras_dict = {c['imi']: c for c in compras}
            
            # Procesar materiales
            materiales = self.process_materiales_detalle(materiales_df, compras_dict)
            
            # Calcular porcentaje de gastos de importación después de procesar materiales
            for compra in compras:
                if compra['total_con_gastos_mxn'] > 0:
                    compra['porcentaje_gastos_importacion'] = (compra['gastos_importacion_mxn'] / compra['total_con_gastos_mxn']) * 100
                else:
                    compra['porcentaje_gastos_importacion'] = 0.0
            
            logger.info(f"Procesados: {len(compras)} compras, {len(materiales)} materiales")
            
            # Calcular KPIs
            kpis = {
                'total_compras': len(compras),
                'total_materiales': len(materiales),
                'total_proveedores': len(set(c['proveedor'] for c in compras)),
                'total_kilogramos': sum(m['kg'] for m in materiales),
                'total_costo_divisa': sum(c.get('total_con_gastos_mxn', 0) for c in compras),  # Usando MXN como aproximación
                'total_costo_mxn': sum(c.get('total_con_iva_mxn', 0) for c in compras),
                'compras_con_anticipo': sum(1 for c in compras if c.get('anticipo_monto', 0) > 0),
                'compras_pagadas': sum(1 for c in compras if c.get('fecha_pago_factura')),
                'proveedores_no_encontrados': len(set(c['proveedor'] for c in compras if c['proveedor'] not in self.proveedores_data))
            }
            
            return {
                'compras_v2': compras,
                'compras_v2_materiales': materiales
            }, kpis
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            raise

def process_compras_v2(content: bytes, filename: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Función principal para procesar archivos de compras v2"""
    processor = ComprasV2Processor()
    return processor.process_excel_file(content, filename)
