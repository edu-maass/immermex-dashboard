"""
Servicio ultra optimizado para compras_v2 usando procesamiento por lotes real
"""
import os
import psycopg2
from psycopg2.extras import execute_batch
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ComprasV2ServiceUltraOptimized:
    """
    Servicio ultra optimizado para compras_v2 que usa procesamiento por lotes real
    con execute_batch de psycopg2 para máxima eficiencia
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
        """Obtiene conexión a Supabase usando la configuración existente del sistema"""
        if self.conn and not self.conn.closed:
            return self.conn
        
        try:
            # Usar la configuración existente del sistema que ya maneja IPv4
            from database import engine
            
            # Obtener conexión raw de SQLAlchemy
            raw_conn = engine.raw_connection()
            self.conn = raw_conn.connection
            
            logger.info("Conexión a Supabase establecida usando configuración del sistema")
            return self.conn
            
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {str(e)}")
            return None
    
    def safe_decimal(self, value, default=0.0):
        """Convierte un valor a decimal de forma segura"""
        if value is None:
            return Decimal(str(default))
        
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            logger.warning(f"Error convirtiendo '{value}' a decimal, usando {default}")
            return Decimal(str(default))
    
    def safe_string(self, value, default=''):
        """Convierte un valor a string de forma segura"""
        if value is None:
            return default
        return str(value).strip()
    
    def safe_percentage(self, value, max_value=None):
        """Convierte un valor a decimal de forma segura para campos NUMERIC(5,4)"""
        if value is None or value == '':
            return Decimal('0.0000')
        
        try:
            # Convertir a float primero
            float_val = float(value)
            
            # Si el valor es mayor a 1, asumir que es un porcentaje (ej: 15.5 -> 0.155)
            if float_val > 1:
                float_val = float_val / 100
            
            # Convertir a Decimal con 4 decimales
            decimal_value = Decimal(str(float_val)).quantize(Decimal('0.0001'))
            
            # Validar que esté en rango válido (0 a 1)
            if decimal_value < 0:
                logger.warning(f"Porcentaje negativo '{value}', usando 0.0000")
                return Decimal('0.0000')
            elif decimal_value > 1:
                logger.warning(f"Porcentaje mayor a 100% '{value}', usando 1.0000")
                return Decimal('1.0000')
            
            return decimal_value
            
        except (ValueError, TypeError):
            logger.warning(f"Error convirtiendo porcentaje '{value}' a decimal, usando 0.0000")
            return Decimal('0.0000')
    
    def save_compras_v2_ultra_batch(self, compras: List[Dict[str, Any]], archivo_id: int) -> Dict[str, int]:
        """Guarda compras_v2 usando execute_batch para máxima eficiencia"""
        if not compras:
            return {"guardadas": 0, "omitidas": 0}
        
        conn = self.get_connection()
        if not conn:
            return {"guardadas": 0, "omitidas": 0}
        
        cursor = conn.cursor()
        compras_guardadas = 0
        compras_omitidas = 0
        
        try:
            # Obtener todos los IMIs existentes de una vez
            imis = [compra['imi'] for compra in compras]
            placeholders = ','.join(['%s'] * len(imis))
            
            cursor.execute(f"SELECT imi FROM compras_v2 WHERE imi IN ({placeholders})", imis)
            existing_imis = {row[0] for row in cursor.fetchall()}
            
            # Separar en INSERTs y UPDATEs
            insert_data = []
            update_data = []
            
            for compra in compras:
                # Validar campos obligatorios
                if not compra.get('imi') or compra['imi'] <= 0:
                    logger.warning(f"Saltando compra sin IMI válido: {compra.get('proveedor', 'N/A')}")
                    compras_omitidas += 1
                    continue
                
                if not compra.get('proveedor') or not compra.get('fecha_pedido'):
                    logger.warning(f"Saltando compra con datos incompletos: IMI={compra['imi']}")
                    compras_omitidas += 1
                    continue
                
                # Calcular fecha_vencimiento automáticamente
                fecha_vencimiento = self.calculate_fecha_vencimiento(
                    compra.get('fecha_salida_real'),
                    compra.get('fecha_salida_estimada'),
                    compra.get('dias_credito')
                )
                
                compra_tuple = (
                    compra['imi'], compra['proveedor'], compra['fecha_pedido'], compra.get('puerto_origen'),
                    compra.get('fecha_salida_estimada'), compra.get('fecha_arribo_estimada'), compra['moneda'],
                    compra['dias_credito'], self.safe_percentage(compra['anticipo_pct']), 
                    self.safe_decimal(compra['anticipo_monto']), compra.get('fecha_anticipo'), 
                    compra.get('fecha_pago_factura'), compra.get('fecha_salida_real'), compra.get('fecha_arribo_real'), 
                    compra.get('fecha_planta_real'), self.safe_decimal(compra.get('tipo_cambio_estimado')), 
                    self.safe_decimal(compra.get('tipo_cambio_real')), self.safe_decimal(compra.get('gastos_importacion_divisa')), 
                    self.safe_decimal(compra.get('gastos_importacion_mxn')), self.safe_percentage(compra.get('porcentaje_gastos_importacion')), 
                    self.safe_decimal(compra.get('iva_monto_mxn')), self.safe_decimal(compra.get('total_con_iva_mxn')), 
                    fecha_vencimiento, datetime.utcnow(), datetime.utcnow()
                )
                
                if compra['imi'] in existing_imis:
                    # Para UPDATE, agregar IMI al final
                    update_data.append(compra_tuple + (compra['imi'],))
                else:
                    insert_data.append(compra_tuple)
            
            # Ejecutar INSERTs en lote usando execute_batch
            if insert_data:
                insert_sql = """
                    INSERT INTO compras_v2 (
                        imi, proveedor, fecha_pedido, puerto_origen,
                        fecha_salida_estimada, fecha_arribo_estimada, moneda,
                        dias_credito, anticipo_pct, anticipo_monto, fecha_anticipo,
                        fecha_pago_factura, fecha_salida_real, fecha_arribo_real,
                        fecha_planta_real, tipo_cambio_estimado, tipo_cambio_real,
                        gastos_importacion_divisa, gastos_importacion_mxn,
                        porcentaje_gastos_importacion, iva_monto_mxn, total_con_iva_mxn,
                        fecha_vencimiento, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                execute_batch(cursor, insert_sql, insert_data, page_size=100)
                compras_guardadas += len(insert_data)
                logger.info(f"Insertados {len(insert_data)} registros nuevos")
            
            # Ejecutar UPDATEs en lote usando execute_batch
            if update_data:
                update_sql = """
                    UPDATE compras_v2 SET
                        proveedor = %s, fecha_pedido = %s, puerto_origen = %s,
                        fecha_salida_estimada = %s, fecha_arribo_estimada = %s, moneda = %s,
                        dias_credito = %s, anticipo_pct = %s, anticipo_monto = %s,
                        fecha_anticipo = %s, fecha_pago_factura = %s, fecha_salida_real = %s,
                        fecha_arribo_real = %s, fecha_planta_real = %s, tipo_cambio_estimado = %s,
                        tipo_cambio_real = %s, gastos_importacion_divisa = %s,
                        gastos_importacion_mxn = %s, porcentaje_gastos_importacion = %s,
                        iva_monto_mxn = %s, total_con_iva_mxn = %s,
                        fecha_vencimiento = %s, updated_at = %s
                    WHERE imi = %s
                """
                execute_batch(cursor, update_sql, update_data, page_size=100)
                compras_guardadas += len(update_data)
                logger.info(f"Actualizados {len(update_data)} registros existentes")
            
            conn.commit()
            logger.info(f"Total compras procesadas: {compras_guardadas}, omitidas: {compras_omitidas}")
            
        except Exception as e:
            logger.error(f"Error en procesamiento por lotes: {str(e)}")
            conn.rollback()
            compras_guardadas = 0
        finally:
            cursor.close()
        
        return {"guardadas": compras_guardadas, "omitidas": compras_omitidas}
    
    def save_compras_v2_materiales_ultra_batch(self, materiales: List[Dict[str, Any]]) -> Dict[str, int]:
        """Guarda materiales usando execute_batch para máxima eficiencia"""
        if not materiales:
            return {"guardadas": 0, "omitidas": 0}
        
        conn = self.get_connection()
        if not conn:
            return {"guardadas": 0, "omitidas": 0}
        
        cursor = conn.cursor()
        materiales_guardados = 0
        materiales_omitidos = 0
        
        try:
            # Obtener todos los IDs existentes de una vez
            material_ids = [(mat['compra_id'], mat['material_codigo']) for mat in materiales]
            
            # Verificar existencias usando una consulta más eficiente
            existing_materials = set()
            if material_ids:
                placeholders = ','.join(['(%s,%s)'] * len(material_ids))
                values = [item for sublist in material_ids for item in sublist]
                cursor.execute(f"""
                    SELECT compra_imi, material_codigo FROM compras_v2_materiales 
                    WHERE (compra_imi, material_codigo) IN ({placeholders})
                """, values)
                existing_materials = {(row[0], row[1]) for row in cursor.fetchall()}
            
            # Separar en INSERTs y UPDATEs
            insert_data = []
            update_data = []
            
            for material in materiales:
                # Validar que tenga compra_id válido
                compra_id = material.get('compra_id')
                if not compra_id or compra_id <= 0 or compra_id is None:
                    logger.warning(f"Saltando material sin compra_id válido: Material={material.get('material_codigo', 'N/A')}, compra_id={compra_id}")
                    materiales_omitidos += 1
                    continue
                
                # Validar que el material tenga datos básicos
                if not material.get('material_codigo') or not material.get('kg') or material['kg'] <= 0:
                    logger.warning(f"Saltando material con datos incompletos: Material={material.get('material_codigo', 'N/A')}, KG={material.get('kg', 'N/A')}")
                    materiales_omitidos += 1
                    continue
                
                material_tuple = (
                    material['compra_id'], material['material_codigo'], self.safe_decimal(material['kg']),
                    self.safe_decimal(material['pu_divisa']), self.safe_decimal(material.get('pu_mxn')),
                    self.safe_decimal(material.get('costo_total_divisa')), self.safe_decimal(material.get('costo_total_mxn')),
                    self.safe_decimal(material.get('pu_mxn_importacion')), self.safe_decimal(material.get('costo_total_mxn_imporacion')),
                    self.safe_decimal(material.get('iva')), self.safe_decimal(material.get('costo_total_con_iva')),
                    datetime.utcnow(), datetime.utcnow()
                )
                
                if (material['compra_id'], material['material_codigo']) in existing_materials:
                    # Para UPDATE, agregar compra_id y material_codigo al final
                    update_data.append(material_tuple + (material['compra_id'], material['material_codigo']))
                else:
                    insert_data.append(material_tuple)
            
            # Ejecutar INSERTs en lote
            if insert_data:
                insert_sql = """
                    INSERT INTO compras_v2_materiales (
                        compra_imi, material_codigo, kg, pu_divisa,
                        pu_mxn, costo_total_divisa, costo_total_mxn,
                        pu_mxn_importacion, costo_total_mxn_imporacion, iva, costo_total_con_iva,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                execute_batch(cursor, insert_sql, insert_data, page_size=200)
                materiales_guardados += len(insert_data)
                logger.info(f"Insertados {len(insert_data)} materiales nuevos")
            
            # Ejecutar UPDATEs en lote
            if update_data:
                update_sql = """
                    UPDATE compras_v2_materiales SET
                        kg = %s, pu_divisa = %s, pu_mxn = %s,
                        costo_total_divisa = %s, costo_total_mxn = %s,
                        pu_mxn_importacion = %s, costo_total_mxn_imporacion = %s,
                        iva = %s, costo_total_con_iva = %s, updated_at = %s
                    WHERE compra_imi = %s AND material_codigo = %s
                """
                execute_batch(cursor, update_sql, update_data, page_size=200)
                materiales_guardados += len(update_data)
                logger.info(f"Actualizados {len(update_data)} materiales existentes")
            
            conn.commit()
            logger.info(f"Total materiales procesados: {materiales_guardados}, omitidos: {materiales_omitidos}")
            
        except Exception as e:
            logger.error(f"Error en procesamiento de materiales por lotes: {str(e)}")
            conn.rollback()
            materiales_guardados = 0
        finally:
            cursor.close()
        
        return {"guardadas": materiales_guardados, "omitidas": materiales_omitidos}
    
    def save_compras_data(self, processed_data_dict: Dict[str, Any], archivo_id: int) -> Dict[str, int]:
        """Método principal que guarda todos los datos usando procesamiento ultra optimizado"""
        try:
            compras = processed_data_dict.get('compras_v2', [])
            materiales = processed_data_dict.get('compras_v2_materiales', [])
            
            logger.info(f"Iniciando guardado ultra optimizado de {len(compras)} compras y {len(materiales)} materiales")
            
            # Guardar compras usando procesamiento ultra optimizado
            compras_result = self.save_compras_v2_ultra_batch(compras, archivo_id)
            
            # Guardar materiales usando procesamiento ultra optimizado
            materiales_result = self.save_compras_v2_materiales_ultra_batch(materiales)
            
            return {
                'compras_guardadas': compras_result['guardadas'],
                'compras_omitidas': compras_result['omitidas'],
                'materiales_guardados': materiales_result['guardadas'],
                'materiales_omitidos': materiales_result['omitidas'],
                'total_procesados': compras_result['guardadas'] + materiales_result['guardadas'],
                'total_omitidos': compras_result['omitidas'] + materiales_result['omitidas']
            }
            
        except Exception as e:
            logger.error(f"Error guardando datos: {str(e)}")
            return {
                'compras_guardadas': 0,
                'materiales_guardados': 0,
                'total_procesados': 0
            }
    
    def calculate_fecha_vencimiento(self, fecha_salida_real, fecha_salida_estimada, dias_credito):
        """
        Calcula la fecha de vencimiento basada en la fecha de salida y días de crédito
        
        Args:
            fecha_salida_real: Fecha real de salida (prioridad alta)
            fecha_salida_estimada: Fecha estimada de salida (prioridad baja)
            dias_credito: Número de días de crédito
        
        Returns:
            datetime: Fecha de vencimiento calculada o None si no se puede calcular
        """
        try:
            from datetime import timedelta
            
            # Validar días de crédito
            if not dias_credito or dias_credito <= 0:
                return None
            
            # Determinar qué fecha usar (prioridad: fecha_salida_real > fecha_salida_estimada)
            fecha_base = None
            
            if fecha_salida_real:
                fecha_base = fecha_salida_real
            elif fecha_salida_estimada:
                fecha_base = fecha_salida_estimada
            
            if not fecha_base:
                return None
            
            # Calcular fecha de vencimiento
            fecha_vencimiento = fecha_base + timedelta(days=dias_credito)
            
            logger.debug(f"Fecha vencimiento calculada: {fecha_base} + {dias_credito} días = {fecha_vencimiento}")
            
            return fecha_vencimiento
            
        except Exception as e:
             logger.error(f"Error calculando fecha_vencimiento: {str(e)}")
             return None
    
    def close_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Conexión a Supabase cerrada")
