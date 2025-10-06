"""
Servicio optimizado de guardado para compras_v2 y compras_v2_materiales
Con procesamiento por lotes para mejor rendimiento
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class ComprasV2ServiceOptimized:
    """
    Servicio optimizado para guardar datos en compras_v2 y compras_v2_materiales
    """
    
    def __init__(self):
        self.conn = None
    
    def load_production_config(self):
        """Carga la configuración desde variables de entorno"""
        config = {}
        
        # Intentar cargar desde archivo production.env primero
        env_file = "production.env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key] = value
        
        # Sobrescribir con variables de entorno del sistema
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_password = os.getenv('SUPABASE_PASSWORD')
        
        if supabase_url:
            config['SUPABASE_URL'] = supabase_url
        if supabase_password:
            config['SUPABASE_PASSWORD'] = supabase_password
        
        return config
    
    def get_connection(self):
        """Obtiene conexión a Supabase"""
        if self.conn and not self.conn.closed:
            return self.conn
        
        try:
            config = self.load_production_config()
            if not config:
                return None
            
            supabase_url = config.get('SUPABASE_URL')
            supabase_password = config.get('SUPABASE_PASSWORD')
            
            if not supabase_url or not supabase_password:
                logger.error("Variables SUPABASE_URL y SUPABASE_PASSWORD no encontradas")
                return None
            
            # Construir URL de conexión
            if "supabase.co" in supabase_url:
                project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
                conn_string = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
            else:
                logger.error("URL de Supabase no válida")
                return None
            
            self.conn = psycopg2.connect(conn_string)
            logger.info("Conexión a Supabase establecida")
            return self.conn
            
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {str(e)}")
            return None
    
    def safe_decimal(self, value, default=0.0):
        """Convierte un valor a decimal de forma segura"""
        if value is None or value == '':
            return Decimal(str(default))
        try:
            return Decimal(str(value))
        except:
            return Decimal(str(default))
    
    def safe_int(self, value, default=0):
        """Convierte un valor a entero de forma segura"""
        if value is None or value == '':
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
    
    def save_compras_v2_batch(self, compras: List[Dict[str, Any]], archivo_id: int) -> int:
        """Guarda compras en la tabla compras_v2 usando procesamiento por lotes"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            compras_guardadas = 0
            batch_size = 100  # Procesar en lotes de 100 para mejor rendimiento
            
            # Dividir compras en lotes
            for i in range(0, len(compras), batch_size):
                batch = compras[i:i + batch_size]
                logger.info(f"Procesando lote {i//batch_size + 1}: compras {i+1}-{min(i+batch_size, len(compras))}")
                
                try:
                    cursor = conn.cursor()
                    
                    for compra in batch:
                        try:
                            # Verificar si ya existe
                            cursor.execute("SELECT id FROM compras_v2 WHERE imi = %s", (compra['imi'],))
                            existing = cursor.fetchone()
                            
                            if existing:
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
                                        iva_monto_mxn = %s,
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
                                        porcentaje_gastos_importacion,
                                        iva_monto_mxn, total_con_iva_mxn,
                                        created_at, updated_at
                                    )
                                    VALUES (
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                            
                            compras_guardadas += 1
                            
                        except Exception as e:
                            logger.error(f"Error guardando compra IMI {compra['imi']}: {str(e)}")
                            continue
                    
                    # Commit del lote completo
                    conn.commit()
                    logger.info(f"Lote {i//batch_size + 1} guardado exitosamente: {len(batch)} compras")
                    
                except Exception as e:
                    logger.error(f"Error en lote {i//batch_size + 1}: {str(e)}")
                    conn.rollback()
                    continue
                finally:
                    if 'cursor' in locals():
                        cursor.close()
            
            logger.info(f"Guardadas {compras_guardadas} compras en compras_v2")
            return compras_guardadas
            
        except Exception as e:
            logger.error(f"Error general guardando compras: {str(e)}")
            return 0
    
    def save_compras_v2_materiales_batch(self, materiales: List[Dict[str, Any]]) -> int:
        """Guarda materiales en la tabla compras_v2_materiales usando procesamiento por lotes"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            materiales_guardados = 0
            batch_size = 200  # Procesar materiales en lotes más grandes
            
            # Dividir materiales en lotes
            for i in range(0, len(materiales), batch_size):
                batch = materiales[i:i + batch_size]
                logger.info(f"Procesando lote de materiales {i//batch_size + 1}: {len(batch)} materiales")
                
                try:
                    cursor = conn.cursor()
                    
                    for material in batch:
                        try:
                            # Obtener compra_id usando IMI
                            cursor.execute("SELECT id FROM compras_v2 WHERE imi = %s", (material['imi'],))
                            compra_result = cursor.fetchone()
                            
                            if not compra_result:
                                logger.warning(f"No se encontró compra con IMI {material['imi']} para material {material['material_codigo']}")
                                continue
                            
                            compra_id = compra_result[0]
                            
                            # Insertar material
                            cursor.execute("""
                                INSERT INTO compras_v2_materiales (
                                    compra_id, material_codigo, kg, pu_divisa, pu_mxn,
                                    costo_total_divisa, costo_total_mxn, costo_total_mxn_con_gastos,
                                    iva, costo_total_con_iva, created_at, updated_at
                                )
                                VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """, (
                                compra_id,
                                material['material_codigo'],
                                self.safe_decimal(material['kg']),
                                self.safe_decimal(material['pu_divisa']),
                                self.safe_decimal(material['pu_mxn']),
                                self.safe_decimal(material['costo_total_divisa']),
                                self.safe_decimal(material['costo_total_mxn']),
                                self.safe_decimal(material['costo_total_mxn_con_gastos']),
                                self.safe_decimal(material['iva']),
                                self.safe_decimal(material['costo_total_con_iva']),
                                datetime.utcnow(),
                                datetime.utcnow()
                            ))
                            
                            materiales_guardados += 1
                            
                        except Exception as e:
                            logger.error(f"Error guardando material {material['material_codigo']} para IMI {material['imi']}: {str(e)}")
                            continue
                    
                    # Commit del lote completo
                    conn.commit()
                    logger.info(f"Lote de materiales {i//batch_size + 1} guardado exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error en lote de materiales {i//batch_size + 1}: {str(e)}")
                    conn.rollback()
                    continue
                finally:
                    if 'cursor' in locals():
                        cursor.close()
            
            logger.info(f"Guardados {materiales_guardados} materiales en compras_v2_materiales")
            return materiales_guardados
            
        except Exception as e:
            logger.error(f"Error general guardando materiales: {str(e)}")
            return 0
    
    def save_compras_data(self, processed_data: Dict[str, Any], archivo_id: int) -> Dict[str, int]:
        """Guarda datos procesados usando procesamiento por lotes optimizado"""
        try:
            compras = processed_data.get('compras_v2', [])
            materiales = processed_data.get('compras_v2_materiales', [])
            
            logger.info(f"Iniciando guardado optimizado de {len(compras)} compras y {len(materiales)} materiales")
            
            # Guardar compras por lotes
            compras_guardadas = self.save_compras_v2_batch(compras, archivo_id)
            
            # Guardar materiales por lotes
            materiales_guardados = self.save_compras_v2_materiales_batch(materiales)
            
            return {
                'compras_guardadas': compras_guardadas,
                'materiales_guardados': materiales_guardados,
                'total_procesados': compras_guardadas + materiales_guardados
            }
            
        except Exception as e:
            logger.error(f"Error guardando datos: {str(e)}")
            return {
                'compras_guardadas': 0,
                'materiales_guardados': 0,
                'total_procesados': 0
            }
