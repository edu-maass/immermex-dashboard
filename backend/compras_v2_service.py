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
    
    def save_compras_v2(self, compras: List[Dict[str, Any]], archivo_id: int) -> int:
        """Guarda compras en la tabla compras_v2"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            compras_guardadas = 0
            
            for compra in compras:
                try:
                    # Verificar si ya existe
                    cursor.execute("SELECT id FROM compras_v2 WHERE imi = %s", (compra['imi'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        logger.warning(f"Compra con IMI {compra['imi']} ya existe, actualizando...")
                        
                        # Actualizar registro existente
                        cursor.execute("""
                            UPDATE compras_v2 SET
                                proveedor = %s,
                                fecha_pedido = %s,
                                puerto_origen = %s,
                                fecha_salida_estimada = %s,
                                fecha_arribo_estimada = %s,
                                moneda = %s,
                                dias_credito = %s,
                                anticipo_pct = %s,
                                anticipo_monto = %s,
                                fecha_anticipo = %s,
                                fecha_pago_factura = %s,
                                tipo_cambio_estimado = %s,
                                tipo_cambio_real = %s,
                                gastos_importacion_divisa = %s,
                                gastos_importacion_mxn = %s,
                                porcentaje_gastos_importacion = %s,
                                iva_monto_divisa = %s,
                                iva_monto_mxn = %s,
                                total_con_iva_divisa = %s,
                                total_con_iva_mxn = %s,
                                updated_at = %s
                            WHERE imi = %s
                        """, (
                            compra['proveedor'],
                            compra['fecha_pedido'],
                            compra['puerto_origen'],
                            compra['fecha_salida_estimada'],
                            compra['fecha_arribo_estimada'],
                            compra['moneda'],
                            compra['dias_credito'],
                            self.safe_decimal(compra['anticipo_pct']),
                            self.safe_decimal(compra['anticipo_monto']),
                            compra['fecha_anticipo'],
                            compra['fecha_pago_factura'],
                            self.safe_decimal(compra['tipo_cambio_estimado']),
                            self.safe_decimal(compra['tipo_cambio_real']),
                            self.safe_decimal(compra['gastos_importacion_divisa']),
                            self.safe_decimal(compra['gastos_importacion_mxn']),
                            self.safe_decimal(compra['porcentaje_gastos_importacion']),
                            self.safe_decimal(compra['iva_monto_divisa']),
                            self.safe_decimal(compra['iva_monto_mxn']),
                            self.safe_decimal(compra['total_con_iva_divisa']),
                            self.safe_decimal(compra['total_con_iva_mxn']),
                            datetime.utcnow(),
                            compra['imi']
                        ))
                    else:
                        # Insertar nuevo registro
                        cursor.execute("""
                            INSERT INTO compras_v2 (
                                imi, proveedor, fecha_pedido, puerto_origen,
                                fecha_salida_estimada, fecha_arribo_estimada,
                                moneda, dias_credito, anticipo_pct, anticipo_monto,
                                fecha_anticipo, fecha_pago_factura,
                                tipo_cambio_estimado, tipo_cambio_real,
                                gastos_importacion_divisa, gastos_importacion_mxn,
                                porcentaje_gastos_importacion, iva_monto_divisa,
                                iva_monto_mxn, total_con_iva_divisa, total_con_iva_mxn,
                                created_at, updated_at
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            compra['imi'],
                            compra['proveedor'],
                            compra['fecha_pedido'],
                            compra['puerto_origen'],
                            compra['fecha_salida_estimada'],
                            compra['fecha_arribo_estimada'],
                            compra['moneda'],
                            compra['dias_credito'],
                            self.safe_decimal(compra['anticipo_pct']),
                            self.safe_decimal(compra['anticipo_monto']),
                            compra['fecha_anticipo'],
                            compra['fecha_pago_factura'],
                            self.safe_decimal(compra['tipo_cambio_estimado']),
                            self.safe_decimal(compra['tipo_cambio_real']),
                            self.safe_decimal(compra['gastos_importacion_divisa']),
                            self.safe_decimal(compra['gastos_importacion_mxn']),
                            self.safe_decimal(compra['porcentaje_gastos_importacion']),
                            self.safe_decimal(compra['iva_monto_divisa']),
                            self.safe_decimal(compra['iva_monto_mxn']),
                            self.safe_decimal(compra['total_con_iva_divisa']),
                            self.safe_decimal(compra['total_con_iva_mxn']),
                            datetime.utcnow(),
                            datetime.utcnow()
                        ))
                    
                    compras_guardadas += 1
                    
                except Exception as e:
                    logger.error(f"Error guardando compra IMI {compra['imi']}: {str(e)}")
                    continue
            
            conn.commit()
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
    
    def get_compras_by_filtros(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtiene compras filtradas de compras_v2"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Construir query base
            query = """
                SELECT 
                    c2.imi, c2.proveedor, c2.fecha_pedido, c2.puerto_origen,
                    c2.fecha_salida_estimada, c2.fecha_arribo_estimada,
                    c2.moneda, c2.dias_credito, c2.anticipo_pct, c2.anticipo_monto,
                    c2.fecha_anticipo, c2.fecha_pago_factura,
                    c2.tipo_cambio_estimado, c2.tipo_cambio_real,
                    c2.gastos_importacion_divisa, c2.gastos_importacion_mxn,
                    c2.porcentaje_gastos_importacion, c2.iva_monto_divisa,
                    c2.iva_monto_mxn, c2.total_con_iva_divisa, c2.total_con_iva_mxn,
                    COUNT(c2m.id) as materiales_count
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_id
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if filtros.get('proveedor'):
                query += " AND c2.proveedor ILIKE %s"
                params.append(f"%{filtros['proveedor']}%")
            
            if filtros.get('fecha_desde'):
                query += " AND c2.fecha_pedido >= %s"
                params.append(filtros['fecha_desde'])
            
            if filtros.get('fecha_hasta'):
                query += " AND c2.fecha_pedido <= %s"
                params.append(filtros['fecha_hasta'])
            
            if filtros.get('moneda'):
                query += " AND c2.moneda = %s"
                params.append(filtros['moneda'])
            
            # Agrupar y ordenar
            query += " GROUP BY c2.imi ORDER BY c2.fecha_pedido DESC"
            
            if filtros.get('limit'):
                query += " LIMIT %s"
                params.append(filtros['limit'])
            
            cursor.execute(query, params)
            compras = cursor.fetchall()
            
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
            cursor.close()
            return materiales
            
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
            
            # Query base para KPIs
            base_query = """
                SELECT 
                    COUNT(DISTINCT c2.imi) as total_compras,
                    COUNT(DISTINCT c2.proveedor) as total_proveedores,
                    SUM(c2m.kg) as total_kilogramos,
                    SUM(c2.total_con_iva_divisa) as total_costo_divisa,
                    SUM(c2.total_con_iva_mxn) as total_costo_mxn,
                    SUM(CASE WHEN c2.anticipo_monto > 0 THEN 1 ELSE 0 END) as compras_con_anticipo,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NOT NULL THEN 1 ELSE 0 END) as compras_pagadas,
                    AVG(c2.tipo_cambio_estimado) as tipo_cambio_promedio
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_id
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros si existen
            if filtros:
                if filtros.get('fecha_desde'):
                    base_query += " AND c2.fecha_pedido >= %s"
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    base_query += " AND c2.fecha_pedido <= %s"
                    params.append(filtros['fecha_hasta'])
            
            cursor.execute(base_query, params)
            kpis = cursor.fetchone()
            
            cursor.close()
            return dict(kpis) if kpis else {}
            
        except Exception as e:
            logger.error(f"Error calculando KPIs: {str(e)}")
            return {}
    
    def __del__(self):
        """Destructor para cerrar conexión"""
        self.close_connection()
