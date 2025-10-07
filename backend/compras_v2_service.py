"""
Servicio de guardado para compras_v2 y compras_v2_materiales
Integrado con el nuevo procesador robusto
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class ComprasV2Service:
    """
    Servicio para guardar datos en compras_v2 y compras_v2_materiales
    """
    
    def __init__(self):
        self.conn = None
    
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
    
    def get_connection(self):
        """Obtiene conexión a Supabase"""
        if self.conn and not self.conn.closed:
            return self.conn
        
        try:
            config = self.load_production_config()
            if not config:
                return None
            
            database_url = config.get("DATABASE_URL")
            
            if not database_url:
                logger.error("DATABASE_URL no encontrada en production.env")
                return None
            
            self.conn = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor,
                sslmode='require',
                connect_timeout=30
            )
            
            return self.conn
            
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {str(e)}")
            return None
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def safe_decimal(self, value, default=0.0):
        """Convierte un valor a Decimal de forma segura"""
        if value is None:
            return Decimal(str(default))
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except:
            return Decimal(str(default))
    
    def safe_int(self, value, default=0):
        """Convierte un valor a int de forma segura"""
        if value is None:
            return default
        try:
            return int(value)
        except:
            return default
    
    def safe_string(self, value, default=''):
        """Convierte un valor a string de forma segura"""
        if value is None:
            return default
        return str(value).strip()
    
    def safe_percentage(self, value, max_value=9.9999):
        """Convierte un valor a decimal de forma segura para campos NUMERIC(5,4)"""
        if value is None:
            return Decimal('0.0000')
        
        try:
            decimal_value = Decimal(str(value))
            # Limitar a la precisión máxima permitida por NUMERIC(5,4)
            if decimal_value > max_value:
                logger.warning(f"Valor de porcentaje {decimal_value} excede el máximo permitido ({max_value}), limitando a {max_value}")
                return Decimal(str(max_value))
            elif decimal_value < -max_value:
                logger.warning(f"Valor de porcentaje {decimal_value} excede el mínimo permitido (-{max_value}), limitando a -{max_value}")
                return Decimal(str(-max_value))
            return decimal_value
        except (ValueError, TypeError):
            logger.warning(f"Error convirtiendo porcentaje '{value}' a decimal, usando 0.0000")
            return Decimal('0.0000')
    
    def _is_valid_update_value(self, value):
        """Determina si un valor es válido para actualización"""
        if value is None:
            return False
        
        if isinstance(value, str):
            # String vacío o valores que indican "no hay dato"
            if value.strip() == '' or value.strip().lower() in ['nan', 'none', 'null', 'n/a', '-']:
                return False
            return True
        
        # Para números, 0 puede ser un valor válido
        if isinstance(value, (int, float)):
            return True
        
        # Para fechas, cualquier fecha válida es aceptable
        if hasattr(value, 'year'):  # datetime.date o datetime.datetime
            return True
        
        # Para otros tipos, verificar si no es None
        return value is not None
    
    
    def save_compras_v2(self, compras: List[Dict[str, Any]], archivo_id: int) -> int:
        """Guarda compras en la tabla compras_v2 con actualización parcial"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            compras_guardadas = 0
            
            for compra in compras:
                # Usar transacción individual para cada compra
                try:
                    cursor = conn.cursor()
                    # Verificar si ya existe
                    cursor.execute("SELECT id FROM compras_v2 WHERE imi = %s", (compra['imi'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        logger.info(f"Compra con IMI {compra['imi']} ya existe, verificando actualización parcial...")
                        
                        # Construir query de actualización dinámica solo con campos no vacíos
                        update_fields = []
                        update_values = []
                        
                        # Lista de campos que pueden ser actualizados
                        updatable_fields = {
                            'proveedor': compra.get('proveedor'),
                            'fecha_pedido': compra.get('fecha_pedido'),
                            'puerto_origen': compra.get('puerto_origen'),
                            'fecha_salida_estimada': compra.get('fecha_salida_estimada'),
                            'fecha_arribo_estimada': compra.get('fecha_arribo_estimada'),
                            'fecha_planta_estimada': compra.get('fecha_planta_estimada'),
                            'moneda': compra.get('moneda'),
                            'dias_credito': compra.get('dias_credito'),
                            'anticipo_pct': compra.get('anticipo_pct'),
                            'anticipo_monto': compra.get('anticipo_monto'),
                            'fecha_anticipo': compra.get('fecha_anticipo'),
                            'fecha_pago_factura': compra.get('fecha_pago_factura'),
                            'tipo_cambio_estimado': compra.get('tipo_cambio_estimado'),
                            'tipo_cambio_real': compra.get('tipo_cambio_real'),
                            'gastos_importacion_divisa': compra.get('gastos_importacion_divisa'),
                            'gastos_importacion_mxn': compra.get('gastos_importacion_mxn'),
                            'porcentaje_gastos_importacion': compra.get('porcentaje_gastos_importacion'),
                            'iva_monto_mxn': compra.get('iva_monto_mxn'),
                            'total_con_iva_mxn': compra.get('total_con_iva_mxn')
                        }
                        
                        # Solo agregar campos que tienen valores no vacíos
                        for field, value in updatable_fields.items():
                            # Verificar si el valor es válido para actualización
                            if self._is_valid_update_value(value):
                                if field in ['anticipo_pct', 'porcentaje_gastos_importacion']:
                                    update_fields.append(f"{field} = %s")
                                    update_values.append(self.safe_percentage(value))
                                elif field in ['anticipo_monto', 'tipo_cambio_estimado', 'tipo_cambio_real', 
                                             'gastos_importacion_divisa', 'gastos_importacion_mxn', 
                                             'iva_monto_mxn', 'total_con_iva_mxn']:
                                    update_fields.append(f"{field} = %s")
                                    update_values.append(self.safe_decimal(value))
                        else:
                                    update_fields.append(f"{field} = %s")
                                    update_values.append(value)
                        
                        # Siempre actualizar el timestamp
                        update_fields.append("updated_at = %s")
                        update_values.append(datetime.utcnow())
                        
                        # Agregar el IMI para la condición WHERE
                        update_values.append(compra['imi'])
                        
                        if update_fields:
                            # Construir query dinámico
                            update_query = f"""
                            UPDATE compras_v2 SET
                                    {', '.join(update_fields)}
                            WHERE imi = %s
                            """
                            
                            cursor.execute(update_query, update_values)
                            logger.info(f"Actualizando compra IMI {compra['imi']} con {len(update_fields)-1} campos")
                        else:
                            logger.info(f"No hay campos para actualizar en compra IMI {compra['imi']}")
                    else:
                        # Insertar nuevo registro
                        logger.info(f"Insertando nueva compra IMI {compra['imi']}...")
                        cursor.execute("""
                            INSERT INTO compras_v2 (
                                imi, proveedor, fecha_pedido, puerto_origen,
                                fecha_salida_estimada, fecha_arribo_estimada, fecha_planta_estimada,
                                moneda, dias_credito, anticipo_pct, anticipo_monto,
                                fecha_anticipo, fecha_pago_factura,
                                tipo_cambio_estimado, tipo_cambio_real,
                                gastos_importacion_divisa, gastos_importacion_mxn,
                                porcentaje_gastos_importacion,
                                iva_monto_mxn, total_con_iva_mxn,
                                created_at, updated_at
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            compra['imi'],
                            compra['proveedor'],
                            compra['fecha_pedido'],
                            compra['puerto_origen'],
                            compra['fecha_salida_estimada'],
                            compra['fecha_arribo_estimada'],
                            compra['fecha_planta_estimada'],
                            compra['moneda'],
                            compra['dias_credito'],
                            self.safe_percentage(compra['anticipo_pct']),
                            self.safe_decimal(compra['anticipo_monto']),
                            compra['fecha_anticipo'],
                            compra['fecha_pago_factura'],
                            self.safe_decimal(compra['tipo_cambio_estimado']),
                            self.safe_decimal(compra['tipo_cambio_real']),
                            self.safe_decimal(compra['gastos_importacion_divisa']),
                            self.safe_decimal(compra['gastos_importacion_mxn']),
                            self.safe_percentage(compra['porcentaje_gastos_importacion']),
                            self.safe_decimal(compra['iva_monto_mxn']),
                            self.safe_decimal(compra['total_con_iva_mxn']),
                            datetime.utcnow(),
                            datetime.utcnow()
                        ))
                    
                    # Commit individual para esta compra
                    conn.commit()
                    compras_guardadas += 1
                    logger.info(f"Compra IMI {compra['imi']} guardada exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error guardando compra IMI {compra['imi']}: {str(e)}")
                    # Rollback individual para esta compra
                    conn.rollback()
                    continue
                finally:
                    # Cerrar cursor individual
                    if 'cursor' in locals():
                        cursor.close()
            
            logger.info(f"Guardadas {compras_guardadas} compras en compras_v2")
            
            cursor.close()
            return compras_guardadas
            
        except Exception as e:
            logger.error(f"Error guardando compras_v2: {str(e)}")
            conn.rollback()
            return 0
    
    def save_compras_v2_materiales(self, materiales: List[Dict[str, Any]]) -> int:
        """Guarda materiales en la tabla compras_v2_materiales"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            materiales_guardados = 0
            
            for material in materiales:
                try:
                    # Verificar si ya existe
                    cursor.execute("""
                        SELECT id FROM compras_v2_materiales 
                        WHERE compra_id = %s AND material_codigo = %s
                    """, (material['compra_id'], material['material_codigo']))
                    existing = cursor.fetchone()
                    
                    if existing:
                        logger.warning(f"Material {material['material_codigo']} para compra {material['compra_id']} ya existe, actualizando...")
                        
                        # Actualizar registro existente
                        cursor.execute("""
                            UPDATE compras_v2_materiales SET
                                kg = %s,
                                pu_divisa = %s,
                                pu_mxn = %s,
                                costo_total_divisa = %s,
                                costo_total_mxn = %s,
                                pu_mxn_importacion = %s,
                                costo_total_mxn_imporacion = %s,
                                iva = %s,
                                costo_total_con_iva = %s,
                                compra_imi = %s,
                                updated_at = %s
                            WHERE compra_id = %s AND material_codigo = %s
                        """, (
                            self.safe_decimal(material['kg']),
                            self.safe_decimal(material['pu_divisa']),
                            self.safe_decimal(material['pu_mxn']),
                            self.safe_decimal(material['costo_total_divisa']),
                            self.safe_decimal(material['costo_total_mxn']),
                            self.safe_decimal(material['pu_mxn_importacion']),
                            self.safe_decimal(material['costo_total_mxn_imporacion']),
                            self.safe_decimal(material['iva']),
                            self.safe_decimal(material['costo_total_con_iva']),
                            material['compra_imi'],
                            datetime.utcnow(),
                            material['compra_id'],
                            material['material_codigo']
                        ))
                    else:
                        # Insertar nuevo registro
                        cursor.execute("""
                            INSERT INTO compras_v2_materiales (
                                compra_id, material_codigo, kg, pu_divisa, pu_mxn,
                                costo_total_divisa, costo_total_mxn, pu_mxn_importacion,
                                costo_total_mxn_imporacion, iva, costo_total_con_iva,
                                compra_imi, created_at, updated_at
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            material['compra_id'],
                            material['material_codigo'],
                            self.safe_decimal(material['kg']),
                            self.safe_decimal(material['pu_divisa']),
                            self.safe_decimal(material['pu_mxn']),
                            self.safe_decimal(material['costo_total_divisa']),
                            self.safe_decimal(material['costo_total_mxn']),
                            self.safe_decimal(material['pu_mxn_importacion']),
                            self.safe_decimal(material['costo_total_mxn_imporacion']),
                            self.safe_decimal(material['iva']),
                            self.safe_decimal(material['costo_total_con_iva']),
                            material['compra_imi'],
                            datetime.utcnow(),
                            datetime.utcnow()
                        ))
                    
                    materiales_guardados += 1
                    
                except Exception as e:
                    logger.error(f"Error guardando material {material['material_codigo']} para compra {material['compra_id']}: {str(e)}")
                    continue
            
            conn.commit()
            logger.info(f"Guardados {materiales_guardados} materiales en compras_v2_materiales")
            
            cursor.close()
            return materiales_guardados
            
        except Exception as e:
            logger.error(f"Error guardando compras_v2_materiales: {str(e)}")
            conn.rollback()
            return 0
    
    def save_compras_data(self, processed_data: Dict[str, Any], archivo_id: int) -> Dict[str, int]:
        """Guarda datos procesados en las tablas compras_v2 y compras_v2_materiales"""
        try:
            compras = processed_data.get('compras_v2', [])
            materiales = processed_data.get('compras_v2_materiales', [])
            
            logger.info(f"Iniciando guardado de {len(compras)} compras y {len(materiales)} materiales")
            
            # Guardar compras
            compras_guardadas = self.save_compras_v2(compras, archivo_id)
            
            # Guardar materiales
            materiales_guardados = self.save_compras_v2_materiales(materiales)
            
            return {
                'compras_guardadas': compras_guardadas,
                'materiales_guardados': materiales_guardados,
                'total_procesados': len(compras) + len(materiales)
            }
            
        except Exception as e:
            logger.error(f"Error guardando datos de compras: {str(e)}")
            return {
                'compras_guardadas': 0,
                'materiales_guardados': 0,
                'total_procesados': 0
            }
    
    def get_compras_simple(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Método simple que replica exactamente el patrón de KPIs"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Usar exactamente el mismo patrón que KPIs
            query = """
                SELECT 
                    c2.id, c2.imi, c2.proveedor, c2.fecha_pedido
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.id = c2m.compra_id
                WHERE 1=1
                GROUP BY c2.id, c2.imi, c2.proveedor, c2.fecha_pedido
                ORDER BY c2.fecha_pedido DESC
                LIMIT %s
            """
            
            cursor.execute(query, [limit])
            compras_raw = cursor.fetchall()
            
            logger.info(f"Query ejecutada: {query}")
            logger.info(f"Parámetros: {[limit]}")
            logger.info(f"Resultados obtenidos: {len(compras_raw)} registros")
            
            # Log de los primeros registros para debug
            if compras_raw:
                logger.info(f"Primer registro raw: {compras_raw[0]}")
                logger.info(f"Tipo del primer registro: {type(compras_raw[0])}")
            
            # Convertir a diccionarios
            compras = []
            for i, row in enumerate(compras_raw):
                try:
                    logger.info(f"Procesando fila {i}: {row}")
                    compra = {
                        'id': int(row['id']) if row['id'] is not None else None,
                        'imi': str(row['imi']) if row['imi'] is not None else None,
                        'proveedor': str(row['proveedor']) if row['proveedor'] is not None else None,
                        'fecha_pedido': row['fecha_pedido'].isoformat() if row['fecha_pedido'] is not None else None
                    }
                    compras.append(compra)
                    logger.info(f"Fila {i} convertida exitosamente: {compra}")
                except Exception as e:
                    logger.error(f"Error convirtiendo fila {i} {row}: {str(e)}")
                    continue
            
            logger.info(f"Total compras convertidas: {len(compras)}")
            cursor.close()
            return compras
            
        except Exception as e:
            logger.error(f"Error en get_compras_simple: {str(e)}")
            return []

    def get_compras_by_filtros(self, filtros: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene compras filtradas de compras_v2"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Construir query base usando el mismo patrón que KPIs (que funciona)
            query = """
                SELECT 
                    c2.id, c2.imi, c2.proveedor, c2.fecha_pedido
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.id = c2m.compra_id
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if filtros.get('proveedor'):
                query += " AND c2.proveedor ILIKE %s"
                params.append(f"%{filtros['proveedor']}%")
            
            if filtros.get('material'):
                query += " AND EXISTS (SELECT 1 FROM compras_v2_materiales WHERE compra_id = c2.id AND material_codigo ILIKE %s)"
                params.append(f"%{filtros['material']}%")
            
            if filtros.get('mes') and filtros.get('año'):
                query += " AND EXTRACT(MONTH FROM c2.fecha_pedido) = %s AND EXTRACT(YEAR FROM c2.fecha_pedido) = %s"
                params.append(filtros['mes'])
                params.append(filtros['año'])
            elif filtros.get('año'):
                query += " AND EXTRACT(YEAR FROM c2.fecha_pedido) = %s"
                params.append(filtros['año'])
            
            if filtros.get('fecha_desde'):
                query += " AND c2.fecha_pedido >= %s"
                params.append(filtros['fecha_desde'])
            
            if filtros.get('fecha_hasta'):
                query += " AND c2.fecha_pedido <= %s"
                params.append(filtros['fecha_hasta'])
            
            if filtros.get('moneda'):
                query += " AND c2.moneda = %s"
                params.append(filtros['moneda'])
            
            # Agrupar y ordenar (necesario por el LEFT JOIN)
            query += " GROUP BY c2.id, c2.imi, c2.proveedor, c2.fecha_pedido ORDER BY c2.fecha_pedido DESC"
            
            # Aplicar límite
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            logger.info(f"Ejecutando query: {query}")
            logger.info(f"Con parámetros: {params}")
            
            cursor.execute(query, params)
            compras_raw = cursor.fetchall()
            
            logger.info(f"Resultados obtenidos: {len(compras_raw)} registros")
            
            # Convertir a diccionarios
            compras = []
            for row in compras_raw:
                compra = {
                    'id': int(row['id']) if row['id'] is not None else None,
                    'imi': str(row['imi']) if row['imi'] is not None else None,
                    'proveedor': str(row['proveedor']) if row['proveedor'] is not None else None,
                    'fecha_pedido': row['fecha_pedido'].isoformat() if row['fecha_pedido'] is not None else None
                }
                compras.append(compra)
            
            cursor.close()
            return compras
            
        except Exception as e:
            logger.error(f"Error obteniendo compras: {str(e)}")
            return []
    
    def get_materiales_by_compra(self, imi: int) -> List[Dict[str, Any]]:
        """Obtiene materiales de una compra específica"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    material_codigo, kg, pu_divisa, pu_mxn,
                    costo_total_divisa, costo_total_mxn, pu_mxn_importacion,
                    costo_total_mxn_imporacion, iva, costo_total_con_iva
                FROM compras_v2_materiales
                WHERE compra_id = %s
                ORDER BY material_codigo
            """, (imi,))
            
            materiales = cursor.fetchall()
            
            # Convertir a diccionarios
            materiales_list = []
            for row in materiales:
                material = {
                    'material_codigo': str(row['material_codigo']) if row['material_codigo'] is not None else None,
                    'kg': float(row['kg']) if row['kg'] is not None else 0.0,
                    'pu_divisa': float(row['pu_divisa']) if row['pu_divisa'] is not None else 0.0,
                    'pu_mxn': float(row['pu_mxn']) if row['pu_mxn'] is not None else 0.0,
                    'costo_total_divisa': float(row['costo_total_divisa']) if row['costo_total_divisa'] is not None else 0.0,
                    'costo_total_mxn': float(row['costo_total_mxn']) if row['costo_total_mxn'] is not None else 0.0,
                    'pu_mxn_importacion': float(row['pu_mxn_importacion']) if row['pu_mxn_importacion'] is not None else 0.0,
                    'costo_total_mxn_imporacion': float(row['costo_total_mxn_imporacion']) if row['costo_total_mxn_imporacion'] is not None else 0.0,
                    'iva': float(row['iva']) if row['iva'] is not None else 0.0,
                    'costo_total_con_iva': float(row['costo_total_con_iva']) if row['costo_total_con_iva'] is not None else 0.0
                }
                materiales_list.append(material)
            
            cursor.close()
            return materiales_list
            
        except Exception as e:
            logger.error(f"Error obteniendo materiales para compra {imi}: {str(e)}")
            return []
    
    def calculate_kpis(self, filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calcula KPIs de compras"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Query base para KPIs principales
            base_query = """
                SELECT 
                    COUNT(DISTINCT c2.imi) as total_compras,
                    COUNT(DISTINCT c2.proveedor) as total_proveedores,
                    SUM(c2m.kg) as total_kilogramos,
                    SUM(c2.total_con_iva_divisa) as total_costo_divisa,
                    SUM(c2.total_con_iva_mxn) as total_costo_mxn,
                    SUM(CASE WHEN c2.anticipo_monto > 0 THEN 1 ELSE 0 END) as compras_con_anticipo,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NOT NULL THEN 1 ELSE 0 END) as compras_pagadas,
                    AVG(c2.tipo_cambio_estimado) as tipo_cambio_promedio,
                    AVG(c2.dias_credito) as dias_credito_promedio,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NULL THEN c2.total_con_iva_mxn ELSE 0 END) as compras_pendientes,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NULL THEN 1 ELSE 0 END) as compras_pendientes_count,
                    SUM(c2.total_con_iva_mxn) / NULLIF(COUNT(DISTINCT c2.proveedor), 0) as promedio_por_proveedor,
                    COUNT(DISTINCT c2.proveedor) as proveedores_unicos
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.id = c2m.compra_id
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros si existen
            if filtros:
                if filtros.get('mes'):
                    base_query += " AND EXTRACT(MONTH FROM c2.fecha_pedido) = %s"
                    params.append(filtros['mes'])
                
                if filtros.get('año'):
                    base_query += " AND EXTRACT(YEAR FROM c2.fecha_pedido) = %s"
                    params.append(filtros['año'])
                
                if filtros.get('proveedor'):
                    base_query += " AND c2.proveedor ILIKE %s"
                    params.append(f"%{filtros['proveedor']}%")
                
                if filtros.get('material'):
                    base_query += " AND c2m.material_codigo ILIKE %s"
                    params.append(f"%{filtros['material']}%")
            
            cursor.execute(base_query, params)
            kpis_basicos = cursor.fetchone()
            
            # Query adicional para KPIs avanzados
            kpis_avanzados_query = """
                SELECT 
                    AVG(CASE 
                        WHEN c2.fecha_salida_estimada IS NOT NULL AND c2.fecha_arribo_estimada IS NOT NULL 
                        THEN (c2.fecha_arribo_estimada - c2.fecha_salida_estimada)
                        ELSE NULL 
                    END) as ciclo_compras_promedio,
                    AVG(c2m.pu_divisa) as precio_unitario_promedio_usd,
                    AVG(c2m.pu_mxn) as precio_unitario_promedio_mxn,
                    COUNT(DISTINCT c2m.material_codigo) as materiales_unicos
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.id = c2m.compra_id
                WHERE 1=1
            """
            
            # Aplicar los mismos filtros
            if filtros:
                if filtros.get('mes'):
                    kpis_avanzados_query += " AND EXTRACT(MONTH FROM c2.fecha_pedido) = %s"
                if filtros.get('año'):
                    kpis_avanzados_query += " AND EXTRACT(YEAR FROM c2.fecha_pedido) = %s"
                if filtros.get('proveedor'):
                    kpis_avanzados_query += " AND c2.proveedor ILIKE %s"
                if filtros.get('material'):
                    kpis_avanzados_query += " AND c2m.material_codigo ILIKE %s"
            
            cursor.execute(kpis_avanzados_query, params)
            kpis_avanzados = cursor.fetchone()
            
            cursor.close()
            
            # Combinar resultados
            resultado = {}
            if kpis_basicos:
                resultado.update(dict(kpis_basicos))
            if kpis_avanzados:
                resultado.update(dict(kpis_avanzados))
            
            # Calcular KPIs derivados
            if resultado.get('total_compras', 0) > 0:
                # Rotación de inventario (simplificada - basada en frecuencia de compras)
                resultado['rotacion_inventario'] = resultado.get('total_compras', 0) / 12.0  # Aproximación mensual
                
                # Margen bruto promedio (simplificado - diferencia entre precio unitario promedio)
                precio_usd = resultado.get('precio_unitario_promedio_usd', 0) or 0
                precio_mxn = resultado.get('precio_unitario_promedio_mxn', 0) or 0
                if precio_usd > 0 and precio_mxn > 0:
                    # Estimación de margen basada en diferencia de precios
                    resultado['margen_bruto_promedio'] = ((precio_mxn - precio_usd * 20) / precio_mxn) * 100
                else:
                    resultado['margen_bruto_promedio'] = 0
            else:
                resultado['rotacion_inventario'] = 0
                resultado['margen_bruto_promedio'] = 0
            
            # Ciclo de compras
            resultado['ciclo_compras'] = resultado.get('ciclo_compras_promedio', 0) or 0
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error calculando KPIs: {str(e)}")
            return {}
    
    def get_evolucion_precios(self, filtros: Dict[str, Any] = None, moneda: str = 'USD') -> Dict[str, Any]:
        """Obtiene evolución mensual de precios por kg"""
        conn = self.get_connection()
        if not conn:
            return {'labels': [], 'data': [], 'titulo': 'Sin datos'}
        
        try:
            cursor = conn.cursor()
            
            # Determinar campo de precio según moneda
            precio_field = 'pu_divisa' if moneda == 'USD' else 'pu_mxn'
            
            query = f"""
                SELECT 
                    DATE_TRUNC('month', c2.fecha_pedido) as mes,
                    AVG(c2m.{precio_field}) as precio_promedio,
                    MIN(c2m.{precio_field}) as precio_min,
                    MAX(c2m.{precio_field}) as precio_max
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.id = c2m.compra_id
                WHERE c2.fecha_pedido IS NOT NULL 
                AND c2m.{precio_field} IS NOT NULL 
                AND c2m.{precio_field} > 0
            """
            
            params = []
            
            # Aplicar filtros
            if filtros and filtros.get('material'):
                query += " AND c2m.material_codigo ILIKE %s"
                params.append(f"%{filtros['material']}%")
            
            query += """
                GROUP BY DATE_TRUNC('month', c2.fecha_pedido)
                ORDER BY mes ASC
            """
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            cursor.close()
            
            if not resultados:
                return {'labels': [], 'data': [], 'titulo': 'Sin datos'}
            
            labels = []
            data = []
            
            for row in resultados:
                mes = row['mes']
                precio_promedio = float(row['precio_promedio']) if row['precio_promedio'] else 0
                precio_min = float(row['precio_min']) if row['precio_min'] else 0
                precio_max = float(row['precio_max']) if row['precio_max'] else 0
                
                labels.append(mes.strftime('%Y-%m'))
                data.append({
                    'fecha': mes.strftime('%Y-%m'),
                    'precio_promedio': precio_promedio,
                    'precio_min': precio_min,
                    'precio_max': precio_max
                })
            
            titulo = f"Evolución de Precios por kg ({moneda})"
            if filtros and filtros.get('material'):
                titulo += f" - {filtros['material']}"
            
            return {
                'labels': labels,
                'data': data,
                'titulo': titulo
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo evolución de precios: {str(e)}")
            return {'labels': [], 'data': [], 'titulo': 'Error'}
    
    def get_flujo_pagos(self, filtros: Dict[str, Any] = None, moneda: str = 'USD') -> Dict[str, Any]:
        """Obtiene flujo de pagos por semana"""
        conn = self.get_connection()
        if not conn:
            return {'labels': [], 'datasets': [], 'titulo': 'Sin datos'}
        
        try:
            cursor = conn.cursor()
            
            # Determinar campo de monto según moneda
            monto_field = 'total_con_iva_divisa' if moneda == 'USD' else 'total_con_iva_mxn'
            
            query = f"""
                SELECT 
                    DATE_TRUNC('week', COALESCE(c2.fecha_pago_factura, c2.fecha_pedido)) as semana,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NOT NULL THEN c2.{monto_field} ELSE 0 END) as pagos,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NULL THEN c2.{monto_field} ELSE 0 END) as pendiente
                FROM compras_v2 c2
                WHERE c2.fecha_pedido IS NOT NULL
            """
            
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('mes'):
                    query += " AND EXTRACT(MONTH FROM c2.fecha_pedido) = %s"
                    params.append(filtros['mes'])
                
                if filtros.get('año'):
                    query += " AND EXTRACT(YEAR FROM c2.fecha_pedido) = %s"
                    params.append(filtros['año'])
                
                if filtros.get('proveedor'):
                    query += " AND c2.proveedor ILIKE %s"
                    params.append(f"%{filtros['proveedor']}%")
            
            query += """
                GROUP BY DATE_TRUNC('week', c2.fecha_pago_factura)
                ORDER BY semana ASC
            """
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            cursor.close()
            
            if not resultados:
                return {'labels': [], 'datasets': [], 'titulo': 'Sin datos'}
            
            labels = []
            pagos_data = []
            pendiente_data = []
            
            for row in resultados:
                semana = row['semana']
                pagos = float(row['pagos']) if row['pagos'] else 0
                pendiente = float(row['pendiente']) if row['pendiente'] else 0
                
                labels.append(f"Semana {semana.isocalendar()[1]}")
                pagos_data.append(pagos)
                pendiente_data.append(pendiente)
            
            titulo = f"Flujo de Pagos Semanal ({moneda})"
            
            return {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Pagos Realizados',
                        'data': pagos_data,
                        'backgroundColor': '#10b981'
                    },
                    {
                        'label': 'Pendiente',
                        'data': pendiente_data,
                        'backgroundColor': '#f59e0b'
                    }
                ],
                'titulo': titulo
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo flujo de pagos: {str(e)}")
            return {'labels': [], 'datasets': [], 'titulo': 'Error'}
    
    def get_aging_cuentas_pagar(self, filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene aging de cuentas por pagar"""
        conn = self.get_connection()
        if not conn:
            return {'labels': [], 'data': [], 'titulo': 'Sin datos'}
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    periodo,
                    SUM(monto) as monto
                FROM (
                SELECT 
                    CASE 
                        WHEN c2.fecha_vencimiento IS NULL THEN 'Sin fecha'
                        WHEN c2.fecha_vencimiento < CURRENT_DATE THEN 'Vencido'
                        WHEN c2.fecha_vencimiento <= CURRENT_DATE + INTERVAL '30 days' THEN '0-30 días'
                        WHEN c2.fecha_vencimiento <= CURRENT_DATE + INTERVAL '60 days' THEN '31-60 días'
                        WHEN c2.fecha_vencimiento <= CURRENT_DATE + INTERVAL '90 days' THEN '61-90 días'
                        ELSE '90+ días'
                    END as periodo,
                        c2.total_con_iva_mxn as monto,
                        c2.fecha_pedido,
                        c2.proveedor
                FROM compras_v2 c2
                WHERE c2.fecha_pago_factura IS NULL
                ) subquery
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('mes'):
                    query += " AND EXTRACT(MONTH FROM subquery.fecha_pedido) = %s"
                    params.append(filtros['mes'])
                
                if filtros.get('año'):
                    query += " AND EXTRACT(YEAR FROM subquery.fecha_pedido) = %s"
                    params.append(filtros['año'])
                
                if filtros.get('proveedor'):
                    query += " AND subquery.proveedor ILIKE %s"
                    params.append(f"%{filtros['proveedor']}%")
            
            query += """
                GROUP BY periodo
                ORDER BY 
                    CASE periodo
                        WHEN 'Vencido' THEN 1
                        WHEN '0-30 días' THEN 2
                        WHEN '31-60 días' THEN 3
                        WHEN '61-90 días' THEN 4
                        WHEN '90+ días' THEN 5
                        ELSE 6
                    END
            """
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            cursor.close()
            
            if not resultados:
                return {'labels': [], 'data': [], 'titulo': 'Sin datos'}
            
            labels = []
            data = []
            
            for row in resultados:
                periodo = row['periodo']
                monto = float(row['monto']) if row['monto'] else 0
                
                labels.append(periodo)
                data.append(monto)
            
            titulo = "Aging de Cuentas por Pagar"
            
            return {
                'labels': labels,
                'data': data,
                'titulo': titulo
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo aging de cuentas por pagar: {str(e)}")
            return {'labels': [], 'data': [], 'titulo': 'Error'}
    
    def get_materiales(self) -> List[str]:
        """Obtiene lista de materiales únicos"""
        conn = self.get_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos para obtener materiales")
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT material_codigo
                FROM compras_v2_materiales
                WHERE material_codigo IS NOT NULL AND material_codigo != ''
                ORDER BY material_codigo
            """)
            
            results = cursor.fetchall()
            materiales = [row['material_codigo'] for row in results]
            cursor.close()
            
            logger.info(f"Materiales obtenidos: {len(materiales)}")
            
            return materiales
            
        except Exception as e:
            logger.error(f"Error obteniendo materiales: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_proveedores(self) -> List[str]:
        """Obtiene lista de proveedores únicos"""
        conn = self.get_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos para obtener proveedores")
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT proveedor
                FROM compras_v2
                WHERE proveedor IS NOT NULL AND proveedor != ''
                ORDER BY proveedor
            """)
            
            results = cursor.fetchall()
            proveedores = [row['proveedor'] for row in results]
            cursor.close()
            
            logger.info(f"Proveedores obtenidos: {len(proveedores)}")
            
            return proveedores
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedores: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_años_disponibles(self) -> List[int]:
        """Obtiene lista de años disponibles en compras_v2"""
        conn = self.get_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos para obtener años disponibles")
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT EXTRACT(YEAR FROM fecha_pedido)::integer as año
                FROM compras_v2
                WHERE fecha_pedido IS NOT NULL
                ORDER BY año DESC
            """)
            
            results = cursor.fetchall()
            años = [int(row['año']) for row in results if row['año'] is not None]
            cursor.close()
            
            logger.info(f"Años disponibles obtenidos: {años}")
            
            return años
            
        except Exception as e:
            logger.error(f"Error obteniendo años disponibles: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def __del__(self):
        """Destructor para cerrar conexión"""
        self.close_connection()
