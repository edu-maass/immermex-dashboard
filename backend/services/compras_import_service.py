"""
Servicio de importación automática de compras desde OneDrive
Procesa archivos Excel de compras y los importa a Supabase
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import asyncio
from io import BytesIO
import hashlib

from services.onedrive_service import OneDriveService, OneDriveSyncService, OneDriveFile
from database_service_refactored import DatabaseService
from excel_processor import ExcelProcessor

logger = logging.getLogger(__name__)

class ComprasImportService:
    """Servicio para importar compras desde OneDrive a Supabase"""
    
    def __init__(self):
        self.onedrive_service = OneDriveService()
        self.sync_service = OneDriveSyncService(self.onedrive_service)
        self.db_service = DatabaseService()
        self.excel_processor = ExcelProcessor()
        
        # Configuración de mapeo de columnas para compras
        self.column_mapping = {
            'fecha_compra': ['fecha', 'fecha_compra', 'date', 'fecha_factura'],
            'numero_factura': ['factura', 'numero_factura', 'folio', 'invoice'],
            'proveedor': ['proveedor', 'supplier', 'vendor', 'cliente'],
            'concepto': ['concepto', 'descripcion', 'description', 'detalle'],
            'categoria': ['categoria', 'category', 'tipo', 'clasificacion'],
            'subcategoria': ['subcategoria', 'subcategory', 'sub_tipo'],
            'cantidad': ['cantidad', 'quantity', 'qty', 'unidades'],
            'unidad': ['unidad', 'unit', 'medida', 'uom'],
            'precio_unitario': ['precio_unitario', 'unit_price', 'precio', 'costo_unitario'],
            'subtotal': ['subtotal', 'sub_total', 'importe_sin_iva'],
            'iva': ['iva', 'tax', 'impuesto'],
            'total': ['total', 'importe_total', 'amount'],
            'moneda': ['moneda', 'currency', 'curr'],
            'forma_pago': ['forma_pago', 'payment_method', 'metodo_pago'],
            'dias_credito': ['dias_credito', 'credit_days', 'dias'],
            'fecha_vencimiento': ['fecha_vencimiento', 'due_date', 'vencimiento'],
            'fecha_pago': ['fecha_pago', 'payment_date', 'fecha_cobro'],
            'centro_costo': ['centro_costo', 'cost_center', 'departamento'],
            'proyecto': ['proyecto', 'project', 'obra'],
            'notas': ['notas', 'notes', 'observaciones', 'comentarios']
        }
    
    async def import_compras_from_onedrive(self, folder_path: str = None) -> Dict[str, any]:
        """Importa compras desde archivos de OneDrive"""
        try:
            logger.info("Iniciando importación de compras desde OneDrive")
            
            # Obtener archivos nuevos
            new_files = await self.sync_service.get_new_files(folder_path)
            
            if not new_files:
                logger.info("No hay archivos nuevos para procesar")
                return {
                    "success": True,
                    "message": "No hay archivos nuevos para procesar",
                    "files_processed": 0,
                    "records_imported": 0
                }
            
            total_records = 0
            processed_files = []
            
            for file in new_files:
                try:
                    logger.info(f"Procesando archivo: {file.name}")
                    
                    # Descargar archivo
                    file_content = await self.onedrive_service.download_file(file)
                    
                    # Procesar archivo Excel
                    result = await self.process_compras_file(file_content, file.name)
                    
                    if result["success"]:
                        total_records += result["records_imported"]
                        processed_files.append({
                            "file": file.name,
                            "records": result["records_imported"],
                            "status": "success"
                        })
                        logger.info(f"Archivo {file.name} procesado exitosamente: {result['records_imported']} registros")
                    else:
                        processed_files.append({
                            "file": file.name,
                            "records": 0,
                            "status": "error",
                            "error": result["error"]
                        })
                        logger.error(f"Error procesando archivo {file.name}: {result['error']}")
                
                except Exception as e:
                    logger.error(f"Error procesando archivo {file.name}: {e}")
                    processed_files.append({
                        "file": file.name,
                        "records": 0,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "message": f"Importación completada. {len(processed_files)} archivos procesados",
                "files_processed": len(processed_files),
                "records_imported": total_records,
                "files": processed_files
            }
            
        except Exception as e:
            logger.error(f"Error durante la importación: {e}")
            return {
                "success": False,
                "error": str(e),
                "files_processed": 0,
                "records_imported": 0
            }
    
    async def process_compras_file(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """Procesa un archivo Excel de compras"""
        try:
            # Leer archivo Excel
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
            
            if df.empty:
                return {
                    "success": False,
                    "error": "El archivo está vacío",
                    "records_imported": 0
                }
            
            # Mapear columnas
            mapped_df = self.map_columns(df)
            
            # Validar datos requeridos
            validation_result = self.validate_compras_data(mapped_df)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Datos inválidos: {validation_result['errors']}",
                    "records_imported": 0
                }
            
            # Procesar y limpiar datos
            processed_df = self.clean_compras_data(mapped_df)
            
            # Registrar archivo procesado
            archivo_id = await self.register_processed_file(filename, len(processed_df))
            
            # Importar a base de datos
            imported_count = await self.import_to_database(processed_df, archivo_id)
            
            return {
                "success": True,
                "records_imported": imported_count,
                "archivo_id": archivo_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo {filename}: {e}")
            return {
                "success": False,
                "error": str(e),
                "records_imported": 0
            }
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea las columnas del DataFrame a los campos estándar"""
        mapped_df = pd.DataFrame()
        
        for standard_field, possible_columns in self.column_mapping.items():
            found_column = None
            
            # Buscar columna que coincida
            for col in df.columns:
                col_lower = str(col).lower().strip()
                for possible_col in possible_columns:
                    if possible_col.lower() in col_lower or col_lower in possible_col.lower():
                        found_column = col
                        break
                if found_column:
                    break
            
            if found_column:
                mapped_df[standard_field] = df[found_column]
            else:
                # Si no se encuentra, crear columna vacía
                mapped_df[standard_field] = None
        
        return mapped_df
    
    def validate_compras_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida los datos de compras"""
        errors = []
        
        # Verificar campos requeridos
        required_fields = ['fecha_compra', 'proveedor', 'total']
        for field in required_fields:
            if field not in df.columns or df[field].isna().all():
                errors.append(f"Campo requerido '{field}' no encontrado o vacío")
        
        # Verificar que hay al menos una fila
        if len(df) == 0:
            errors.append("No hay datos para procesar")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def clean_compras_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza los datos de compras"""
        cleaned_df = df.copy()
        
        # Limpiar fechas
        date_columns = ['fecha_compra', 'fecha_vencimiento', 'fecha_pago']
        for col in date_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
        
        # Limpiar valores numéricos
        numeric_columns = ['cantidad', 'precio_unitario', 'subtotal', 'iva', 'total', 'dias_credito']
        for col in numeric_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
        
        # Limpiar texto
        text_columns = ['proveedor', 'concepto', 'categoria', 'subcategoria', 'unidad', 'forma_pago', 'centro_costo', 'proyecto', 'notas']
        for col in text_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                cleaned_df[col] = cleaned_df[col].replace('nan', None)
        
        # Calcular campos derivados
        if 'mes' not in cleaned_df.columns and 'fecha_compra' in cleaned_df.columns:
            cleaned_df['mes'] = cleaned_df['fecha_compra'].dt.month
        if 'año' not in cleaned_df.columns and 'fecha_compra' in cleaned_df.columns:
            cleaned_df['año'] = cleaned_df['fecha_compra'].dt.year
        
        # Calcular fecha de vencimiento si no existe
        if 'fecha_vencimiento' not in cleaned_df.columns or cleaned_df['fecha_vencimiento'].isna().all():
            if 'fecha_compra' in cleaned_df.columns and 'dias_credito' in cleaned_df.columns:
                cleaned_df['fecha_vencimiento'] = cleaned_df['fecha_compra'] + pd.to_timedelta(cleaned_df['dias_credito'], unit='D')
        
        # Establecer valores por defecto
        cleaned_df['moneda'] = cleaned_df.get('moneda', 'MXN')
        cleaned_df['tipo_cambio'] = cleaned_df.get('tipo_cambio', 1.0)
        cleaned_df['dias_credito'] = cleaned_df.get('dias_credito', 0)
        
        return cleaned_df
    
    async def register_processed_file(self, filename: str, record_count: int) -> int:
        """Registra el archivo procesado en la base de datos"""
        try:
            # Crear hash del archivo
            file_hash = hashlib.md5(filename.encode()).hexdigest()
            
            # Obtener mes y año del nombre del archivo o fecha actual
            current_date = datetime.now()
            mes = current_date.month
            año = current_date.year
            
            # Intentar extraer mes y año del nombre del archivo
            import re
            date_match = re.search(r'(\d{4})[_-]?(\d{1,2})', filename)
            if date_match:
                año = int(date_match.group(1))
                mes = int(date_match.group(2))
            
            # Insertar registro de archivo procesado
            query = """
                INSERT INTO archivos_procesados 
                (nombre_archivo, registros_procesados, estado, mes, año, hash_archivo, algoritmo_usado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hash_archivo) DO UPDATE SET
                    registros_procesados = EXCLUDED.registros_procesados,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            result = await self.db_service.execute_query(
                query, 
                (filename, record_count, 'procesado', mes, año, file_hash, 'compras_import')
            )
            
            return result[0]['id'] if result else None
            
        except Exception as e:
            logger.error(f"Error registrando archivo procesado: {e}")
            return None
    
    async def import_to_database(self, df: pd.DataFrame, archivo_id: int) -> int:
        """Importa los datos procesados a la base de datos"""
        try:
            imported_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Preparar datos para inserción
                    compra_data = {
                        'fecha_compra': row.get('fecha_compra'),
                        'numero_factura': row.get('numero_factura'),
                        'proveedor': row.get('proveedor'),
                        'concepto': row.get('concepto'),
                        'categoria': row.get('categoria'),
                        'subcategoria': row.get('subcategoria'),
                        'cantidad': row.get('cantidad', 0),
                        'unidad': row.get('unidad'),
                        'precio_unitario': row.get('precio_unitario', 0),
                        'subtotal': row.get('subtotal', 0),
                        'iva': row.get('iva', 0),
                        'total': row.get('total', 0),
                        'moneda': row.get('moneda', 'MXN'),
                        'tipo_cambio': row.get('tipo_cambio', 1.0),
                        'forma_pago': row.get('forma_pago'),
                        'dias_credito': row.get('dias_credito', 0),
                        'fecha_vencimiento': row.get('fecha_vencimiento'),
                        'fecha_pago': row.get('fecha_pago'),
                        'centro_costo': row.get('centro_costo'),
                        'proyecto': row.get('proyecto'),
                        'notas': row.get('notas'),
                        'archivo_origen': f"OneDrive/{archivo_id}",
                        'archivo_id': archivo_id,
                        'mes': row.get('mes'),
                        'año': row.get('año')
                    }
                    
                    # Insertar registro
                    query = """
                        INSERT INTO compras (
                            fecha_compra, numero_factura, proveedor, concepto, categoria, subcategoria,
                            cantidad, unidad, precio_unitario, subtotal, iva, total, moneda, tipo_cambio,
                            forma_pago, dias_credito, fecha_vencimiento, fecha_pago, centro_costo,
                            proyecto, notas, archivo_origen, archivo_id, mes, año
                        ) VALUES (
                            %(fecha_compra)s, %(numero_factura)s, %(proveedor)s, %(concepto)s, %(categoria)s, %(subcategoria)s,
                            %(cantidad)s, %(unidad)s, %(precio_unitario)s, %(subtotal)s, %(iva)s, %(total)s, %(moneda)s, %(tipo_cambio)s,
                            %(forma_pago)s, %(dias_credito)s, %(fecha_vencimiento)s, %(fecha_pago)s, %(centro_costo)s,
                            %(proyecto)s, %(notas)s, %(archivo_origen)s, %(archivo_id)s, %(mes)s, %(año)s
                        )
                    """
                    
                    await self.db_service.execute_query(query, compra_data)
                    imported_count += 1
                    
                except Exception as e:
                    logger.error(f"Error insertando registro de compra: {e}")
                    continue
            
            logger.info(f"Importados {imported_count} registros de compras")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importando a base de datos: {e}")
            return 0
    
    async def get_compras_summary(self, mes: int = None, año: int = None) -> Dict[str, any]:
        """Obtiene resumen de compras"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_compras,
                    SUM(total) as total_monto,
                    SUM(CASE WHEN estado_pago = 'pagado' THEN total ELSE 0 END) as monto_pagado,
                    SUM(CASE WHEN estado_pago = 'pendiente' THEN total ELSE 0 END) as monto_pendiente,
                    SUM(CASE WHEN estado_pago = 'vencido' THEN total ELSE 0 END) as monto_vencido,
                    COUNT(CASE WHEN estado_pago = 'pagado' THEN 1 END) as compras_pagadas,
                    COUNT(CASE WHEN estado_pago = 'pendiente' THEN 1 END) as compras_pendientes,
                    COUNT(CASE WHEN estado_pago = 'vencido' THEN 1 END) as compras_vencidas
                FROM compras
                WHERE 1=1
            """
            
            params = []
            if mes:
                query += " AND mes = %s"
                params.append(mes)
            if año:
                query += " AND año = %s"
                params.append(año)
            
            result = await self.db_service.execute_query(query, params)
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de compras: {e}")
            return {}
    
    async def sync_compras_automatic(self) -> Dict[str, any]:
        """Sincronización automática de compras"""
        try:
            if not self.sync_service.should_sync():
                return {
                    "success": True,
                    "message": "No es necesario sincronizar aún",
                    "skipped": True
                }
            
            logger.info("Iniciando sincronización automática de compras")
            result = await self.import_compras_from_onedrive()
            
            return result
            
        except Exception as e:
            logger.error(f"Error en sincronización automática: {e}")
            return {
                "success": False,
                "error": str(e)
            }
