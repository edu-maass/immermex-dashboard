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
from utils.cache import cache_filtros, invalidate_data_cache
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
            
            # Limpiar datos anteriores si es necesario (solo para el tipo de datos correcto)
            tipo_datos = archivo_info.get("tipo_datos", "facturacion")
            if archivo_info.get("reemplazar_datos", False):
                if tipo_datos == "compras":
                    # Solo limpiar tabla de compras
                    try:
                        from sqlalchemy import text
                        self.db.execute(text("DELETE FROM compras"))
                        self.db.commit()
                        logger.info("Datos de compras existentes eliminados")
                    except Exception as e:
                        logger.error(f"Error limpiando datos de compras: {str(e)}")
                else:
                    # Limpiar datos de facturación
                    self._clear_existing_data()
            
            # Guardar cada tipo de datos usando servicios especializados
            facturas_count = self.facturacion_service.save_facturas(processed_data_dict.get("facturacion_clean", []), archivo.id)
            cobranzas_count = self.cobranza_service.save_cobranzas(processed_data_dict.get("cobranza_clean", []), archivo.id)
            anticipos_count = self._save_anticipos(processed_data_dict.get("cfdi_clean", []), archivo.id)
            pedidos_count = self.pedidos_service.save_pedidos(processed_data_dict.get("pedidos_clean", []), archivo.id)
            
            # Guardar datos de compras si están presentes
            compras_count = 0
            if "compras" in processed_data_dict:
                compras_count = self._save_compras(processed_data_dict.get("compras", []), archivo.id)
            
            # Actualizar registro de archivo
            total_registros = facturas_count + cobranzas_count + anticipos_count + pedidos_count + compras_count
            archivo.registros_procesados = total_registros
            archivo.estado = "procesado"
            
            self.db.commit()
            self.db.refresh(archivo)
            
            # Invalidar caché después de actualizar datos
            invalidate_data_cache()
            logger.info("Cache invalidated after data update")
            
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
        """Crea registro de archivo procesado o retorna el existente si ya fue procesado"""
        file_hash = self._calculate_file_hash(archivo_info.get("contenido", ""))
        logger.info(f"Buscando archivo con hash: {file_hash}")
        
        # Verificar si el archivo ya existe
        existing_archivo = self.db.query(ArchivoProcesado).filter(
            ArchivoProcesado.hash_archivo == file_hash
        ).first()
        
        if existing_archivo:
            logger.info(f"Archivo ya existe: {existing_archivo.nombre_archivo}, usando registro existente")
            return existing_archivo
        
        logger.info(f"Creando nuevo registro para archivo: {archivo_info.get('nombre_archivo', '')}")
        # Crear nuevo registro
        archivo = ArchivoProcesado(
            nombre_archivo=archivo_info.get("nombre_archivo", ""),
            fecha_procesamiento=datetime.now(),
            estado="procesando",
            registros_procesados=0,
            hash_archivo=file_hash,
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
    
    def _clean_nat_values(self, value):
        """Convierte valores NaT de pandas a None para PostgreSQL"""
        import pandas as pd
        if pd.isna(value):
            return None
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        return value
    
    def _save_compras(self, compras_data: list, archivo_id: int) -> int:
        """Guarda datos de compras"""
        count = 0
        for compra_data in compras_data:
            try:
                # Crear registro de compra usando SQL directo para evitar problemas de modelo
                compra_values = {
                    'fecha_compra': self._clean_nat_values(compra_data.get('fecha_compra')),
                    'numero_factura': DataValidator.safe_string(compra_data.get('numero_factura', '')),
                    'proveedor': DataValidator.safe_string(compra_data.get('proveedor', '')),
                    'concepto': DataValidator.safe_string(compra_data.get('concepto', '')),
                    'categoria': DataValidator.safe_string(compra_data.get('categoria', 'Importación')),
                    'subcategoria': DataValidator.safe_string(compra_data.get('subcategoria', '')),
                    'cantidad': DataValidator.safe_float(compra_data.get('cantidad', 0)),
                    'unidad': DataValidator.safe_string(compra_data.get('unidad', 'KG')),
                    'precio_unitario': DataValidator.safe_float(compra_data.get('precio_unitario', 0)),
                    'subtotal': DataValidator.safe_float(compra_data.get('subtotal', 0)),
                    'iva': DataValidator.safe_float(compra_data.get('iva', 0)),
                    'total': DataValidator.safe_float(compra_data.get('total', 0)),
                    'moneda': DataValidator.safe_string(compra_data.get('moneda', 'USD')),
                    'tipo_cambio': DataValidator.safe_float(compra_data.get('tipo_cambio', 1.0)),
                    'forma_pago': DataValidator.safe_string(compra_data.get('forma_pago', '')),
                    'dias_credito': DataValidator.safe_int(compra_data.get('dias_credito', 0)),
                    'fecha_vencimiento': self._clean_nat_values(compra_data.get('fecha_vencimiento')),
                    'fecha_pago': self._clean_nat_values(compra_data.get('fecha_pago')),
                    'estado_pago': DataValidator.safe_string(compra_data.get('estado_pago', 'pendiente')),
                    'centro_costo': DataValidator.safe_string(compra_data.get('centro_costo', '')),
                    'proyecto': DataValidator.safe_string(compra_data.get('proyecto', '')),
                    'notas': DataValidator.safe_string(compra_data.get('notas', '')),
                    'archivo_origen': f"Upload/{archivo_id}",
                    'archivo_id': archivo_id,
                    'mes': DataValidator.safe_int(compra_data.get('mes', 0)),
                    'año': DataValidator.safe_int(compra_data.get('año', 0)),
                    # Campos específicos de importación
                    'imi': DataValidator.safe_string(compra_data.get('imi', '')),
                    'puerto_origen': DataValidator.safe_string(compra_data.get('puerto_origen', '')),
                    'fecha_salida_puerto': self._clean_nat_values(compra_data.get('fecha_salida_puerto')),
                    'fecha_arribo_puerto': self._clean_nat_values(compra_data.get('fecha_arribo_puerto')),
                    'fecha_entrada_inmermex': self._clean_nat_values(compra_data.get('fecha_entrada_inmermex')),
                    'precio_dlls': DataValidator.safe_float(compra_data.get('precio_dlls', 0)),
                    'xr': DataValidator.safe_float(compra_data.get('xr', 0)),
                    'financiera': DataValidator.safe_string(compra_data.get('financiera', '')),
                    'porcentaje_anticipo': DataValidator.safe_float(compra_data.get('porcentaje_anticipo', 0)),
                    'fecha_anticipo': self._clean_nat_values(compra_data.get('fecha_anticipo')),
                    'anticipo_dlls': DataValidator.safe_float(compra_data.get('anticipo_dlls', 0)),
                    'tipo_cambio_anticipo': DataValidator.safe_float(compra_data.get('tipo_cambio_anticipo', 0)),
                    'pago_factura_dlls': DataValidator.safe_float(compra_data.get('pago_factura_dlls', 0)),
                    'tipo_cambio_factura': DataValidator.safe_float(compra_data.get('tipo_cambio_factura', 0)),
                    'pu_mxn': DataValidator.safe_float(compra_data.get('pu_mxn', 0)),
                    'precio_mxn': DataValidator.safe_float(compra_data.get('precio_mxn', 0)),
                    'porcentaje_imi': DataValidator.safe_float(compra_data.get('porcentaje_imi', 0)),
                    'fecha_entrada_aduana': self._clean_nat_values(compra_data.get('fecha_entrada_aduana')),
                    'pedimento': DataValidator.safe_string(compra_data.get('pedimento', '')),
                    'gastos_aduanales': DataValidator.safe_float(compra_data.get('gastos_aduanales', 0)),
                    'costo_total': DataValidator.safe_float(compra_data.get('costo_total', 0)),
                    'porcentaje_gastos_aduanales': DataValidator.safe_float(compra_data.get('porcentaje_gastos_aduanales', 0)),
                    'pu_total': DataValidator.safe_float(compra_data.get('pu_total', 0)),
                    'fecha_pago_impuestos': self._clean_nat_values(compra_data.get('fecha_pago_impuestos')),
                    'fecha_salida_aduana': self._clean_nat_values(compra_data.get('fecha_salida_aduana')),
                    'dias_en_puerto': DataValidator.safe_int(compra_data.get('dias_en_puerto', 0)),
                    'agente': DataValidator.safe_string(compra_data.get('agente', '')),
                    'fac_agente': DataValidator.safe_string(compra_data.get('fac_agente', ''))
                }
                
                # Insertar usando SQL directo
                insert_query = """
                    INSERT INTO compras (
                        fecha_compra, numero_factura, proveedor, concepto, categoria, subcategoria,
                        cantidad, unidad, precio_unitario, subtotal, iva, total, moneda, tipo_cambio,
                        forma_pago, dias_credito, fecha_vencimiento, fecha_pago, estado_pago,
                        centro_costo, proyecto, notas, archivo_origen, archivo_id, mes, año,
                        imi, puerto_origen, fecha_salida_puerto, fecha_arribo_puerto, fecha_entrada_inmermex,
                        precio_dlls, xr, financiera, porcentaje_anticipo, fecha_anticipo, anticipo_dlls,
                        tipo_cambio_anticipo, pago_factura_dlls, tipo_cambio_factura, pu_mxn, precio_mxn,
                        porcentaje_imi, fecha_entrada_aduana, pedimento, gastos_aduanales, costo_total,
                        porcentaje_gastos_aduanales, pu_total, fecha_pago_impuestos, fecha_salida_aduana,
                        dias_en_puerto, agente, fac_agente
                    ) VALUES (
                        :fecha_compra, :numero_factura, :proveedor, :concepto, :categoria, :subcategoria,
                        :cantidad, :unidad, :precio_unitario, :subtotal, :iva, :total, :moneda, :tipo_cambio,
                        :forma_pago, :dias_credito, :fecha_vencimiento, :fecha_pago, :estado_pago,
                        :centro_costo, :proyecto, :notas, :archivo_origen, :archivo_id, :mes, :año,
                        :imi, :puerto_origen, :fecha_salida_puerto, :fecha_arribo_puerto, :fecha_entrada_inmermex,
                        :precio_dlls, :xr, :financiera, :porcentaje_anticipo, :fecha_anticipo, :anticipo_dlls,
                        :tipo_cambio_anticipo, :pago_factura_dlls, :tipo_cambio_factura, :pu_mxn, :precio_mxn,
                        :porcentaje_imi, :fecha_entrada_aduana, :pedimento, :gastos_aduanales, :costo_total,
                        :porcentaje_gastos_aduanales, :pu_total, :fecha_pago_impuestos, :fecha_salida_aduana,
                        :dias_en_puerto, :agente, :fac_agente
                    )
                """
                
                from sqlalchemy import text
                self.db.execute(text(insert_query), compra_values)
                count += 1
                
            except Exception as e:
                logger.warning(f"Error guardando compra: {str(e)}")
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
    
    @cache_filtros(ttl=600)  # Cache por 10 minutos
    def get_filtros_disponibles(self) -> dict:
        """Obtiene opciones disponibles para filtros"""
        try:
            from sqlalchemy import and_
            
            # Pedidos disponibles - usar pedido (columna C) para filtrado
            pedidos = self.db.query(Pedido.pedido).filter(Pedido.pedido.isnot(None)).distinct().all()
            pedidos_list = [p[0] for p in pedidos if p[0]]
            
            # Clientes disponibles
            clientes = self.db.query(Facturacion.cliente).filter(Facturacion.cliente.isnot(None)).distinct().all()
            clientes_list = [c[0] for c in clientes if c[0]]
            
            # Materiales disponibles
            materiales = self.db.query(Pedido.material).filter(Pedido.material.isnot(None)).distinct().all()
            materiales_list = [m[0] for m in materiales if m[0]]
            
            # Meses y años disponibles
            meses_años = self.db.query(Facturacion.mes, Facturacion.año).filter(
                and_(Facturacion.mes.isnot(None), Facturacion.año.isnot(None))
            ).distinct().all()
            
            meses_disponibles = sorted(set(m[0] for m in meses_años if m[0]))
            años_disponibles = sorted(set(m[1] for m in meses_años if m[1]))
            
            return {
                "pedidos": pedidos_list,
                "clientes": clientes_list,
                "materiales": materiales_list,
                "meses": meses_disponibles,
                "años": años_disponibles
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo filtros disponibles: {str(e)}")
            return {
                "pedidos": [],
                "clientes": [],
                "materiales": [],
                "meses": [],
                "años": []
            }
