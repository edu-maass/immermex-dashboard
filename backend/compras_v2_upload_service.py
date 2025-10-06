"""
Servicio actualizado para upload de compras_v2 y compras_v2_materiales
Integrado con el nuevo procesador robusto y servicio de guardado
"""

from sqlalchemy.orm import Session
from database import (
    ArchivoProcesado, get_db
)
from compras_processor_v2_robust import process_compras_v2
from compras_v2_service import ComprasV2Service
import logging
import os
from datetime import datetime
from typing import Dict, Any

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
            
            # Paso 1: Procesar archivo en memoria (sin base de datos)
            logger.info("[COMPRAS_V2_SERVICE] Paso 1: Procesando archivo con nuevo procesador...")
            processed_data_dict, kpis = process_compras_v2(file_content, filename)
            
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
            logger.info(f"  - Materiales guardados: {save_results['materiales_guardados']}")
            logger.info(f"  - Total procesados: {save_results['total_procesados']}")
            
            return {
                "success": True,
                "archivo_id": archivo_id,
                "compras_guardadas": save_results['compras_guardadas'],
                "materiales_guardados": save_results['materiales_guardados'],
                "total_procesados": save_results['total_procesados'],
                "kpis": kpis,
                "mensaje": f"Archivo de compras procesado exitosamente. {save_results['compras_guardadas']} compras y {save_results['materiales_guardados']} materiales guardados."
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
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        if hasattr(self, 'compras_service'):
            self.compras_service.close_connection()
