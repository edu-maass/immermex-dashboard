"""
Servicio de base de datos refactorizado para Immermex Dashboard
Utiliza servicios especializados para operaciones específicas
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import (
    Facturacion, Cobranza, CFDIRelacionado, Inventario, Pedido, 
    ArchivoProcesado, KPI, get_latest_data_summary
)
from services import FacturacionService, CobranzaService, PedidosService, KPIAggregator
from utils.validators import DataValidator
from utils.logging_config import setup_logging, log_performance
from datetime import datetime, timedelta
import logging
import hashlib
import time

logger = setup_logging()

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
        # Inicializar servicios especializados
        self.facturacion_service = FacturacionService(db)
        self.cobranza_service = CobranzaService(db)
        self.pedidos_service = PedidosService(db)
        self.kpi_aggregator = KPIAggregator(db)
    
    def save_processed_data(self, processed_data_dict: dict, archivo_info: dict) -> dict:
        """
        Guarda los datos procesados en la base de datos
        """
        try:
            # Crear registro de archivo
            archivo = self._create_archivo_record(archivo_info)
            
            # Limpiar datos anteriores si es necesario
            if archivo_info.get("reemplazar_datos", False):
                self._clear_existing_data()
            
            # Guardar cada tipo de datos usando servicios especializados
            facturas_count = self.facturacion_service.save_facturas(processed_data_dict.get("facturacion_clean", []), archivo.id)
            cobranzas_count = self.cobranza_service.save_cobranzas(processed_data_dict.get("cobranza_clean", []), archivo.id)
            anticipos_count = self._save_anticipos(processed_data_dict.get("cfdi_clean", []), archivo.id)
            pedidos_count = self.pedidos_service.save_pedidos(processed_data_dict.get("pedidos_clean", []), archivo.id)
            
            # Actualizar registro de archivo
            total_registros = facturas_count + cobranzas_count + anticipos_count + pedidos_count
            archivo.registros_procesados = total_registros
            archivo.estado = "procesado"
            
            self.db.commit()
            self.db.refresh(archivo)
            
            return {
                "archivo_id": archivo.id,
                "total_registros": total_registros,
                "facturas": facturas_count,
                "cobranzas": cobranzas_count,
                "anticipos": anticipos_count,
                "pedidos": pedidos_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error guardando datos procesados: {str(e)}")
            raise
    
    def _create_archivo_record(self, archivo_info: dict) -> ArchivoProcesado:
        """Crea registro de archivo procesado"""
        archivo = ArchivoProcesado(
            nombre_archivo=archivo_info.get("nombre_archivo", ""),
            fecha_procesamiento=datetime.now(),
            estado="procesando",
            registros_procesados=0,
            hash_archivo=self._calculate_file_hash(archivo_info.get("contenido", "")),
            tamaño_archivo=len(archivo_info.get("contenido", "")),
            algoritmo_usado="refactored_processing"
        )
        self.db.add(archivo)
        self.db.commit()
        self.db.refresh(archivo)
        return archivo
    
    def _calculate_file_hash(self, content: str) -> str:
        """Calcula hash del archivo para evitar duplicados"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _clear_existing_data(self):
        """Limpia datos existentes si se solicita reemplazar"""
        try:
            self.db.query(Facturacion).delete()
            self.db.query(Cobranza).delete()
            self.db.query(CFDIRelacionado).delete()
            self.db.query(Pedido).delete()
            self.db.query(Inventario).delete()
            self.db.commit()
            logger.info("Datos existentes eliminados")
        except Exception as e:
            logger.error(f"Error limpiando datos existentes: {str(e)}")
            raise
    
    def _save_anticipos(self, anticipos_data: list, archivo_id: int) -> int:
        """Guarda datos de anticipos (CFDI relacionados)"""
        count = 0
        for anticipo_data in anticipos_data:
            try:
                anticipo = CFDIRelacionado(
                    xml=DataValidator.safe_string(anticipo_data.get('xml', '')),
                    cliente_receptor=DataValidator.safe_string(anticipo_data.get('cliente_receptor', '')),
                    tipo_relacion=DataValidator.safe_string(anticipo_data.get('tipo_relacion', '')),
                    importe_relacion=DataValidator.safe_float(anticipo_data.get('importe_relacion', 0)),
                    uuid_factura_relacionada=DataValidator.safe_string(anticipo_data.get('uuid_factura_relacionada', '')),
                    archivo_id=archivo_id
                )
                self.db.add(anticipo)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando anticipo: {str(e)}")
                continue
        
        self.db.commit()
        return count
    
    def calculate_kpis(self, filtros: dict = None) -> dict:
        """
        Calcula KPIs usando el agregador especializado
        """
        return self.kpi_aggregator.calculate_kpis(filtros)
    
    def get_data_summary(self) -> dict:
        """Obtiene resumen de datos en la base de datos"""
        try:
            return get_latest_data_summary(self.db)
        except Exception as e:
            logger.error(f"Error obteniendo resumen de datos: {str(e)}")
            return {}
    
    def get_archivos_procesados(self) -> list:
        """Obtiene lista de archivos procesados"""
        try:
            return self.db.query(ArchivoProcesado).order_by(ArchivoProcesado.fecha_procesamiento.desc()).all()
        except Exception as e:
            logger.error(f"Error obteniendo archivos procesados: {str(e)}")
            return []
    
    def delete_archivo(self, archivo_id: int) -> bool:
        """Elimina un archivo y sus datos relacionados"""
        try:
            # Eliminar datos relacionados
            self.db.query(Facturacion).filter(Facturacion.archivo_id == archivo_id).delete()
            self.db.query(Cobranza).filter(Cobranza.archivo_id == archivo_id).delete()
            self.db.query(CFDIRelacionado).filter(CFDIRelacionado.archivo_id == archivo_id).delete()
            self.db.query(Pedido).filter(Pedido.archivo_id == archivo_id).delete()
            
            # Eliminar registro de archivo
            self.db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo_id).delete()
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error eliminando archivo {archivo_id}: {str(e)}")
            self.db.rollback()
            return False
