"""
Servicio especializado para el upload de archivos de compras
Manejo mejorado de sesiones SQLAlchemy para evitar ObjectDeletedError con Supabase
"""

from sqlalchemy.orm import Session
from database import (
    ArchivoProcesado, Compras, get_db
)
from compras_processor_v2 import process_compras_v2
import logging
import os
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ComprasUploadService:
    """Servicio especializado para manejar uploads de compras con mejor gestión de sesiones"""
    
    def upload_compras_file(self, file_content: bytes, filename: str, replace_data: bool = True) -> Dict[str, Any]:
        """
        Procesa y guarda archivo de compras usando múltiples sesiones para evitar problemas de estado
        """
        try:
            logger.info(f"[COMPRAS_SERVICE] Iniciando procesamiento de: {filename}")
            
            # Paso 1: Procesar archivo en memoria (sin base de datos)
            logger.info("[COMPRAS_SERVICE] Paso 1: Procesando archivo...")
            processed_data_dict, kpis = process_compras_v2(file_content, filename)
            logger.info(f"[COMPRAS_SERVICE] Datos procesados: {len(processed_data_dict.get('compras', []))} compras")
            
            # Paso 2: Crear registro de archivo en sesión separada
            logger.info("[COMPRAS_SERVICE] Paso 2: Creando registro de archivo...")
            archivo_id = self._create_archivo_record(filename, len(file_content), replace_data)
            
            if not archivo_id:
                raise Exception("No se pudo crear el registro de archivo")
            
            logger.info(f"[COMPRAS_SERVICE] Archivo creado con ID: {archivo_id}")
            
            # Paso 3: Guardar compras en sesión separada
            logger.info("[COMPRAS_SERVICE] Paso 3: Guardando compras...")
            compras_count = self._save_compras_in_new_session(processed_data_dict.get('compras', []), archivo_id)
            
            # Paso 4: Actualizar estado del archivo en sesión separada
            logger.info("[COMPRAS_SERVICE] Paso 4: Actualizando estado del archivo...")
            self._update_archivo_status(archivo_id, "procesado", compras_count)
            
            logger.info(f"[COMPRAS_SERVICE] Proceso completado exitosamente: {compras_count} compras guardadas")
            
            return {
                "success": True,
                "archivo_id": archivo_id,
                "registros_procesados": compras_count,
                "kpis_companos": kpis,
                "mensaje": f"Archivo de compras procesado exitosamente. {compras_count} registros guardados."
            }
            
        except Exception as e:
            logger.error(f"[COMPRAS_SERVICE] Error en procesamiento: {str(e)}")
            import traceback
            logger.error(f"[COMPRAS_SERVICE] Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    def _create_archivo_record(self, filename: str, file_size: int, replace_data: bool) -> int:
        """Crea registro de archivo en sesión separada"""
        db = next(get_db())
        try:
            # Si se debe reemplazar datos, limpiar existentes
            if replace_data:
                logger.info("[COMPRAS_SERVICE] Limpiando datos existentes...")
                self._clear_existing_data(db)
            
            # Crear nuevo registro
            archivo = ArchivoProcesado(
                nombre_archivo=filename,
                tamaño_archivo=file_size,
                algoritmo_usado="compras_v2",
                estado="en_proceso",
                fecha_procesamiento=datetime.utcnow()
            )
            
            db.add(archivo)
            db.commit()
            db.refresh(archivo)  # Refrescar para obtener el ID
            
            logger.info(f"[COMPRAS_SERVICE] Archivo creado: ID={archivo.id}, nombre={filename}")
            return archivo.id
            
        except Exception as e:
            logger.error(f"[COMPRAS_SERVICE] Error creando archivo: {str(e)}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def _save_compras_in_new_session(self, compras_data: list, archivo_id: int) -> int:
        """Guarda compras en sesión completamente separada"""
        db = next(get_db())
        try:
            logger.info(f"[COMPRAS_SERVICE] Guardando {len(compras_data)} compras con archivo_id={archivo_id}")
            
            count = 0
            for compra_data in compras_data:
                try:
                    # Crear objeto Compras
                    compra = Compras(
                        fecha_compra=self._safe_date(compra_data.get('fecha_compra')),
                        numero_factura=self._safe_string(compra_data.get('numero_factura', '')),
                        proveedor=self._safe_string(compra_data.get('proveedor', '')),
                        concepto=self._safe_string(compra_data.get('concepto', '')),
                        categoria=self._safe_string(compra_data.get('categoria', '')),
                        subcategoria=self._safe_string(compra_data.get('subcategoria', '')),
                        cantidad=self._safe_float(compra_data.get('cantidad', 0)),
                        unidad=self._safe_string(compra_data.get('unidad', 'KG')),
                        precio_unitario=self._safe_float(compra_data.get('precio_unitario', 0)),
                        subtotal=self._safe_float(compra_data.get('subtotal', 0)),
                        iva=self._safe_float(compra_data.get('iva', 0)),
                        total=self._safe_float(compra_data.get('total', 0)),
                        moneda=self._safe_string(compra_data.get('moneda', 'USD')),
                        tipo_cambio=self._safe_float(compra_data.get('tipo_cambio', 1.0)),
                        forma_pago=self._safe_string(compra_data.get('forma_pago', '')),
                        dias_credito=self._safe_int(compra_data.get('dias_credito', 0)),
                        fecha_vencimiento=self._safe_date(compra_data.get('fecha_vencimiento')),
                        fecha_pago=self._safe_date(compra_data.get('fecha_pago')),
                        estado_pago=self._safe_string(compra_data.get('estado_pago', 'pendiente')),
                        centro_costo=self._safe_string(compra_data.get('centro_costo', '')),
                        proyecto=self._safe_string(compra_data.get('proyecto', '')),
                        notas=self._safe_string(compra_data.get('notas', '')),
                        archivo_origen=self._safe_string(compra_data.get('archivo_origen', '')),
                        archivo_id=archivo_id,
                        mes=self._safe_int(compra_data.get('mes')),
                        año=self._safe_int(compra_data.get('año')),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(compra)
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"[COMPRAS_SERVICE] Error guardando compra individual: {str(e)}")
                    continue
            
            # Commit final de todas las compras
            db.commit()
            logger.info(f"[COMPRAS_SERVICE] {count} compras guardadas exitosamente")
            return count
            
        except Exception as e:
            logger.error(f"[COMPRAS_SERVICE] Error en guardado masivo: {str(e)}")
            db.rollback()
            return 0
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
                logger.info(f"[COMPRAS_SERVICE] Archivo {archivo_id} actualizado a estado {estado}")
            else:
                logger.error(f"[COMPRAS_SERVICE] No se encontró archivo con ID {archivo_id}")
                
        except Exception as e:
            logger.error(f"[COMPRAS_SERVICE] Error actualizando archivo: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def _clear_existing_data(self, db: Session):
        """Limpia datos existentes"""
        try:
            # Limpiar en orden debido a foreign keys
            db.query(Compras).delete()
            db.query(ArchivoProcesado).delete()
            db.commit()
            logger.info("[COMPRAS_SERVICE] Datos existentes limpiados")
        except Exception as e:
            logger.error(f"[COMPRAS_SERVICE] Error limpiando datos: {str(e)}")
            db.rollback()
    
    # Helper methods for data validation
    def _safe_date(self, value):
        """Convierte valor a date de forma segura"""
        if not value or value == 'NaT' or str(value) == 'NaT':
            return None
        try:
            # Verificar si es NaT de pandas
            if hasattr(value, 'strftime') and str(value) == 'NaT':
                return None
            if isinstance(value, str):
                if value.lower() in ['nat', 'nan', '']:
                    return None
                return datetime.strptime(value, '%Y-%m-%d').date()
            elif isinstance(value, datetime):
                return value.date()
            elif hasattr(value, 'date'):  # Para objetos date
                return value
            return value
        except Exception as e:
            logger.debug(f"Error convirtiendo fecha {value}: {str(e)}")
            return None
    
    def _safe_int(self, value, default=0):
        """Convierte valor a int de forma segura"""
        if value is None or value == '':
            return default
        try:
            return int(float(value))
        except:
            return default
    
    def _safe_float(self, value, default=0.0):
        """Convierte valor a float de forma segura"""
        if value is None or value == '':
            return default
        try:
            return float(value)
        except:
            return default
    
    def _safe_string(self, value, default=''):
        """Convierte valor a string de forma segura"""
        if value is None:
            return default
        return str(value).strip() if str(value).strip() != 'nan' else default
