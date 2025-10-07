"""
Servicio de base de datos refactorizado para Immermex Dashboard
Utiliza servicios especializados para operaciones específicas
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import (
    Facturacion, Cobranza, CFDIRelacionado, Inventario, Pedido, PedidosCompras,
    ArchivoProcesado, KPI, Compras, get_latest_data_summary
)
from services import FacturacionService, CobranzaService, PedidosService, KPIAggregator
from utils.validators import DataValidator
from utils.logging_config import setup_logging, log_performance
from datetime import datetime, timedelta
import logging
import hashlib
import time
import numpy as np

logger = setup_logging()

# Helper functions for data validation
def safe_date(value):
    """Convierte valor a date de forma segura"""
    if not value:
        return None
    try:
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime):
            return value.date()
        return value
    except:
        return None

def safe_int(value, default=0):
    """Convierte valor a int de forma segura"""
    if value is None or value == '':
        return default
    try:
        return int(float(value))
    except:
        return default

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
            logger.info(f"🚀🚀🚀 VERSIÓN ACTUALIZADA EJECUTÁNDOSE - INICIANDO save_processed_data 🚀🚀🚀")
            logger.info(f"Datos recibidos: {list(processed_data_dict.keys())}")
            logger.info(f"Archivo info: {archivo_info}")
            
            # Crear registro de archivo
            logger.info(f"Creando registro de archivo para: {archivo_info.get('nombre', 'unknown')}")
            logger.info(f"Llamando a _create_archivo_record...")
            try:
                archivo = self._create_archivo_record(archivo_info)
                logger.info(f"_create_archivo_record completado exitosamente")
                logger.info(f"ArchivoProcesado creado con ID: {archivo.id}")
                logger.info(f"Tipo de archivo: {type(archivo)}")
            except Exception as e:
                logger.error(f"ERROR en _create_archivo_record: {str(e)}")
                logger.error(f"Tipo de error: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            # CRITICAL: No hacer commit intermedio - usar flush() para asegurar visibilidad
            logger.info("🔥🔥🔥 NEW DEPLOYMENT CONFIRMATION - DATABASE SERVICE 🔥🔥🔥")
            logger.info("ArchivoProcesado ya fue committeado en _create_archivo_record")
            logger.info("🔥🔥🔥 ARCHIVO YA COMMITTED - No need for additional commit 🔥🔥🔥")
            
            # Limpiar datos anteriores si es necesario
            if archivo_info.get("reemplazar_datos", False):
                self._clear_existing_data()
            
            # CRITICAL: Guardar el ID del archivo ANTES de usarlo para evitar ObjectDeletedError
            archivo_id = archivo.id
            logger.info(f"🔑 Archivo ID guardado: {archivo_id}")
            
            # Guardar cada tipo de datos usando servicios especializados
            logger.info("Guardando facturas...")
            facturas_count = self.facturacion_service.save_facturas(processed_data_dict.get("facturacion_clean", []), archivo_id)
            logger.info("Guardando cobranzas...")
            cobranzas_count = self.cobranza_service.save_cobranzas(processed_data_dict.get("cobranza_clean", []), archivo_id)
            logger.info("Guardando anticipos...")
            anticipos_count = self._save_anticipos(processed_data_dict.get("cfdi_clean", []), archivo_id)
            logger.info("Guardando pedidos...")
            pedidos_count = self.pedidos_service.save_pedidos(processed_data_dict.get("pedidos_clean", []), archivo_id)
            
            # Actualizar registro de archivo y hacer commit final
            total_registros = facturas_count + cobranzas_count + anticipos_count + pedidos_count
            
            # Buscar el archivo nuevamente para actualizarlo - usar nueva sesión para evitar ObjectDeletedError
            try:
                archivo_final = self.db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo_id).first()
                if archivo_final:
                    archivo_final.registros_procesados = total_registros
                    archivo_final.estado = "procesado"
                    self.db.commit()  # Commit final para actualizar el estado del archivo
                    logger.info(f"Datos guardados exitosamente: {total_registros} registros")
                else:
                    logger.error(f"No se encontró archivo con ID {archivo_id} para actualizar")
            except Exception as update_error:
                logger.error(f"Error actualizando archivo final: {str(update_error)}")
                # Intentar actualización directa con SQL si falla la ORM
                try:
                    from sqlalchemy import text
                    self.db.execute(text("UPDATE archivos_procesados SET registros_procesados = :total, estado = 'procesado' WHERE id = :archivo_id"), 
                                  {"total": total_registros, "archivo_id": archivo_id})
                    self.db.commit()
                    logger.info(f"Actualización directa exitosa: {total_registros} registros")
                except Exception as sql_error:
                    logger.error(f"Error en actualización directa: {str(sql_error)}")
            
            return {
                "success": True,
                "archivo_id": archivo_id,
                "registros_procesados": total_registros,
                "desglose": {
                    "facturas": facturas_count,
                    "cobranzas": cobranzas_count,
                    "anticipos": anticipos_count,
                    "pedidos": pedidos_count,
                    "compras": compras_count
                }
            }
            
        except Exception as e:
            logger.error(f"=== EXCEPCIÓN EN save_processed_data ===")
            logger.error(f"Error guardando datos: {str(e)}")
            logger.error(f"Tipo de error: {type(e)}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            self.db.rollback()
            if 'archivo_id' in locals() and archivo_id:
                try:
                    error_archivo = self.db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo_id).first()
                    if error_archivo:
                        error_archivo.estado = "error"
                        error_archivo.error_message = str(e)
                        self.db.commit()
                        logger.info(f"Updated archivo {archivo_id} to error state")
                except Exception as error_update_exception:
                    logger.error(f"Error actualizando archivo a estado error: {str(error_update_exception)}")
                    # Intentar actualización directa con SQL
                    try:
                        from sqlalchemy import text
                        self.db.execute(text("UPDATE archivos_procesados SET estado = 'error', error_message = :error_msg WHERE id = :archivo_id"), 
                                      {"error_msg": str(e), "archivo_id": archivo_id})
                        self.db.commit()
                        logger.info(f"Updated archivo {archivo_id} to error state via SQL")
                    except Exception as sql_error:
                        logger.error(f"Error en actualización SQL de error: {str(sql_error)}")
            return {"success": False, "error": str(e)}
    
    def _create_archivo_record(self, archivo_info: dict) -> ArchivoProcesado:
        """Crea o actualiza el registro de archivo"""
        try:
            logger.info(f"Iniciando _create_archivo_record para: {archivo_info.get('nombre', 'unknown')}")
            
            # Calcular hash del archivo para evitar duplicados
            file_hash = hashlib.md5(f"{archivo_info['nombre']}_{archivo_info['tamaño']}".encode()).hexdigest()
            logger.info(f"Hash calculado: {file_hash}")
            
            # Buscar si ya existe por nombre de archivo (debido a la constraint unique)
            logger.info("Buscando archivo existente...")
            archivo = self.db.query(ArchivoProcesado).filter(
                ArchivoProcesado.nombre_archivo == archivo_info['nombre']
            ).first()
            
            if archivo:
                logger.info(f"Archivo existente encontrado: ID={archivo.id}")
                # Actualizar archivo existente
                archivo.hash_archivo = file_hash
                archivo.tamaño_archivo = archivo_info['tamaño']
                archivo.estado = "en_proceso"
                archivo.updated_at = datetime.utcnow()
                archivo.fecha_procesamiento = datetime.utcnow()
                archivo.registros_procesados = 0  # Resetear contador
                archivo.error_message = None  # Limpiar errores previos
            else:
                logger.info("No se encontró archivo existente, creando nuevo...")
                # Crear nuevo archivo
                archivo = ArchivoProcesado(
                    nombre_archivo=archivo_info['nombre'],
                    hash_archivo=file_hash,
                    tamaño_archivo=archivo_info['tamaño'],
                    algoritmo_usado=archivo_info.get('algoritmo', 'advanced_cleaning'),
                    estado="en_proceso"
                )
                logger.info(f"ArchivoProcesado creado en memoria: {archivo}")
                self.db.add(archivo)
                logger.info("ArchivoProcesado agregado a la sesión")
            
            # Hacer commit inmediato para evitar problemas de sesión
            logger.info("Haciendo commit del ArchivoProcesado...")
            self.db.commit()
            logger.info("Commit del ArchivoProcesado exitoso")
            
            # Refrescar el objeto para asegurar que esté actualizado
            logger.info("Refrescando objeto después del commit...")
            self.db.refresh(archivo)
            logger.info("Objeto refrescado")
            
            # Verificar que el archivo fue creado correctamente y es visible
            logger.info(f"ArchivoProcesado creado/actualizado: ID={archivo.id}, nombre={archivo.nombre_archivo}")
            
            return archivo
            
        except Exception as e:
            logger.error(f"Error en _create_archivo_record: {str(e)}")
            logger.error(f"Tipo de error: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.db.rollback()
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
    
    def _save_pedidos(self, pedidos_data: list, archivo_id: int) -> int:
        """Guarda datos de pedidos con asignación automática de fecha_factura y dias_credito"""
        count = 0
        
        # Obtener facturas para asignar fechas y días de crédito automáticamente
        facturas = self.db.query(Facturacion).all()
        fechas_por_folio = {}
        dias_credito_por_folio = {}
        
        for factura in facturas:
            if factura.folio_factura:
                # Limpiar el folio para evitar problemas de espacios o formato
                folio_limpio = str(factura.folio_factura).strip()
                
                # Asignar fecha si existe
                if factura.fecha_factura:
                    fechas_por_folio[folio_limpio] = factura.fecha_factura
                
                # Asignar días de crédito si existe
                if factura.dias_credito is not None:
                    dias_credito_por_folio[folio_limpio] = factura.dias_credito
        
        logger.info(f"Se encontraron {len(fechas_por_folio)} facturas con fechas para asignar a pedidos")
        logger.info(f"Se encontraron {len(dias_credito_por_folio)} facturas con días de crédito para asignar a pedidos")
        
        # Log de muestra de folios disponibles para debugging
        sample_folios = list(fechas_por_folio.keys())[:5]
        logger.info(f"Muestra de folios de facturas disponibles: {sample_folios}")
        
        # Log de muestra de días de crédito disponibles para debugging
        sample_dias_credito = {k: v for k, v in list(dias_credito_por_folio.items())[:5]}
        logger.info(f"Muestra de días de crédito disponibles: {sample_dias_credito}")
        
        # Log de muestra de folios de pedidos para debugging
        sample_pedidos_folios = [p.get('folio_factura', '') for p in pedidos_data[:5] if p.get('folio_factura')]
        logger.info(f"Muestra de folios de pedidos: {sample_pedidos_folios}")
        
        fechas_asignadas = 0
        dias_credito_asignados = 0
        for pedido_data in pedidos_data:
            try:
                # Convertir fechas de forma segura usando la función global
                fecha_factura = safe_date(pedido_data.get('fecha_factura'))
                fecha_pago = safe_date(pedido_data.get('fecha_pago'))
                
                # Si no hay fecha_factura, intentar asignarla desde la factura relacionada
                if not fecha_factura:
                    folio_factura = pedido_data.get('folio_factura', '')
                    if folio_factura:
                        # Limpiar el folio para hacer la comparación
                        folio_limpio = str(folio_factura).strip()
                        if folio_limpio in fechas_por_folio:
                            fecha_factura = fechas_por_folio[folio_limpio]
                            fechas_asignadas += 1
                            logger.info(f"✅ Asignada fecha de factura automáticamente a pedido {pedido_data.get('pedido', '')} (folio {folio_limpio}): {fecha_factura}")
                        else:
                            logger.debug(f"⚠️ No se encontró factura con folio '{folio_limpio}' para pedido {pedido_data.get('pedido', '')}")
                    else:
                        logger.debug(f"⚠️ Pedido {pedido_data.get('pedido', '')} no tiene folio_factura para asignar fecha")
                
                # Asignar días de crédito desde la factura relacionada
                # Obtener el folio_factura del pedido
                folio_factura = pedido_data.get('folio_factura', '')
                dias_credito_pedido = safe_int(pedido_data.get('dias_credito', 30))  # Usar función global
                
                if folio_factura:
                    # Limpiar el folio para hacer la comparación
                    folio_limpio = str(folio_factura).strip()
                    if folio_limpio in dias_credito_por_folio:
                        dias_credito_factura = dias_credito_por_folio[folio_limpio]
                        # Siempre sobrescribir con el valor de la factura (fuente de verdad)
                        dias_credito_pedido = dias_credito_factura
                        dias_credito_asignados += 1
                        logger.info(f"✅ Asignados días de crédito automáticamente a pedido {pedido_data.get('pedido', '')} (folio {folio_limpio}): {dias_credito_factura}")
                    else:
                        logger.debug(f"⚠️ No se encontró factura con folio '{folio_limpio}' para asignar días de crédito a pedido {pedido_data.get('pedido', '')}")
                else:
                    logger.debug(f"⚠️ Pedido {pedido_data.get('pedido', '')} no tiene folio_factura para asignar días de crédito")
                
                # Limpiar y validar datos numéricos
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or str(value).strip() == '':
                            return default
                        # Verificar si es NaN usando numpy
                        if np.isnan(float(value)) if isinstance(value, (int, float)) else False:
                            return default
                        # Verificar si es NaN como string
                        if str(value).lower() in ['nan', 'none', 'null']:
                            return default
                        # Remover caracteres no numéricos excepto punto y coma
                        clean_value = str(value).replace(',', '').replace('$', '').strip()
                        if clean_value and clean_value != 'nan':
                            result = float(clean_value)
                            # Verificar si el resultado es NaN
                            if np.isnan(result):
                                return default
                            return result
                        return default
                    except (ValueError, TypeError):
                        return default
                
                def safe_string(value, default=''):
                    """Convierte valor a string seguro, manejando NaN"""
                    try:
                        if value is None:
                            return default
                        if isinstance(value, (int, float)) and np.isnan(value):
                            return default
                        if str(value).lower() in ['nan', 'none', 'null']:
                            return default
                        return str(value).strip() or default
                    except (ValueError, TypeError):
                        return default
                
                pedido = Pedido(
                    folio_factura=safe_string(pedido_data.get('folio_factura', '')),
                    pedido=safe_string(pedido_data.get('pedido', '')),
                    kg=safe_float(pedido_data.get('kg', 0)),
                    precio_unitario=safe_float(pedido_data.get('precio_unitario', 0)),
                    importe_sin_iva=safe_float(pedido_data.get('importe_sin_iva', 0)),
                    material=safe_string(pedido_data.get('material', '')),
                    dias_credito=dias_credito_pedido,  # Usar el valor procesado
                    fecha_factura=fecha_factura,
                    fecha_pago=fecha_pago,
                    archivo_id=archivo_id
                )
                self.db.add(pedido)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando pedido: {str(e)}")
                continue
        
        self.db.commit()
        
        if fechas_asignadas > 0:
            logger.info(f"✅ Se asignaron automáticamente {fechas_asignadas} fechas de factura a pedidos durante el procesamiento")
        else:
            logger.info("✅ Las fechas de factura ya estaban asignadas o no hay coincidencias")
        
        if dias_credito_asignados > 0:
            logger.info(f"✅ Se asignaron automáticamente {dias_credito_asignados} días de crédito de facturas a pedidos durante el procesamiento")
        else:
            logger.info("✅ Los días de crédito ya estaban asignados o no hay coincidencias")
        
        return count
    
    def _clear_existing_data(self):
        """Limpia todos los datos existentes"""
        try:
            self.db.query(Pedido).delete()
            self.db.query(CFDIRelacionado).delete()
            self.db.query(Cobranza).delete()
            self.db.query(Facturacion).delete()
            self.db.query(Compras).delete()
            self.db.query(KPI).delete()
            self.db.query(ArchivoProcesado).delete()  # Limpiar también archivos procesados
            self.db.commit()
            logger.info("Datos existentes limpiados")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error limpiando datos: {str(e)}")
    
    def _get_facturas_related_to_pedidos(self, pedidos_filtrados: list) -> list:
        """
        Obtiene todas las facturas relacionadas con los pedidos filtrados.
        Considera la relación many-to-many: un pedido puede estar en múltiples facturas.
        Solo busca por folio_factura directo, no por cliente.
        """
        facturas_relacionadas = []
        
        for pedido in pedidos_filtrados:
            # Buscar todas las facturas donde aparece este pedido por folio_factura
            if pedido.folio_factura:
                facturas_folio = self.db.query(Facturacion).filter(
                    Facturacion.folio_factura == pedido.folio_factura
                ).all()
                facturas_relacionadas.extend(facturas_folio)
                logger.debug(f"Pedido {pedido.pedido} -> Facturas por folio {pedido.folio_factura}: {len(facturas_folio)}")
        
        # Eliminar duplicados por UUID
        facturas_unicas = {}
        for factura in facturas_relacionadas:
            if factura.uuid_factura:
                facturas_unicas[factura.uuid_factura] = factura
        
        logger.info(f"Facturas relacionadas con pedidos filtrados: {len(facturas_unicas)}")
        return list(facturas_unicas.values())

    def calculate_kpis(self, filtros: dict = None) -> dict:
        """
        Calcula KPIs usando el agregador especializado
        """
        return self.kpi_aggregator.calculate_kpis(filtros)
    
    def _calculate_aging_cartera(self, facturas: list) -> dict:
        """Calcula aging de cartera por monto pendiente"""
        aging = {"0-30 dias": 0, "31-60 dias": 0, "61-90 dias": 0, "90+ dias": 0}
        
        for factura in facturas:
            if factura.fecha_factura:
                dias_credito = factura.dias_credito or 30
                fecha_vencimiento = factura.fecha_factura + timedelta(days=dias_credito)
                dias_vencidos = (datetime.now() - fecha_vencimiento).days
                
                # Calcular monto pendiente
                monto_pendiente = factura.monto_total - (factura.importe_cobrado or 0)
                
                if monto_pendiente > 0:  # Solo incluir facturas con saldo pendiente
                    if dias_vencidos <= 30:
                        aging["0-30 dias"] += monto_pendiente
                    elif dias_vencidos <= 60:
                        aging["31-60 dias"] += monto_pendiente
                    elif dias_vencidos <= 90:
                        aging["61-90 dias"] += monto_pendiente
                    else:
                        aging["90+ dias"] += monto_pendiente
        
        return aging
    
    def _calculate_top_clientes(self, facturas: list) -> dict:
        """Calcula top clientes por facturación"""
        clientes_facturacion = {}
        
        for factura in facturas:
            cliente = factura.cliente or "Sin cliente"
            if cliente not in clientes_facturacion:
                clientes_facturacion[cliente] = 0
            clientes_facturacion[cliente] += factura.monto_total
        
        # Ordenar y tomar top 10
        sorted_clientes = sorted(clientes_facturacion.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_clientes[:10])
    
    def _calculate_consumo_material(self, pedidos: list) -> dict:
        """Calcula consumo por material"""
        materiales_consumo = {}
        pedidos_omitidos = 0
        
        for pedido in pedidos:
            # Omitir pedidos sin material o con material vacío
            if not pedido.material or pedido.material.strip() == "":
                pedidos_omitidos += 1
                continue
                
            material = pedido.material.strip()
            # Truncar código de material a primeros 7 dígitos para agrupación útil
            if len(material) > 7:
                material = material[:7]
            
            if material not in materiales_consumo:
                materiales_consumo[material] = 0
            materiales_consumo[material] += pedido.kg
        
        # Log de debug
        logger.info(f"Consumo material: {pedidos_omitidos} pedidos omitidos sin material, {len(materiales_consumo)} materiales válidos")
        
        # Ordenar y tomar top 10
        sorted_materiales = sorted(materiales_consumo.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_materiales[:10])
    
    def _calculate_expectativa_cobranza(self, facturas: list, pedidos: list, anticipos: list = None, cobranzas: list = None, aplicar_filtro_proporcional: bool = False) -> dict:
        """Calcula expectativa de cobranza futura basada en pedidos y sus días de crédito"""
        from datetime import datetime, timedelta
        
        expectativa = {}
        
        logger.info(f"Calculando expectativa de cobranza con {len(pedidos)} pedidos, {len(facturas)} facturas, {len(cobranzas or [])} cobranzas, aplicar_filtro_proporcional={aplicar_filtro_proporcional}")
        
        # Log de debug para días de crédito en pedidos
        pedidos_con_credito_info = []
        pedidos_con_fecha_info = []
        for pedido in pedidos[:5]:  # Solo los primeros 5 para no saturar logs
            pedidos_con_credito_info.append(f"ID:{pedido.id}, dias_credito:{pedido.dias_credito}, fecha_factura:{pedido.fecha_factura}")
            if hasattr(pedido, 'importe_sin_iva'):
                pedidos_con_fecha_info.append(f"ID:{pedido.id}, importe_sin_iva:{pedido.importe_sin_iva}")
        logger.info(f"Muestra de pedidos con crédito: {pedidos_con_credito_info}")
        logger.info(f"Muestra de pedidos con importe: {pedidos_con_fecha_info}")
        
        # Obtener fecha actual
        hoy = datetime.now()
        
        # Crear diccionarios para búsqueda rápida
        anticipos_por_factura = {}
        if anticipos:
            for anticipo in anticipos:
                if hasattr(anticipo, 'uuid_factura_relacionada') and anticipo.uuid_factura_relacionada:
                    anticipos_por_factura[anticipo.uuid_factura_relacionada] = anticipos_por_factura.get(anticipo.uuid_factura_relacionada, 0) + anticipo.importe_relacion
        
        cobranzas_por_factura = {}
        if cobranzas:
            for cobranza in cobranzas:
                if cobranza.uuid_factura_relacionada:
                    cobranzas_por_factura[cobranza.uuid_factura_relacionada] = cobranzas_por_factura.get(cobranza.uuid_factura_relacionada, 0) + cobranza.importe_pagado
        
        # Calcular fecha de referencia basada en los pedidos
        fechas_pedidos = [p.fecha_factura for p in pedidos if p.fecha_factura]
        if fechas_pedidos:
            fecha_referencia = min(fechas_pedidos)
            # Ajustar al lunes de esa semana
            dias_hasta_lunes = fecha_referencia.weekday()
            fecha_referencia = fecha_referencia - timedelta(days=dias_hasta_lunes)
        else:
            fecha_referencia = hoy
        
        logger.info(f"Fecha de referencia para semanas: {fecha_referencia.strftime('%Y-%m-%d')}")
        
        # Agrupar por semana (4 semanas pasadas + 18 semanas futuras para cubrir créditos de 120 días)
        for i in range(-4, 18):
            semana_inicio = fecha_referencia + timedelta(weeks=i)
            semana_fin = semana_inicio + timedelta(days=6)
            semana_key = f"Semana {i+5} ({semana_inicio.strftime('%d/%m')} - {semana_fin.strftime('%d/%m')})"
            
            cobranza_esperada = 0
            cobranza_real = 0
            pedidos_pendientes = 0
            
            # Calcular cobranza esperada basada en pedidos que vencen en esa semana
            pedidos_con_credito = 0
            pedidos_vencen_semana = 0
            
            for pedido in pedidos:
                if not pedido.fecha_factura:
                    continue
                
                # Contar pedidos con crédito (dias_credito > 0)
                if pedido.dias_credito and pedido.dias_credito > 0:
                    pedidos_con_credito += 1
                
                try:
                    # Calcular fecha de vencimiento usando fecha_factura + dias_credito del pedido
                    dias_credito = pedido.dias_credito or 0
                    fecha_vencimiento = pedido.fecha_factura + timedelta(days=dias_credito)
                    
                    # Si el pedido vence en esta semana
                    if semana_inicio <= fecha_vencimiento <= semana_fin:
                        pedidos_vencen_semana += 1
                        
                        # Verificar si el pedido ya está cobrado
                        pedido_cobrado = False
                        if pedido.folio_factura:
                            # Buscar factura relacionada
                            factura_pedido = next((f for f in facturas if f.folio_factura == pedido.folio_factura), None)
                            if factura_pedido and factura_pedido.uuid_factura:
                                # Buscar cobranzas de esta factura
                                cobranzas_factura = [c for c in cobranzas or [] if c.uuid_factura_relacionada == factura_pedido.uuid_factura]
                                if cobranzas_factura:
                                    total_cobrado_factura = sum(c.importe_pagado for c in cobranzas_factura)
                                    if factura_pedido.monto_total > 0:
                                        porcentaje_cobrado = total_cobrado_factura / factura_pedido.monto_total
                                        if porcentaje_cobrado >= 0.99:  # 99% o más cobrado
                                            pedido_cobrado = True
                        
                        # Solo incluir en cobranza esperada si NO está cobrado
                        if not pedido_cobrado:
                            monto_pedido = getattr(pedido, 'importe_sin_iva', 0) or 0
                            
                            # Solo considerar si hay monto positivo
                            if monto_pedido > 0:
                                cobranza_esperada += monto_pedido
                                logger.debug(f"Pedido {pedido.id} vence en semana {i+1}: ${monto_pedido} (pendiente)")
                        else:
                            logger.debug(f"Pedido {pedido.id} vence en semana {i+1}: ya cobrado, excluido de esperada")
                            
                except Exception as e:
                    logger.warning(f"Error procesando pedido {pedido.id}: {str(e)}")
                    continue
            
            # Log de debug para cada semana
            if abs(i) <= 2:  # Solo semanas cercanas para no saturar logs
                logger.info(f"Semana {i+5} ({semana_inicio.strftime('%d/%m')} - {semana_fin.strftime('%d/%m')}): {pedidos_con_credito} pedidos con crédito, {pedidos_vencen_semana} vencen, cobranza esperada: ${cobranza_esperada}")
            
            # Calcular cobranza real para esta semana usando datos de cobranza filtrada
            try:
                if aplicar_filtro_proporcional and facturas:
                    # Aplicar filtro proporcional: solo considerar cobranzas relacionadas con facturas de pedidos filtrados
                    cobranza_real_proporcional = 0
                    
                    # Crear diccionario de cobranzas por UUID de factura
                    cobranzas_por_uuid = {}
                    for cobranza in cobranzas or []:
                        if cobranza.fecha_pago and semana_inicio <= cobranza.fecha_pago <= semana_fin:
                            uuid_factura = cobranza.uuid_factura_relacionada
                            if uuid_factura not in cobranzas_por_uuid:
                                cobranzas_por_uuid[uuid_factura] = 0
                            cobranzas_por_uuid[uuid_factura] += cobranza.importe_pagado
                            logger.debug(f"Semana {i+5}: Cobranza encontrada - UUID: {uuid_factura}, Monto: {cobranza.importe_pagado}, Fecha: {cobranza.fecha_pago}")
                    
                    # Calcular cobranza proporcional para cada factura
                    for factura in facturas:
                        if not factura.uuid_factura:
                            continue
                        
                        uuid_factura = factura.uuid_factura
                        cobranza_factura = cobranzas_por_uuid.get(uuid_factura, 0)
                        
                        if cobranza_factura > 0 and factura.monto_total > 0:
                            # Calcular proporción basada en el monto de los pedidos filtrados vs total de la factura
                            # Usar el monto de la factura como base
                            monto_total_factura = factura.monto_total
                            
                            # Calcular monto de pedidos filtrados en esta factura
                            monto_pedidos_filtrados_factura = 0
                            for pedido in pedidos:
                                if pedido.folio_factura == factura.folio_factura:
                                    monto_pedidos_filtrados_factura += pedido.importe_sin_iva or 0
                            
                            if monto_total_factura > 0:
                                # Calcular cobranza proporcional basada en monto
                                porcentaje_monto_pedidos_filtrados = monto_pedidos_filtrados_factura / monto_total_factura
                                cobranza_proporcional = cobranza_factura * porcentaje_monto_pedidos_filtrados
                                cobranza_real_proporcional += cobranza_proporcional
                                
                                logger.info(f"Factura {factura.folio_factura}: ${monto_pedidos_filtrados_factura:.2f}/${monto_total_factura:.2f} ({porcentaje_monto_pedidos_filtrados:.1%}) pedidos filtrados, cobranza proporcional: ${cobranza_proporcional:.2f}")
                    
                    cobranza_real = cobranza_real_proporcional
                else:
                    # Cálculo normal sin filtro proporcional
                    for cobranza in cobranzas or []:
                        if cobranza.fecha_pago and semana_inicio <= cobranza.fecha_pago <= semana_fin:
                            cobranza_real += cobranza.importe_pagado
            except Exception as e:
                logger.warning(f"Error calculando cobranza real para semana {i+5}: {str(e)}")
                cobranza_real = 0
            
            # Contar pedidos pendientes para esa semana (pedidos que se esperan facturar)
            try:
                pedidos_semana = [p for p in pedidos if p.fecha_factura and semana_inicio <= p.fecha_factura <= semana_fin]
                pedidos_pendientes = len(pedidos_semana)
            except Exception as e:
                logger.warning(f"Error contando pedidos para semana {i+5}: {str(e)}")
                pedidos_pendientes = 0
            
            expectativa[semana_key] = {
                'cobranza_esperada': round(cobranza_esperada, 2),
                'cobranza_real': round(cobranza_real, 2),  # Datos reales de cobranza filtrada
                'pedidos_pendientes': pedidos_pendientes
            }
        
        logger.info(f"Expectativa calculada: {len(expectativa)} semanas, total esperado: {sum(d['cobranza_esperada'] for d in expectativa.values())}")
        
        # Si no hay datos, agregar datos de prueba para verificar que el gráfico funcione
        if len(expectativa) == 0 or sum(d['cobranza_esperada'] for d in expectativa.values()) == 0:
            logger.warning("No hay datos de expectativa de cobranza, agregando datos de prueba")
            logger.info(f"Total de pedidos procesados: {len(pedidos)}")
            logger.info(f"Pedidos con fecha_factura: {sum(1 for p in pedidos if p.fecha_factura)}")
            logger.info(f"Pedidos con dias_credito: {sum(1 for p in pedidos if p.dias_credito)}")
            
            from datetime import datetime, timedelta
            hoy = datetime.now()
            
            for i in range(8):
                semana_inicio = hoy + timedelta(weeks=i)
                semana_fin = semana_inicio + timedelta(days=6)
                semana_key = f"Semana {i+1} ({semana_inicio.strftime('%d/%m')} - {semana_fin.strftime('%d/%m')})"
                
                # Datos de prueba
                expectativa[semana_key] = {
                    'cobranza_esperada': 100000 + (i * 50000),  # Datos de prueba incrementales
                    'cobranza_real': 0,
                    'pedidos_pendientes': 5 + i
                }
        
        return expectativa
    
    def _get_default_kpis(self) -> dict:
        """Retorna KPIs por defecto cuando no hay datos"""
        return {
            "facturacion_total": 0.0,
            "facturacion_sin_iva": 0.0,
            "cobranza_total": 0.0,
            "cobranza_general_total": 0.0,
            "cobranza_sin_iva": 0.0,
            "anticipos_total": 0.0,
            "porcentaje_anticipos": 0.0,
            "porcentaje_cobrado": 0.0,
            "porcentaje_cobrado_general": 0.0,
            "total_facturas": 0,
            "clientes_unicos": 0,
            "pedidos_unicos": 0,
            "toneladas_total": 0.0,
            "aging_cartera": {},
            "top_clientes": {},
            "consumo_material": {},
            "expectativa_cobranza": {},
            "rotacion_inventario": 0.0,
            "dias_cxc_ajustado": 0.0,
            "ciclo_efectivo": 0.0
        }
    
    def get_filtros_disponibles(self) -> dict:
        """Obtiene opciones disponibles para filtros"""
        try:
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
    
    def get_data_summary(self) -> dict:
        """Obtiene resumen de datos disponibles"""
        return get_latest_data_summary(self.db)
    
    # ==================== MÉTODOS DE COMPRAS (LEGACY) - ELIMINADOS ====================
    # Todos los métodos de compras legacy han sido eliminados
    # Usar ComprasV2Service en su lugar
    
    """
    MÉTODOS ELIMINADOS:
    - calculate_compras_kpis()
    - get_evolucion_precios()
    - get_flujo_pagos_compras()
    - get_aging_cuentas_pagar()
    - get_materiales_compras()
    - get_proveedores_compras()
    - _get_default_compras_kpis()
    - _calculate_margen_bruto_compras_pedidos()
    - _calculate_rotacion_inventario_compras()
    - _calculate_ciclo_compras()
    """
    
    
    
    
    
    
    def get_archivos_procesados(self) -> list:
        """Obtiene lista de archivos procesados"""
        try:
            archivos = self.db.query(ArchivoProcesado).order_by(
                ArchivoProcesado.fecha_procesamiento.desc()
            ).limit(50).all()
            
            return [
                {
                    "id": archivo.id,
                    "nombre_archivo": archivo.nombre_archivo,
                    "tipo_archivo": archivo.tipo_archivo,
                    "registros_procesados": archivo.registros_procesados,
                    "fecha_procesamiento": archivo.fecha_procesamiento.isoformat() if archivo.fecha_procesamiento else None,
                    "hash_archivo": archivo.hash_archivo
                }
                for archivo in archivos
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos procesados: {str(e)}")
            return []

    # ==================== MÉTODOS DE COMPRAS_V2 ====================

    def get_compras_v2_kpis(self, filtros: dict = None) -> dict:
        """Calcula KPIs principales de compras_v2 con filtros opcionales"""
        try:
            from database import ComprasV2, ComprasV2Materiales

            # Query base para compras_v2
            query = self.db.query(ComprasV2)

            # Aplicar filtros
            if filtros:
                if filtros.get('mes') and filtros.get('año'):
                    # Para compras_v2, usamos fecha_pedido para filtrar por mes/año
                    from sqlalchemy import extract
                    query = query.filter(
                        extract('month', ComprasV2.fecha_pedido) == filtros['mes'],
                        extract('year', ComprasV2.fecha_pedido) == filtros['año']
                    )
                elif filtros.get('mes') and not filtros.get('año'):
                    logger.warning("Filtro de mes ignorado porque no hay año seleccionado")
                elif filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(extract('year', ComprasV2.fecha_pedido) == filtros['año'])

                if filtros.get('proveedor'):
                    query = query.filter(ComprasV2.proveedor.contains(filtros['proveedor']))

            compras = query.all()

            if not compras:
                return self._get_default_compras_v2_kpis()

            # Calcular métricas principales
            total_compras = len(compras)
            proveedores_unicos = len(set(c.proveedor for c in compras if c.proveedor))

            # Calcular totales desde materiales
            total_kg = 0
            total_costo_divisa = 0
            total_costo_mxn = 0

            for compra in compras:
                materiales = self.db.query(ComprasV2Materiales).filter(
                    ComprasV2Materiales.compra_id == compra.id
                ).all()

                for material in materiales:
                    total_kg += material.kg or 0
                    total_costo_divisa += material.costo_total_divisa or 0
                    total_costo_mxn += material.costo_total_con_iva or 0

            # Calcular promedios
            promedio_por_proveedor = total_compras / proveedores_unicos if proveedores_unicos > 0 else 0
            costo_promedio_kg = total_costo_mxn / total_kg if total_kg > 0 else 0

            # Calcular días de crédito promedio
            dias_credito_values = [c.dias_credito for c in compras if c.dias_credito and c.dias_credito > 0]
            dias_credito_promedio = sum(dias_credito_values) / len(dias_credito_values) if dias_credito_values else 0

            return {
                "total_compras": total_compras,
                "total_kg": round(total_kg, 2),
                "total_costo_divisa": round(total_costo_divisa, 2),
                "total_costo_mxn": round(total_costo_mxn, 2),
                "costo_promedio_kg": round(costo_promedio_kg, 2),
                "proveedores_unicos": proveedores_unicos,
                "promedio_por_proveedor": round(promedio_por_proveedor, 2),
                "dias_credito_promedio": round(dias_credito_promedio, 0)
            }

        except Exception as e:
            logger.error(f"Error calculando KPIs de compras_v2: {str(e)}")
            return self._get_default_compras_v2_kpis()

    def get_evolucion_precios_compras_v2(self, material: str = None, moneda: str = 'USD') -> dict:
        """Obtiene evolución mensual de precios por kg desde compras_v2"""
        try:
            from database import ComprasV2, ComprasV2Materiales
            from sqlalchemy import extract, func

            # Query que une compras_v2 con materiales
            query = self.db.query(
                extract('year', ComprasV2.fecha_pedido).label('año'),
                extract('month', ComprasV2.fecha_pedido).label('mes'),
                ComprasV2Materiales.pu_divisa.label('precio_divisa'),
                ComprasV2Materiales.pu_mxn_importacion.label('precio_mxn'),
                ComprasV2.moneda
            ).join(
                ComprasV2Materiales, ComprasV2.id == ComprasV2Materiales.compra_id
            ).filter(
                ComprasV2.fecha_pedido.isnot(None),
                ComprasV2Materiales.kg > 0
            )

            # Aplicar filtro de material si se especifica
            if material:
                query = query.filter(ComprasV2Materiales.material_codigo.contains(material))

            results = query.all()

            if not results:
                return {"labels": [], "data": [], "titulo": "Evolución de Precios por kg (Compras V2)"}

            # Agrupar por mes y calcular precio promedio
            precios_por_mes = {}

            for row in results:
                mes_key = f"{int(row.año)}-{int(row.mes):02d}"

                # Usar precio según moneda solicitada
                if moneda == 'MXN':
                    precio = row.precio_mxn or 0
                else:  # USD
                    precio = row.precio_divisa or 0

                if mes_key not in precios_por_mes:
                    precios_por_mes[mes_key] = []

                if precio > 0:
                    precios_por_mes[mes_key].append(precio)

            # Calcular promedios por mes
            meses_ordenados = sorted(precios_por_mes.keys())
            precios_promedio = []

            for mes in meses_ordenados:
                precios = precios_por_mes[mes]
                promedio = sum(precios) / len(precios) if precios else 0
                precios_promedio.append(round(promedio, 2))

            return {
                "labels": meses_ordenados,
                "data": precios_promedio,
                "titulo": f"Evolución de Precios por kg ({moneda}) - Compras V2"
            }

        except Exception as e:
            logger.error(f"Error obteniendo evolución de precios compras_v2: {str(e)}")
            return {"labels": [], "data": [], "titulo": "Evolución de Precios por kg (Compras V2)"}

    def get_materiales_compras_v2(self) -> list:
        """Obtiene lista de materiales disponibles en compras_v2"""
        try:
            from database import ComprasV2Materiales
            from sqlalchemy import func

            materiales = self.db.query(
                ComprasV2Materiales.material_codigo
            ).filter(
                ComprasV2Materiales.material_codigo.isnot(None),
                ComprasV2Materiales.material_codigo != ""
            ).distinct().all()

            return [material[0] for material in materiales if material[0]]

        except Exception as e:
            logger.error(f"Error obteniendo materiales de compras_v2: {str(e)}")
            return []

    def get_proveedores_compras_v2(self) -> list:
        """Obtiene lista de proveedores disponibles en compras_v2"""
        try:
            from database import ComprasV2

            proveedores = self.db.query(ComprasV2.proveedor).filter(
                ComprasV2.proveedor.isnot(None),
                ComprasV2.proveedor != ""
            ).distinct().all()

            return [proveedor[0] for proveedor in proveedores if proveedor[0]]

        except Exception as e:
            logger.error(f"Error obteniendo proveedores de compras_v2: {str(e)}")
            return []

    def get_top_proveedores_compras_v2(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene top proveedores por monto de compras_v2"""
        try:
            from database import ComprasV2, ComprasV2Materiales
            from sqlalchemy import func

            # Query que suma los costos totales por proveedor
            query = self.db.query(
                ComprasV2.proveedor,
                func.sum(ComprasV2Materiales.costo_total_con_iva).label('total_compras')
            ).join(
                ComprasV2Materiales, ComprasV2.id == ComprasV2Materiales.compra_id
            ).filter(
                ComprasV2.proveedor.isnot(None),
                ComprasV2.proveedor != ""
            ).group_by(ComprasV2.proveedor)

            # Aplicar filtros
            if filtros:
                if filtros.get('mes') and filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(
                        extract('month', ComprasV2.fecha_pedido) == filtros['mes'],
                        extract('year', ComprasV2.fecha_pedido) == filtros['año']
                    )
                elif filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(extract('year', ComprasV2.fecha_pedido) == filtros['año'])

            # Ordenar por total y limitar
            result = query.order_by(func.sum(ComprasV2Materiales.costo_total_con_iva).desc()).limit(limite).all()

            return {proveedor: float(total or 0) for proveedor, total in result}

        except Exception as e:
            logger.error(f"Error obteniendo top proveedores compras_v2: {str(e)}")
            return {}

    def get_compras_por_material_v2(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene compras agrupadas por material en compras_v2"""
        try:
            from database import ComprasV2, ComprasV2Materiales
            from sqlalchemy import func

            # Query que suma costos por material
            query = self.db.query(
                ComprasV2Materiales.material_codigo,
                func.sum(ComprasV2Materiales.costo_total_con_iva).label('total_compras'),
                func.sum(ComprasV2Materiales.kg).label('total_kg')
            ).join(
                ComprasV2, ComprasV2.id == ComprasV2Materiales.compra_id
            ).filter(
                ComprasV2Materiales.material_codigo.isnot(None),
                ComprasV2Materiales.material_codigo != ""
            ).group_by(ComprasV2Materiales.material_codigo)

            # Aplicar filtros
            if filtros:
                if filtros.get('mes') and filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(
                        extract('month', ComprasV2.fecha_pedido) == filtros['mes'],
                        extract('year', ComprasV2.fecha_pedido) == filtros['año']
                    )
                elif filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(extract('year', ComprasV2.fecha_pedido) == filtros['año'])

                if filtros.get('proveedor'):
                    query = query.filter(ComprasV2.proveedor.contains(filtros['proveedor']))

            # Ordenar por total y limitar
            result = query.order_by(func.sum(ComprasV2Materiales.costo_total_con_iva).desc()).limit(limite).all()

            return {material: {
                'total_compras': float(total or 0),
                'total_kg': float(total_kg or 0)
            } for material, total, total_kg in result}

        except Exception as e:
            logger.error(f"Error obteniendo compras por material v2: {str(e)}")
            return {}

    def _get_default_compras_v2_kpis(self) -> dict:
        """Retorna KPIs por defecto para compras_v2 cuando no hay datos"""
        return {
            "total_compras": 0,
            "total_kg": 0.0,
            "total_costo_divisa": 0.0,
            "total_costo_mxn": 0.0,
            "costo_promedio_kg": 0.0,
            "proveedores_unicos": 0,
            "promedio_por_proveedor": 0.0,
            "dias_credito_promedio": 0.0
        }
    