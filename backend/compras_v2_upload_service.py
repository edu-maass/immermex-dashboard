"""
Servicio actualizado para upload de compras_v2 y compras_v2_materiales
Integrado con el nuevo procesador robusto y servicio de guardado
"""

from sqlalchemy.orm import Session
from database import (
    ArchivoProcesado, get_db
)
from .compras_v2_service import ComprasV2Service
import logging
import os
from datetime import datetime
from typing import Dict, Any
import pandas as pd
import io

logger = logging.getLogger(__name__)

class ComprasV2UploadService:
    """Servicio especializado para manejar uploads de compras_v2 con nueva arquitectura"""
    
    def __init__(self):
        self.compras_service = ComprasV2Service()
    
    def upload_compras_file(self, file_content: bytes, filename: str, replace_data: bool = False) -> Dict[str, Any]:
        """
        Procesa y guarda archivo de compras usando el nuevo sistema compras_v2
        """
        try:
            logger.info(f"[COMPRAS_V2_SERVICE] Iniciando procesamiento de: {filename}")
            
            # Paso 1: Procesar archivo en memoria
            logger.info("[COMPRAS_V2_SERVICE] Paso 1: Procesando archivo Excel...")
            processed_data_dict, kpis = self._process_compras_excel(file_content, filename)
            
            compras_count = len(processed_data_dict.get('compras_v2', []))
            materiales_count = len(processed_data_dict.get('compras_v2_materiales', []))
            
            logger.info(f"[COMPRAS_V2_SERVICE] Datos procesados: {compras_count} compras, {materiales_count} materiales")
            
            # Paso 2: Crear registro de archivo en sesión separada
            logger.info("[COMPRAS_V2_SERVICE] Paso 2: Creando registro de archivo...")
            archivo_id = self._create_archivo_record(filename, len(file_content), replace_data)
            
            if not archivo_id:
                raise Exception("No se pudo crear el registro de archivo")
            
            logger.info(f"[COMPRAS_V2_SERVICE] Archivo creado con ID: {archivo_id}")
            
            # Paso 3: Guardar datos usando el nuevo servicio
            logger.info("[COMPRAS_V2_SERVICE] Paso 3: Guardando datos con nuevo servicio...")
            save_results = self.compras_service.save_compras_data(processed_data_dict, archivo_id)
            
            # Paso 4: Actualizar estado del archivo
            logger.info("[COMPRAS_V2_SERVICE] Paso 4: Actualizando estado del archivo...")
            self._update_archivo_status(archivo_id, "procesado", save_results['total_procesados'])
            
            logger.info(f"[COMPRAS_V2_SERVICE] Proceso completado exitosamente:")
            logger.info(f"  - Compras guardadas: {save_results['compras_guardadas']}")
            logger.info(f"  - Compras omitidas: {save_results.get('compras_omitidas', 0)}")
            logger.info(f"  - Materiales guardados: {save_results['materiales_guardados']}")
            logger.info(f"  - Materiales omitidos: {save_results.get('materiales_omitidos', 0)}")
            logger.info(f"  - Total procesados: {save_results['total_procesados']}")
            logger.info(f"  - Total omitidos: {save_results.get('total_omitidos', 0)}")
            
            return {
                "success": True,
                "archivo_id": archivo_id,
                "compras_guardadas": save_results['compras_guardadas'],
                "compras_omitidas": save_results.get('compras_omitidas', 0),
                "materiales_guardados": save_results['materiales_guardados'],
                "materiales_omitidos": save_results.get('materiales_omitidos', 0),
                "total_procesados": save_results['total_procesados'],
                "total_omitidos": save_results.get('total_omitidos', 0),
                "kpis": kpis,
                "mensaje": f"Archivo procesado exitosamente. Guardados: {save_results['compras_guardadas']} compras, {save_results['materiales_guardados']} materiales. Omitidos: {save_results.get('compras_omitidas', 0)} compras, {save_results.get('materiales_omitidos', 0)} materiales."
            }
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error en procesamiento: {str(e)}")
            import traceback
            logger.error(f"[COMPRAS_V2_SERVICE] Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    def _create_archivo_record(self, filename: str, file_size: int, replace_data: bool) -> int:
        """Crea registro de archivo en sesión separada"""
        db = next(get_db())
        try:
            # Si se debe reemplazar datos, limpiar existentes
            if replace_data:
                logger.info("[COMPRAS_V2_SERVICE] Modo reemplazo: Limpiando datos existentes...")
                self._clear_existing_data(db)
            else:
                logger.info("[COMPRAS_V2_SERVICE] Modo incremental: Conservando datos existentes, actualizando/insertando según corresponda...")
            
            # Verificar si ya existe un archivo con el mismo nombre
            existing_archivo = db.query(ArchivoProcesado).filter(
                ArchivoProcesado.nombre_archivo == filename
            ).first()
            
            if existing_archivo:
                # Actualizar el archivo existente
                existing_archivo.estado = "en_proceso"
                existing_archivo.fecha_procesamiento = datetime.utcnow()
                existing_archivo.tamaño_archivo = file_size
                db.commit()
                db.refresh(existing_archivo)
                logger.info(f"[COMPRAS_V2_SERVICE] Archivo existente actualizado: ID={existing_archivo.id}, nombre={filename}")
                return existing_archivo.id
            else:
                # Crear nuevo registro
                archivo = ArchivoProcesado(
                    nombre_archivo=filename,
                    tamaño_archivo=file_size,
                    algoritmo_usado="compras_v2_robust",
                    estado="en_proceso",
                    fecha_procesamiento=datetime.utcnow()
                )
                
                db.add(archivo)
                db.commit()
                db.refresh(archivo)  # Refrescar para obtener el ID
                
                logger.info(f"[COMPRAS_V2_SERVICE] Archivo creado: ID={archivo.id}, nombre={filename}")
                return archivo.id
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error creando archivo: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def _update_archivo_status(self, archivo_id: int, estado: str, registros_procesados: int):
        """Actualiza estado del archivo en sesión separada"""
        db = next(get_db())
        try:
            archivo = db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo_id).first()
            if archivo:
                archivo.estado = estado
                archivo.registros_procesados = registros_procesados
                archivo.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"[COMPRAS_V2_SERVICE] Archivo {archivo_id} actualizado a estado {estado}")
            else:
                logger.error(f"[COMPRAS_V2_SERVICE] No se encontró archivo con ID {archivo_id}")
                
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error actualizando archivo: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def _clear_existing_data(self, db: Session):
        """Limpia datos existentes de compras_v2"""
        try:
            # Usar el servicio para limpiar datos
            conn = self.compras_service.get_connection()
            if conn:
                cursor = conn.cursor()
                
                # Limpiar en orden debido a foreign keys
                cursor.execute("DELETE FROM compras_v2_materiales")
                cursor.execute("DELETE FROM compras_v2")
                cursor.execute("DELETE FROM archivos_procesados")
                
                conn.commit()
                cursor.close()
                logger.info("[COMPRAS_V2_SERVICE] Datos existentes de compras_v2 limpiados")
            
            # También limpiar usando SQLAlchemy para consistencia
            db.query(ArchivoProcesado).delete()
            db.commit()
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error limpiando datos: {str(e)}")
            db.rollback()
    
    def get_compras_data(self, filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene datos de compras usando el nuevo servicio"""
        try:
            compras = self.compras_service.get_compras_by_filtros(filtros or {})
            kpis = self.compras_service.calculate_kpis(filtros)
            
            return {
                "success": True,
                "compras": compras,
                "kpis": kpis,
                "total_compras": len(compras)
            }
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error obteniendo datos: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "compras": [],
                "kpis": {}
            }
    
    def get_materiales_by_compra(self, imi: int) -> Dict[str, Any]:
        """Obtiene materiales de una compra específica"""
        try:
            materiales = self.compras_service.get_materiales_by_compra(imi)
            
            return {
                "success": True,
                "materiales": materiales,
                "total_materiales": len(materiales)
            }
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error obteniendo materiales: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "materiales": []
            }
    
    def validate_file_structure(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Valida la estructura del archivo antes del procesamiento"""
        try:
            import pandas as pd
            import io
            
            # Leer Excel para validar estructura
            excel_file = io.BytesIO(file_content)
            
            # Intentar leer diferentes hojas
            try:
                compras_df = pd.read_excel(excel_file, sheet_name="Compras Generales")
                compras_sheet_found = True
            except:
                try:
                    excel_file.seek(0)
                    compras_df = pd.read_excel(excel_file, sheet_name=0)
                    compras_sheet_found = False
                except:
                    return {
                        "valid": False,
                        "error": "No se pudo leer el archivo Excel",
                        "recommendations": ["Verificar que el archivo sea un Excel válido"]
                    }
            
            try:
                excel_file.seek(0)
                materiales_df = pd.read_excel(excel_file, sheet_name="Materiales Detalle")
                materiales_sheet_found = True
            except:
                materiales_sheet_found = False
            
            # Validar columnas requeridas
            required_compras_columns = ['imi', 'proveedor', 'fecha_pedido']
            required_materiales_columns = ['imi', 'material_codigo', 'kg']
            
            compras_columns = list(compras_df.columns)
            materiales_columns = list(materiales_df.columns) if materiales_sheet_found else compras_columns
            
            missing_compras = [col for col in required_compras_columns if col not in compras_columns]
            missing_materiales = [col for col in required_materiales_columns if col not in materiales_columns]
            
            recommendations = []
            
            if missing_compras:
                recommendations.append(f"Faltan columnas en compras: {missing_compras}")
            
            if missing_materiales:
                recommendations.append(f"Faltan columnas en materiales: {missing_materiales}")
            
            if not compras_sheet_found:
                recommendations.append("Se recomienda usar hoja 'Compras Generales' para mejor organización")
            
            if not materiales_sheet_found:
                recommendations.append("Se recomienda usar hoja 'Materiales Detalle' para mejor organización")
            
            return {
                "valid": len(missing_compras) == 0 and len(missing_materiales) == 0,
                "compras_sheet_found": compras_sheet_found,
                "materiales_sheet_found": materiales_sheet_found,
                "compras_columns": compras_columns,
                "materiales_columns": materiales_columns,
                "missing_compras": missing_compras,
                "missing_materiales": missing_materiales,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_SERVICE] Error validando archivo: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "recommendations": ["Verificar formato del archivo"]
            }
    
    def _process_compras_excel(self, file_content: bytes, filename: str) -> tuple:
        """
        Procesa archivo Excel de compras_v2 específicamente
        Retorna: (processed_data_dict, kpis)
        """
        try:
            logger.info(f"[COMPRAS_V2_PROCESSOR] Procesando Excel de compras: {filename}")
            
            # Leer archivo Excel
            excel_file = io.BytesIO(file_content)
            
            # Intentar leer hojas específicas
            try:
                compras_df = pd.read_excel(excel_file, sheet_name="Compras Generales")
                logger.info(f"[COMPRAS_V2_PROCESSOR] Hoja 'Compras Generales' encontrada: {len(compras_df)} filas")
            except:
                excel_file.seek(0)
                compras_df = pd.read_excel(excel_file, sheet_name=0)
                logger.info(f"[COMPRAS_V2_PROCESSOR] Usando primera hoja como compras: {len(compras_df)} filas")
            
            try:
                excel_file.seek(0)
                materiales_df = pd.read_excel(excel_file, sheet_name="Materiales Detalle")
                logger.info(f"[COMPRAS_V2_PROCESSOR] Hoja 'Materiales Detalle' encontrada: {len(materiales_df)} filas")
            except:
                # Si no hay hoja de materiales separada, intentar buscar en la misma hoja
                materiales_df = compras_df.copy()
                logger.info(f"[COMPRAS_V2_PROCESSOR] Usando hoja de compras también para materiales")
            
            # Normalizar nombres de columnas
            compras_df.columns = [self._normalize_column_name(col) for col in compras_df.columns]
            materiales_df.columns = [self._normalize_column_name(col) for col in materiales_df.columns]
            
            logger.info(f"[COMPRAS_V2_PROCESSOR] Columnas compras: {list(compras_df.columns)}")
            logger.info(f"[COMPRAS_V2_PROCESSOR] Columnas materiales: {list(materiales_df.columns)}")
            
            # Procesar compras
            compras_list = self._process_compras_df(compras_df)
            materiales_list = self._process_materiales_df(materiales_df)
            
            # Calcular KPIs básicos
            kpis = {
                'total_compras': len(compras_list),
                'total_materiales': len(materiales_list),
                'proveedores_unicos': len(set([c.get('proveedor') for c in compras_list if c.get('proveedor')]))
            }
            
            processed_data = {
                'compras_v2': compras_list,
                'compras_v2_materiales': materiales_list
            }
            
            logger.info(f"[COMPRAS_V2_PROCESSOR] Procesamiento completado: {len(compras_list)} compras, {len(materiales_list)} materiales")
            
            return processed_data, kpis
            
        except Exception as e:
            logger.error(f"[COMPRAS_V2_PROCESSOR] Error procesando Excel: {str(e)}")
            import traceback
            logger.error(f"[COMPRAS_V2_PROCESSOR] Traceback: {traceback.format_exc()}")
            raise
    
    def _normalize_column_name(self, col: str) -> str:
        """Normaliza nombre de columna a snake_case"""
        import re
        # Eliminar espacios al inicio y final
        col = str(col).strip()
        # Convertir a minúsculas
        col = col.lower()
        # Reemplazar espacios y caracteres especiales por guión bajo
        col = re.sub(r'[^\w\s]', '', col)
        col = re.sub(r'\s+', '_', col)
        return col
    
    def _process_compras_df(self, df: pd.DataFrame) -> list:
        """Procesa DataFrame de compras y retorna lista de diccionarios"""
        compras = []
        
        for idx, row in df.iterrows():
            try:
                # Validar que tenga IMI
                if 'imi' not in row or pd.isna(row['imi']) or row['imi'] == '':
                    continue
                
                # Helper para convertir fechas y manejar NaT
                def safe_date(value):
                    if value is None or pd.isna(value):
                        return None
                    try:
                        dt = pd.to_datetime(value, errors='coerce')
                        return None if pd.isna(dt) else dt
                    except:
                        return None
                
                # Obtener fechas
                fecha_salida_real = safe_date(row.get('fecha_salida_real'))
                fecha_arribo_real = safe_date(row.get('fecha_arribo_real'))
                fecha_planta_real = safe_date(row.get('fecha_planta_real'))
                
                # Calcular días automáticamente
                dias_transporte = None
                dias_puerto_planta = None
                
                if fecha_salida_real and fecha_arribo_real:
                    dias_transporte = (fecha_arribo_real - fecha_salida_real).days
                
                if fecha_arribo_real and fecha_planta_real:
                    dias_puerto_planta = (fecha_planta_real - fecha_arribo_real).days
                
                # Obtener datos del proveedor
                proveedor_nombre = str(row['proveedor']) if 'proveedor' in row and pd.notna(row['proveedor']) else ''
                proveedor_info = self._get_proveedor_info(proveedor_nombre) if proveedor_nombre else {}
                
                # Puerto origen: primero buscar en Excel, luego en tabla proveedores
                puerto_origen = str(row['puerto_origen']) if 'puerto_origen' in row and pd.notna(row['puerto_origen']) else ''
                if not puerto_origen and proveedor_info:
                    puerto_origen = proveedor_info.get('puerto_origen', '')
                
                # Tipo de cambio estimado: por defecto 20, o lo que venga en Excel
                tipo_cambio_estimado = float(row['tipo_cambio_estimado']) if 'tipo_cambio_estimado' in row and pd.notna(row['tipo_cambio_estimado']) else 20.0
                tipo_cambio_real = float(row['tipo_cambio_real']) if 'tipo_cambio_real' in row and pd.notna(row['tipo_cambio_real']) else 0
                
                # Usar tipo de cambio real si existe, sino el estimado
                tipo_cambio_efectivo = tipo_cambio_real if tipo_cambio_real > 0 else tipo_cambio_estimado
                
                # Calcular gastos de importación en MXN si no viene
                gastos_importacion_divisa = float(row['gastos_importacion_divisa']) if 'gastos_importacion_divisa' in row and pd.notna(row['gastos_importacion_divisa']) else 0
                gastos_importacion_mxn = float(row['gastos_importacion_mxn']) if 'gastos_importacion_mxn' in row and pd.notna(row['gastos_importacion_mxn']) else 0
                
                if gastos_importacion_mxn == 0 and gastos_importacion_divisa > 0 and tipo_cambio_efectivo > 0:
                    gastos_importacion_mxn = gastos_importacion_divisa * tipo_cambio_efectivo
                
                # Calcular IVA en MXN si no viene
                iva_monto_divisa = float(row['iva_monto_divisa']) if 'iva_monto_divisa' in row and pd.notna(row['iva_monto_divisa']) else 0
                iva_monto_mxn = float(row['iva_monto_mxn']) if 'iva_monto_mxn' in row and pd.notna(row['iva_monto_mxn']) else 0
                
                if iva_monto_mxn == 0 and iva_monto_divisa > 0 and tipo_cambio_efectivo > 0:
                    iva_monto_mxn = iva_monto_divisa * tipo_cambio_efectivo
                
                # Calcular total con IVA en MXN si no viene
                total_con_iva_divisa = float(row['total_con_iva_divisa']) if 'total_con_iva_divisa' in row and pd.notna(row['total_con_iva_divisa']) else 0
                total_con_iva_mxn = float(row['total_con_iva_mxn']) if 'total_con_iva_mxn' in row and pd.notna(row['total_con_iva_mxn']) else 0
                
                if total_con_iva_mxn == 0 and total_con_iva_divisa > 0 and tipo_cambio_efectivo > 0:
                    total_con_iva_mxn = total_con_iva_divisa * tipo_cambio_efectivo
                
                # Calcular fecha de vencimiento
                fecha_vencimiento = safe_date(row.get('fecha_vencimiento'))
                dias_credito = int(row['dias_credito']) if 'dias_credito' in row and pd.notna(row['dias_credito']) else None
                
                if not fecha_vencimiento and fecha_salida_real and dias_credito:
                    from datetime import timedelta
                    fecha_vencimiento = fecha_salida_real + timedelta(days=dias_credito)
                elif not fecha_vencimiento and fecha_salida_estimada and dias_credito:
                    from datetime import timedelta
                    fecha_vencimiento = fecha_salida_estimada + timedelta(days=dias_credito)
                
                # Calcular fechas estimadas usando datos del proveedor
                fecha_pedido = safe_date(row.get('fecha_pedido'))
                fecha_salida_estimada = safe_date(row.get('fecha_salida_estimada'))
                fecha_arribo_estimada = safe_date(row.get('fecha_arribo_estimada'))
                fecha_planta_estimada = safe_date(row.get('fecha_planta_estimada'))
                
                # Solo calcular si no vienen en Excel y tenemos fecha_pedido y datos del proveedor
                if fecha_pedido and proveedor_info and not fecha_salida_estimada:
                    from datetime import timedelta
                    dias_produccion = proveedor_info.get('dias_produccion', 0)
                    if dias_produccion > 0:
                        fecha_salida_estimada = fecha_pedido + timedelta(days=int(dias_produccion))
                        
                        # Calcular fecha_arribo_estimada
                        if not fecha_arribo_estimada:
                            dias_transporte = proveedor_info.get('dias_transporte', 0)
                            if dias_transporte > 0:
                                fecha_arribo_estimada = fecha_salida_estimada + timedelta(days=int(dias_transporte))
                                
                                # Calcular fecha_planta_estimada (arribo + 15 días)
                                if not fecha_planta_estimada:
                                    fecha_planta_estimada = fecha_arribo_estimada + timedelta(days=15)
                
                compra = {
                    'imi': int(row['imi']) if 'imi' in row and pd.notna(row['imi']) else 0,
                    'proveedor': proveedor_nombre,
                    'fecha_pedido': fecha_pedido,
                    'puerto_origen': puerto_origen,
                    'fecha_salida_estimada': fecha_salida_estimada,
                    'fecha_arribo_estimada': fecha_arribo_estimada,
                    'fecha_planta_estimada': fecha_planta_estimada,
                    'fecha_salida_real': fecha_salida_real,
                    'fecha_arribo_real': fecha_arribo_real,
                    'fecha_planta_real': fecha_planta_real,
                    'moneda': str(row['moneda']) if 'moneda' in row and pd.notna(row['moneda']) else 'USD',
                    'dias_credito': int(row['dias_credito']) if 'dias_credito' in row and pd.notna(row['dias_credito']) else None,
                    'anticipo_pct': float(row['anticipo_pct']) if 'anticipo_pct' in row and pd.notna(row['anticipo_pct']) else 0,
                    'anticipo_monto': float(row['anticipo_monto']) if 'anticipo_monto' in row and pd.notna(row['anticipo_monto']) else 0,
                    'fecha_anticipo': safe_date(row.get('fecha_anticipo')),
                    'fecha_pago_factura': safe_date(row.get('fecha_pago_factura')),
                    'tipo_cambio_estimado': tipo_cambio_estimado,
                    'tipo_cambio_real': tipo_cambio_real,
                    'gastos_importacion_divisa': gastos_importacion_divisa,
                    'gastos_importacion_mxn': gastos_importacion_mxn,
                    'porcentaje_gastos_importacion': float(row['porcentaje_gastos_importacion']) if 'porcentaje_gastos_importacion' in row and pd.notna(row['porcentaje_gastos_importacion']) else 0,
                    'iva_monto_divisa': iva_monto_divisa,
                    'iva_monto_mxn': iva_monto_mxn,
                    'total_con_iva_divisa': total_con_iva_divisa,
                    'total_con_iva_mxn': total_con_iva_mxn,
                    'fecha_vencimiento': fecha_vencimiento,
                    'dias_transporte': dias_transporte,
                    'dias_puerto_planta': dias_puerto_planta,
                }
                
                compras.append(compra)
                
            except Exception as e:
                logger.warning(f"[COMPRAS_V2_PROCESSOR] Error procesando fila {idx} de compras: {str(e)}")
                continue
        
        return compras
    
    def _process_materiales_df(self, df: pd.DataFrame) -> list:
        """Procesa DataFrame de materiales y retorna lista de diccionarios"""
        materiales = []
        
        # Primero obtener el mapeo de IMI a compra_id de la base de datos
        compras_map = self._get_compras_id_map()
        
        for idx, row in df.iterrows():
            try:
                # Validar que tenga IMI y material_codigo
                if 'imi' not in row or pd.isna(row['imi']):
                    continue
                if 'material_codigo' not in row or pd.isna(row['material_codigo']):
                    continue
                
                imi = int(row['imi'])
                compra_id = compras_map.get(imi, imi)  # Usar el ID de compra_v2 si existe, sino usar IMI
                
                # Obtener datos básicos del Excel
                kg = float(row['kg']) if 'kg' in row and pd.notna(row['kg']) else 0
                pu_divisa = float(row['pu_divisa']) if 'pu_divisa' in row and pd.notna(row['pu_divisa']) else 0
                
                # Obtener datos de la compra para cálculos
                # Nota: Los datos de la compra se obtendrán en el servicio, aquí solo preparamos los datos básicos
                
                # Calcular campos automáticamente
                pu_mxn = float(row['pu_mxn']) if 'pu_mxn' in row and pd.notna(row['pu_mxn']) else 0
                costo_total_divisa = float(row['costo_total_divisa']) if 'costo_total_divisa' in row and pd.notna(row['costo_total_divisa']) else (kg * pu_divisa)
                
                # Si pu_mxn no viene, se calculará en el servicio usando tipo de cambio
                # Por ahora solo guardamos lo que viene del Excel
                
                # Calcular costo_total_mxn solo si tenemos pu_mxn
                costo_total_mxn = float(row['costo_total_mxn']) if 'costo_total_mxn' in row and pd.notna(row['costo_total_mxn']) else (kg * pu_mxn) if pu_mxn > 0 else 0
                
                # Los siguientes campos se calcularán en el servicio usando datos de la compra:
                # - pu_mxn (si no viene)
                # - porcentaje_gastos_importacion
                # - pu_mxn_importacion
                # - costo_total_mxn_importacion
                # - iva (si no viene)
                # - costo_total_con_iva
                
                pu_mxn_importacion = float(row['pu_mxn_importacion']) if 'pu_mxn_importacion' in row and pd.notna(row['pu_mxn_importacion']) else 0
                costo_total_mxn_imporacion = float(row['costo_total_mxn_importacion']) if 'costo_total_mxn_importacion' in row and pd.notna(row['costo_total_mxn_importacion']) else 0
                iva = float(row['iva']) if 'iva' in row and pd.notna(row['iva']) else 0
                costo_total_con_iva = float(row['costo_total_con_iva']) if 'costo_total_con_iva' in row and pd.notna(row['costo_total_con_iva']) else 0
                
                material = {
                    'compra_id': compra_id,
                    'compra_imi': imi,
                    'material_codigo': str(row['material_codigo']),
                    'kg': kg,
                    'pu_divisa': pu_divisa,
                    'pu_mxn': pu_mxn,
                    'costo_total_divisa': costo_total_divisa,
                    'costo_total_mxn': costo_total_mxn,
                    'pu_mxn_importacion': pu_mxn_importacion,
                    'costo_total_mxn_imporacion': costo_total_mxn_imporacion,
                    'iva': iva,
                    'costo_total_con_iva': costo_total_con_iva,
                }
                
                materiales.append(material)
                
            except Exception as e:
                logger.warning(f"[COMPRAS_V2_PROCESSOR] Error procesando fila {idx} de materiales: {str(e)}")
                continue
        
        return materiales
    
    def _get_compras_id_map(self) -> dict:
        """Obtiene mapeo de IMI a compra_id desde la base de datos"""
        try:
            conn = self.compras_service.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            # En compras_v2, imi ES la clave primaria, no hay columna id separada
            cursor.execute("SELECT imi FROM compras_v2")
            results = cursor.fetchall()
            cursor.close()
            
            # Mapear imi a sí mismo ya que es la clave primaria
            return {row['imi']: row['imi'] for row in results}
            
        except Exception as e:
            logger.warning(f"[COMPRAS_V2_PROCESSOR] No se pudo obtener mapeo de IDs: {str(e)}")
            return {}
    
    def _get_proveedor_info(self, nombre_proveedor: str) -> dict:
        """Obtiene información del proveedor desde la base de datos"""
        try:
            conn = self.compras_service.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT "Puerto", promedio_dias_produccion, promedio_dias_transporte_maritimo
                FROM "Proveedores"
                WHERE "Nombre" = %s
            """, (nombre_proveedor,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'puerto_origen': result['Puerto'],
                    'dias_produccion': result['promedio_dias_produccion'],
                    'dias_transporte': result['promedio_dias_transporte_maritimo']
                }
            else:
                logger.warning(f"[COMPRAS_V2_PROCESSOR] Proveedor '{nombre_proveedor}' no encontrado en tabla Proveedores")
                return {}
                
        except Exception as e:
            logger.warning(f"[COMPRAS_V2_PROCESSOR] Error obteniendo info de proveedor: {str(e)}")
            return {}
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        if hasattr(self, 'compras_service'):
            self.compras_service.close_connection()
