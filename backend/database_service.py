"""
Servicio de base de datos para Immermex Dashboard
Maneja todas las operaciones CRUD y cálculos de KPIs
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from database import (
    Facturacion, Cobranza, CFDIRelacionado, Inventario, Pedido, 
    ArchivoProcesado, KPI, get_latest_data_summary
)
from datetime import datetime, timedelta
import logging
import hashlib
import numpy as np

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
    
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
            
            # Guardar cada tipo de datos
            facturas_count = self._save_facturas(processed_data_dict.get("facturacion_clean", []), archivo.id)
            cobranzas_count = self._save_cobranzas(processed_data_dict.get("cobranza_clean", []), archivo.id)
            anticipos_count = self._save_anticipos(processed_data_dict.get("cfdi_clean", []), archivo.id)
            pedidos_count = self._save_pedidos(processed_data_dict.get("pedidos_clean", []), archivo.id)
            
            # Actualizar registro de archivo
            total_registros = facturas_count + cobranzas_count + anticipos_count + pedidos_count
            archivo.registros_procesados = total_registros
            archivo.estado = "procesado"
            self.db.commit()
            
            logger.info(f"Datos guardados exitosamente: {total_registros} registros")
            return {
                "success": True,
                "archivo_id": archivo.id,
                "registros_procesados": total_registros,
                "desglose": {
                    "facturas": facturas_count,
                    "cobranzas": cobranzas_count,
                    "anticipos": anticipos_count,
                    "pedidos": pedidos_count
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error guardando datos: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_archivo_record(self, archivo_info: dict) -> ArchivoProcesado:
        """Crea o actualiza el registro de archivo"""
        # Calcular hash del archivo para evitar duplicados
        file_hash = hashlib.md5(f"{archivo_info['nombre']}_{archivo_info['tamaño']}".encode()).hexdigest()
        
        # Buscar si ya existe
        archivo = self.db.query(ArchivoProcesado).filter(
            ArchivoProcesado.hash_archivo == file_hash
        ).first()
        
        if archivo:
            # Actualizar archivo existente
            archivo.nombre_archivo = archivo_info['nombre']
            archivo.tamaño_archivo = archivo_info['tamaño']
            archivo.estado = "en_proceso"
            archivo.updated_at = datetime.utcnow()
        else:
            # Crear nuevo archivo
            archivo = ArchivoProcesado(
                nombre_archivo=archivo_info['nombre'],
                hash_archivo=file_hash,
                tamaño_archivo=archivo_info['tamaño'],
                algoritmo_usado=archivo_info.get('algoritmo', 'advanced_cleaning'),
                estado="en_proceso"
            )
            self.db.add(archivo)
        
        self.db.commit()
        self.db.refresh(archivo)
        return archivo
    
    def _save_facturas(self, facturas_data: list, archivo_id: int) -> int:
        """Guarda datos de facturación"""
        count = 0
        for factura_data in facturas_data:
            try:
                # Convertir fecha si es necesario y válida
                fecha_factura = factura_data.get('fecha_factura')
                if fecha_factura is not None:
                    # Verificar si es NaN
                    if isinstance(fecha_factura, (int, float)) and np.isnan(fecha_factura):
                        fecha_factura = None
                    elif isinstance(fecha_factura, str) and fecha_factura.strip():
                        try:
                            # Solo convertir si parece una fecha válida (formato YYYY-MM-DD)
                            if len(fecha_factura) == 10 and fecha_factura.count('-') == 2:
                                fecha_factura = datetime.strptime(fecha_factura, '%Y-%m-%d')
                            else:
                                fecha_factura = None
                        except ValueError:
                            fecha_factura = None
                    else:
                        fecha_factura = None
                else:
                    fecha_factura = None
                
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
                
                def safe_int(value, default=30):
                    try:
                        if value is None or value == '' or str(value).strip() == '':
                            return default
                        return int(float(str(value).replace(',', '').strip()))
                    except (ValueError, TypeError):
                        return default
                
                factura = Facturacion(
                    serie_factura=str(factura_data.get('serie_factura', '')).strip(),
                    folio_factura=str(factura_data.get('folio_factura', '')).strip(),
                    fecha_factura=fecha_factura,
                    cliente=str(factura_data.get('cliente', '')).strip(),
                    agente=str(factura_data.get('agente', '')).strip(),
                    monto_neto=safe_float(factura_data.get('monto_neto', 0)),
                    monto_total=safe_float(factura_data.get('monto_total', 0)),
                    saldo_pendiente=safe_float(factura_data.get('saldo_pendiente', 0)),
                    dias_credito=safe_int(factura_data.get('dias_credito', 30)),
                    uuid_factura=str(factura_data.get('uuid_factura', '')).strip(),
                    archivo_id=archivo_id,
                    mes=fecha_factura.month if fecha_factura else None,
                    año=fecha_factura.year if fecha_factura else None
                )
                self.db.add(factura)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando factura: {str(e)}")
                continue
        
        self.db.commit()
        return count
    
    def _save_cobranzas(self, cobranzas_data: list, archivo_id: int) -> int:
        """Guarda datos de cobranza"""
        count = 0
        for cobranza_data in cobranzas_data:
            try:
                # Convertir fecha si es necesario y válida
                fecha_pago = cobranza_data.get('fecha_pago')
                if fecha_pago is not None:
                    # Verificar si es NaN
                    if isinstance(fecha_pago, (int, float)) and np.isnan(fecha_pago):
                        fecha_pago = None
                    elif isinstance(fecha_pago, str) and fecha_pago.strip():
                        try:
                            # Solo convertir si parece una fecha válida (formato YYYY-MM-DD)
                            if len(fecha_pago) == 10 and fecha_pago.count('-') == 2:
                                fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d')
                            else:
                                fecha_pago = None
                        except ValueError:
                            fecha_pago = None
                    else:
                        fecha_pago = None
                else:
                    fecha_pago = None
                
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
                
                def safe_int(value, default=1):
                    try:
                        if value is None or value == '' or str(value).strip() == '':
                            return default
                        return int(float(str(value).replace(',', '').strip()))
                    except (ValueError, TypeError):
                        return default
                
                cobranza = Cobranza(
                    fecha_pago=fecha_pago,
                    serie_pago=str(cobranza_data.get('serie_pago', '')).strip(),
                    folio_pago=str(cobranza_data.get('folio_pago', '')).strip(),
                    cliente=str(cobranza_data.get('cliente', '')).strip(),
                    moneda=str(cobranza_data.get('moneda', 'MXN')).strip(),
                    tipo_cambio=safe_float(cobranza_data.get('tipo_cambio', 1.0)),
                    forma_pago=str(cobranza_data.get('forma_pago', '')).strip(),
                    parcialidad=safe_int(cobranza_data.get('numero_parcialidades', cobranza_data.get('parcialidad', 1))),
                    importe_pagado=safe_float(cobranza_data.get('importe_pagado', 0)),
                    uuid_factura_relacionada=str(cobranza_data.get('uuid_relacionado', cobranza_data.get('uuid_factura_relacionada', ''))).strip(),
                    archivo_id=archivo_id
                )
                self.db.add(cobranza)
                count += 1
            except Exception as e:
                logger.warning(f"Error guardando cobranza: {str(e)}")
                continue
        
        self.db.commit()
        return count
    
    def _save_anticipos(self, anticipos_data: list, archivo_id: int) -> int:
        """Guarda datos de anticipos (CFDI relacionados)"""
        count = 0
        for anticipo_data in anticipos_data:
            try:
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
                
                anticipo = CFDIRelacionado(
                    xml=str(anticipo_data.get('xml', '')).strip(),
                    cliente_receptor=str(anticipo_data.get('cliente_receptor', '')).strip(),
                    tipo_relacion=str(anticipo_data.get('tipo_relacion', '')).strip(),
                    importe_relacion=safe_float(anticipo_data.get('importe_relacion', 0)),
                    uuid_factura_relacionada=str(anticipo_data.get('uuid_factura_relacionada', '')).strip(),
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
        """Guarda datos de pedidos"""
        count = 0
        for pedido_data in pedidos_data:
            try:
                # Convertir fechas si es necesario y válidas
                fecha_factura = pedido_data.get('fecha_factura')
                if isinstance(fecha_factura, str) and fecha_factura and fecha_factura.strip():
                    try:
                        if len(fecha_factura) == 10 and fecha_factura.count('-') == 2:
                            fecha_factura = datetime.strptime(fecha_factura, '%Y-%m-%d')
                        else:
                            fecha_factura = None
                    except ValueError:
                        fecha_factura = None
                
                fecha_pago = pedido_data.get('fecha_pago')
                if isinstance(fecha_pago, str) and fecha_pago and fecha_pago.strip():
                    try:
                        if len(fecha_pago) == 10 and fecha_pago.count('-') == 2:
                            fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d')
                        else:
                            fecha_pago = None
                    except ValueError:
                        fecha_pago = None
                
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
                
                def safe_int(value, default=30):
                    try:
                        if value is None or value == '' or str(value).strip() == '':
                            return default
                        return int(float(str(value).replace(',', '').strip()))
                    except (ValueError, TypeError):
                        return default
                
                pedido = Pedido(
                    folio_factura=str(pedido_data.get('folio_factura', '')).strip(),
                    pedido=str(pedido_data.get('pedido', '')).strip(),
                    kg=safe_float(pedido_data.get('kg', 0)),
                    precio_unitario=safe_float(pedido_data.get('precio_unitario', 0)),
                    importe_sin_iva=safe_float(pedido_data.get('importe_sin_iva', 0)),
                    material=str(pedido_data.get('material', '')).strip(),
                    dias_credito=safe_int(pedido_data.get('dias_credito', 30)),
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
        return count
    
    def _clear_existing_data(self):
        """Limpia todos los datos existentes"""
        try:
            self.db.query(Pedido).delete()
            self.db.query(CFDIRelacionado).delete()
            self.db.query(Cobranza).delete()
            self.db.query(Facturacion).delete()
            self.db.query(KPI).delete()
            self.db.commit()
            logger.info("Datos existentes limpiados")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error limpiando datos: {str(e)}")
    
    def calculate_kpis(self, filtros: dict = None) -> dict:
        """
        Calcula KPIs basados en los datos de la base de datos
        """
        try:
            # Aplicar filtros base
            query_facturas = self.db.query(Facturacion)
            query_cobranzas = self.db.query(Cobranza)
            query_anticipos = self.db.query(CFDIRelacionado)
            query_pedidos = self.db.query(Pedido)
            
            if filtros:
                if filtros.get('mes'):
                    query_facturas = query_facturas.filter(Facturacion.mes == filtros['mes'])
                    query_pedidos = query_pedidos.filter(func.extract('month', Pedido.fecha_factura) == filtros['mes'])
                
                if filtros.get('año'):
                    query_facturas = query_facturas.filter(Facturacion.año == filtros['año'])
                    query_pedidos = query_pedidos.filter(func.extract('year', Pedido.fecha_factura) == filtros['año'])
                
                if filtros.get('pedidos'):
                    pedidos_list = filtros['pedidos']
                    query_facturas = query_facturas.filter(Facturacion.folio_factura.in_(pedidos_list))
                    query_pedidos = query_pedidos.filter(Pedido.pedido.in_(pedidos_list))
            
            # Obtener datos
            facturas = query_facturas.all()
            cobranzas = query_cobranzas.all()
            anticipos = query_anticipos.all()
            pedidos = query_pedidos.all()
            
            if not facturas:
                return self._get_default_kpis()
            
            # Calcular KPIs
            facturacion_total = sum(f.monto_total for f in facturas)
            cobranza_total = sum(c.importe_pagado for c in cobranzas)
            anticipos_total = sum(a.importe_relacion for a in anticipos)
            
            porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
            
            # Aging de cartera
            aging_cartera = self._calculate_aging_cartera(facturas)
            
            # Top clientes
            top_clientes = self._calculate_top_clientes(facturas)
            
            # Consumo por material
            consumo_material = self._calculate_consumo_material(pedidos)
            
            # Métricas adicionales
            total_facturas = len(facturas)
            clientes_unicos = len(set(f.cliente for f in facturas if f.cliente))
            
            # Pedidos únicos y toneladas
            pedidos_unicos = len(set(p.pedido for p in pedidos if p.pedido))
            toneladas_total = sum(p.kg for p in pedidos)
            
            return {
                "facturacion_total": round(facturacion_total, 2),
                "facturacion_sin_iva": round(sum(f.monto_neto for f in facturas), 2),
                "cobranza_total": round(cobranza_total, 2),
                "cobranza_sin_iva": round(sum(f.monto_neto for f in facturas if f.importe_cobrado > 0), 2),
                "anticipos_total": round(anticipos_total, 2),
                "porcentaje_cobrado": round(porcentaje_cobrado, 2),
                "total_facturas": total_facturas,
                "clientes_unicos": clientes_unicos,
                "pedidos_unicos": pedidos_unicos,
                "toneladas_total": round(toneladas_total, 2),
                "aging_cartera": aging_cartera,
                "top_clientes": top_clientes,
                "consumo_material": consumo_material,
                "rotacion_inventario": 0,  # Se calcularía con datos de inventario
                "dias_cxc_ajustado": 0,    # Se calcularía con datos de inventario
                "ciclo_efectivo": 0        # Se calcularía con datos de inventario
            }
            
        except Exception as e:
            logger.error(f"Error calculando KPIs: {str(e)}")
            return self._get_default_kpis()
    
    def _calculate_aging_cartera(self, facturas: list) -> dict:
        """Calcula aging de cartera"""
        aging = {"0-30 días": 0, "31-60 días": 0, "61-90 días": 0, "90+ días": 0}
        
        for factura in facturas:
            if factura.fecha_factura and factura.importe_cobrado < factura.monto_total:
                dias_credito = factura.dias_credito or 30
                fecha_vencimiento = factura.fecha_factura + timedelta(days=dias_credito)
                dias_vencidos = (datetime.now() - fecha_vencimiento).days
                
                if dias_vencidos <= 30:
                    aging["0-30 días"] += 1
                elif dias_vencidos <= 60:
                    aging["31-60 días"] += 1
                elif dias_vencidos <= 90:
                    aging["61-90 días"] += 1
                else:
                    aging["90+ días"] += 1
        
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
        
        for pedido in pedidos:
            material = pedido.material or "Sin material"
            if material not in materiales_consumo:
                materiales_consumo[material] = 0
            materiales_consumo[material] += pedido.kg
        
        # Ordenar y tomar top 10
        sorted_materiales = sorted(materiales_consumo.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_materiales[:10])
    
    def _get_default_kpis(self) -> dict:
        """Retorna KPIs por defecto cuando no hay datos"""
        return {
            "facturacion_total": 0.0,
            "facturacion_sin_iva": 0.0,
            "cobranza_total": 0.0,
            "cobranza_sin_iva": 0.0,
            "anticipos_total": 0.0,
            "porcentaje_cobrado": 0.0,
            "total_facturas": 0,
            "clientes_unicos": 0,
            "pedidos_unicos": 0,
            "toneladas_total": 0.0,
            "aging_cartera": {},
            "top_clientes": {},
            "consumo_material": {},
            "rotacion_inventario": 0.0,
            "dias_cxc_ajustado": 0.0,
            "ciclo_efectivo": 0.0
        }
    
    def get_filtros_disponibles(self) -> dict:
        """Obtiene opciones disponibles para filtros"""
        try:
            # Pedidos disponibles
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
