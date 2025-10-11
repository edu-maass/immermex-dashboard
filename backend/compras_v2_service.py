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
            # En producción (Render), usar variables de entorno directamente
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                # Fallback: intentar cargar desde archivo
                config = self.load_production_config()
                if config:
                    database_url = config.get("DATABASE_URL")
            
            if not database_url:
                logger.error("DATABASE_URL no encontrada en variables de entorno ni en production.env")
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
    
    def calculate_pu_usd(self, pu_divisa, moneda, tipo_cambio_real=None, tipo_cambio_estimado=None):
        """Calcula pu_usd basado en la moneda y tipo de cambio"""
        try:
            pu_divisa_decimal = self.safe_decimal(pu_divisa)
            
            if moneda == 'USD':
                # Si es USD, usar el mismo valor
                return pu_divisa_decimal
            elif moneda == 'MXN':
                # Si es MXN, convertir a USD
                # Priorizar tipo_cambio_real, luego tipo_cambio_estimado como fallback
                # Tratar 0 como NULL para evitar cálculos incorrectos
                tipo_cambio = None
                if tipo_cambio_real is not None and tipo_cambio_real > 0 and tipo_cambio_real != 1.0:
                    tipo_cambio = self.safe_decimal(tipo_cambio_real)
                elif tipo_cambio_estimado is not None and tipo_cambio_estimado > 0 and tipo_cambio_estimado != 1.0:
                    tipo_cambio = self.safe_decimal(tipo_cambio_estimado)
                
                if tipo_cambio and tipo_cambio > 0:
                    return pu_divisa_decimal / tipo_cambio
                else:
                    # Si no hay tipo de cambio, devolver el valor original
                    return pu_divisa_decimal
            else:
                # Para otras monedas, devolver el valor original
                return pu_divisa_decimal
                
        except Exception as e:
            logger.warning(f"Error calculando pu_usd: {str(e)}, usando pu_divisa")
            return self.safe_decimal(pu_divisa)
    
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
    
    def calculate_dias_transporte(self, fecha_salida_real, fecha_arribo_real):
        """Calcula días de transporte (fecha_arribo_real - fecha_salida_real)"""
        if fecha_salida_real is None or fecha_arribo_real is None:
            return None
        
        try:
            # Si son strings, convertir a date
            if isinstance(fecha_salida_real, str):
                from datetime import datetime
                fecha_salida_real = datetime.fromisoformat(fecha_salida_real).date()
            if isinstance(fecha_arribo_real, str):
                from datetime import datetime
                fecha_arribo_real = datetime.fromisoformat(fecha_arribo_real).date()
            
            # Calcular diferencia en días
            dias = (fecha_arribo_real - fecha_salida_real).days
            return dias if dias >= 0 else None
        except Exception as e:
            logger.warning(f"Error calculando dias_transporte: {str(e)}")
            return None
    
    def calculate_dias_puerto_planta(self, fecha_arribo_real, fecha_planta_real):
        """Calcula días de puerto a planta (fecha_planta_real - fecha_arribo_real)"""
        if fecha_arribo_real is None or fecha_planta_real is None:
            return None
        
        try:
            # Si son strings, convertir a date
            if isinstance(fecha_arribo_real, str):
                from datetime import datetime
                fecha_arribo_real = datetime.fromisoformat(fecha_arribo_real).date()
            if isinstance(fecha_planta_real, str):
                from datetime import datetime
                fecha_planta_real = datetime.fromisoformat(fecha_planta_real).date()
            
            # Calcular diferencia en días
            dias = (fecha_planta_real - fecha_arribo_real).days
            return dias if dias >= 0 else None
        except Exception as e:
            logger.warning(f"Error calculando dias_puerto_planta: {str(e)}")
            return None
    
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
                    cursor.execute("SELECT imi FROM compras_v2 WHERE imi = %s", (compra['imi'],))
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
                            'fecha_salida_real': compra.get('fecha_salida_real'),
                            'fecha_arribo_real': compra.get('fecha_arribo_real'),
                            'fecha_planta_real': compra.get('fecha_planta_real'),
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
                        
                        # Calcular dias_transporte y dias_puerto_planta
                        dias_transporte = self.calculate_dias_transporte(
                            compra.get('fecha_salida_real'),
                            compra.get('fecha_arribo_real')
                        )
                        dias_puerto_planta = self.calculate_dias_puerto_planta(
                            compra.get('fecha_arribo_real'),
                            compra.get('fecha_planta_real')
                        )
                        
                        # Agregar columnas calculadas si tienen valor
                        if dias_transporte is not None:
                            update_fields.append("dias_transporte = %s")
                            update_values.append(dias_transporte)
                        
                        if dias_puerto_planta is not None:
                            update_fields.append("dias_puerto_planta = %s")
                            update_values.append(dias_puerto_planta)
                        
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
                        
                        # Calcular dias_transporte y dias_puerto_planta
                        dias_transporte = self.calculate_dias_transporte(
                            compra.get('fecha_salida_real'),
                            compra.get('fecha_arribo_real')
                        )
                        dias_puerto_planta = self.calculate_dias_puerto_planta(
                            compra.get('fecha_arribo_real'),
                            compra.get('fecha_planta_real')
                        )
                        
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
                                dias_transporte, dias_puerto_planta,
                                created_at, updated_at
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                            dias_transporte,
                            dias_puerto_planta,
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
                    # Verificar primero si la compra existe
                    cursor.execute("""
                        SELECT moneda, tipo_cambio_real, tipo_cambio_estimado 
                        FROM compras_v2 
                        WHERE imi = %s
                    """, (material['compra_id'],))
                    compra_info = cursor.fetchone()
                    
                    # Si la compra no existe, skip este material (material huérfano)
                    if not compra_info:
                        logger.warning(f"⚠️  Material huérfano: {material['material_codigo']} - IMI {material['compra_id']} no existe en compras_v2. Omitiendo...")
                        continue
                    
                    # Calcular pu_usd
                    pu_usd = self.calculate_pu_usd(
                        material['pu_divisa'],
                        compra_info[0] if compra_info else 'USD',  # moneda
                        compra_info[1] if compra_info else None,   # tipo_cambio_real
                        compra_info[2] if compra_info else None    # tipo_cambio_estimado
                    )
                    
                    # Verificar si ya existe (usar compra_id + material_codigo como clave compuesta)
                    cursor.execute("""
                        SELECT compra_id FROM compras_v2_materiales 
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
                                pu_usd = %s,
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
                            pu_usd,
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
                                compra_id, material_codigo, kg, pu_divisa, pu_mxn, pu_usd,
                                costo_total_divisa, costo_total_mxn, pu_mxn_importacion,
                                costo_total_mxn_imporacion, iva, costo_total_con_iva,
                                compra_imi, created_at, updated_at
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            material['compra_id'],
                            material['material_codigo'],
                            self.safe_decimal(material['kg']),
                            self.safe_decimal(material['pu_divisa']),
                            self.safe_decimal(material['pu_mxn']),
                            pu_usd,
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
                    
                    # Commit individual para este material
                    conn.commit()
                    materiales_guardados += 1
                    logger.info(f"Material {material['material_codigo']} para compra IMI {material['compra_id']} guardado exitosamente")
                    
                except Exception as e:
                    error_msg = str(e) if str(e) else repr(e)
                    logger.error(f"Error guardando material {material['material_codigo']} para compra {material['compra_id']}: {error_msg}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Rollback individual para este material
                    conn.rollback()
                    continue
            
            logger.info(f"✅ Guardados {materiales_guardados} materiales en compras_v2_materiales")
            
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
    
    def get_compras_simple(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtiene datos básicos de compras con todos los campos necesarios para el dashboard"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Query que incluye todos los campos necesarios para el dashboard
            query = """
                SELECT 
                    c2.imi,
                    c2.proveedor,
                    c2.puerto_origen,
                    c2.fecha_pedido,
                    c2.fecha_salida_estimada,
                    c2.fecha_arribo_estimada,
                    c2.fecha_salida_real,
                    c2.fecha_arribo_real,
                    ARRAY_AGG(DISTINCT c2m.material_codigo) FILTER (WHERE c2m.material_codigo IS NOT NULL) as materiales_codigos
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
                WHERE c2.fecha_pedido IS NOT NULL
                GROUP BY c2.imi, c2.proveedor, c2.puerto_origen, c2.fecha_pedido, 
                         c2.fecha_salida_estimada, c2.fecha_arribo_estimada, 
                         c2.fecha_salida_real, c2.fecha_arribo_real
                ORDER BY c2.fecha_pedido DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, [limit, offset])
            compras_raw = cursor.fetchall()
            
            logger.info(f"Query ejecutada: {query}")
            logger.info(f"Parámetros: {[limit, offset]}")
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
                        'imi': str(row['imi']) if row['imi'] is not None else None,
                        'proveedor': str(row['proveedor']) if row['proveedor'] is not None else None,
                        'puerto_origen': str(row['puerto_origen']) if row['puerto_origen'] is not None else None,
                        'fecha_pedido': row['fecha_pedido'].isoformat() if row['fecha_pedido'] is not None else None,
                        'fecha_salida_estimada': row['fecha_salida_estimada'].isoformat() if row['fecha_salida_estimada'] is not None else None,
                        'fecha_arribo_estimada': row['fecha_arribo_estimada'].isoformat() if row['fecha_arribo_estimada'] is not None else None,
                        'fecha_salida_real': row['fecha_salida_real'].isoformat() if row['fecha_salida_real'] is not None else None,
                        'fecha_arribo_real': row['fecha_arribo_real'].isoformat() if row['fecha_arribo_real'] is not None else None,
                        'materiales_codigos': row['materiales_codigos'] if row['materiales_codigos'] is not None else []
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

    def get_compras_count(self, filtros: Dict[str, Any] = None) -> int:
        """Obtiene el conteo total de compras con filtros"""
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(DISTINCT c2.imi)
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
                
                if filtros.get('material'):
                    query += " AND EXISTS (SELECT 1 FROM compras_v2_materiales c2m WHERE c2m.compra_id = c2.imi AND c2m.material_codigo ILIKE %s)"
                    params.append(f"%{filtros['material']}%")
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error obteniendo conteo de compras: {str(e)}")
            return 0

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
                    c2.imi, c2.proveedor, c2.fecha_pedido
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if filtros.get('proveedor'):
                query += " AND c2.proveedor ILIKE %s"
                params.append(f"%{filtros['proveedor']}%")
            
            if filtros.get('material'):
                query += " AND EXISTS (SELECT 1 FROM compras_v2_materiales WHERE compra_id = c2.imi AND material_codigo ILIKE %s)"
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
            query += " GROUP BY c2.imi, c2.proveedor, c2.fecha_pedido ORDER BY c2.fecha_pedido DESC"
            
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
                WHERE compra_imi = %s
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
                    AVG(c2.tipo_cambio_real) as tipo_cambio_promedio,
                    AVG(c2.dias_credito) as dias_credito_promedio,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NULL THEN c2.total_con_iva_mxn ELSE 0 END) as compras_pendientes,
                    SUM(CASE WHEN c2.fecha_pago_factura IS NULL THEN 1 ELSE 0 END) as compras_pendientes_count,
                    SUM(c2.total_con_iva_mxn) / NULLIF(COUNT(DISTINCT c2.proveedor), 0) as promedio_por_proveedor,
                    COUNT(DISTINCT c2.proveedor) as proveedores_unicos
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
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
                    COUNT(DISTINCT c2m.material_codigo) as materiales_unicos,
                    ROUND(AVG(c2.dias_transporte)::numeric, 1) as dias_transporte_promedio,
                    ROUND(AVG(c2.dias_puerto_planta)::numeric, 1) as dias_puerto_planta_promedio
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
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
            precio_field = 'pu_usd' if moneda == 'USD' else 'pu_mxn'
            
            query = f"""
                SELECT 
                    DATE_TRUNC('month', c2.fecha_pedido) as mes,
                    AVG(c2m.{precio_field}) as precio_promedio,
                    MIN(c2m.{precio_field}) as precio_min,
                    MAX(c2m.{precio_field}) as precio_max
                FROM compras_v2 c2
                LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
                WHERE c2.fecha_pedido IS NOT NULL 
                AND c2m.{precio_field} IS NOT NULL 
                AND c2m.{precio_field} > 0
            """
            
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('material'):
                    query += " AND c2m.material_codigo ILIKE %s"
                    params.append(f"%{filtros['material']}%")
                
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
        """Obtiene flujo de pagos por semana con columnas apiladas - Versión corregida"""
        conn = self.get_connection()
        if not conn:
            return {'labels': [], 'datasets': [], 'titulo': 'Sin datos'}
        
        try:
            cursor = conn.cursor()
            
            # Query corregida para cálculos reales de flujo de pagos
            # Basada en el ejemplo IMI 1886
            query = """
                SELECT 
                    DATE_TRUNC('week', c2.fecha_pedido) as semana_pedido,
                    -- Liquidaciones: total_con_iva_mxn - anticipo_monto (convertido a la moneda solicitada)
                    CASE 
                        WHEN %s = 'MXN' THEN 
                            COALESCE(c2.total_con_iva_mxn, 0) - COALESCE(c2.anticipo_monto, 0)
                        WHEN c2.moneda = 'USD' THEN 
                            -- Para USD, convertir total_con_iva_mxn a USD y restar anticipo_monto convertido
                            (COALESCE(c2.total_con_iva_mxn, 0) - COALESCE(c2.anticipo_monto, 0)) / 
                            NULLIF(NULLIF(COALESCE(c2.tipo_cambio_real, c2.tipo_cambio_estimado), 0), 1.0)
                        ELSE 0
                    END as liquidaciones,
                    -- Gastos de importación: calcular como porcentaje del total_con_iva_mxn
                    CASE 
                        WHEN %s = 'MXN' THEN 
                            CASE 
                                WHEN c2.porcentaje_gastos_importacion > 0 THEN 
                                    COALESCE(c2.total_con_iva_mxn, 0) * (c2.porcentaje_gastos_importacion / 100.0)
                                ELSE COALESCE(c2.gastos_importacion_mxn, 0)
                            END
                        WHEN c2.moneda = 'USD' THEN 
                            CASE 
                                WHEN c2.porcentaje_gastos_importacion > 0 THEN 
                                    (COALESCE(c2.total_con_iva_mxn, 0) * (c2.porcentaje_gastos_importacion / 100.0)) / 
                                    NULLIF(NULLIF(COALESCE(c2.tipo_cambio_real, c2.tipo_cambio_estimado), 0), 1.0)
                                ELSE COALESCE(c2.gastos_importacion_divisa, 0)
                            END
                        ELSE 0
                    END as gastos_importacion,
                    -- Anticipo: usar anticipo_monto (convertido según moneda solicitada)
                    CASE 
                        WHEN %s = 'MXN' THEN COALESCE(c2.anticipo_monto, 0)
                        WHEN c2.moneda = 'USD' THEN 
                            COALESCE(c2.anticipo_monto, 0) / 
                            NULLIF(NULLIF(COALESCE(c2.tipo_cambio_real, c2.tipo_cambio_estimado), 0), 1.0)
                        ELSE 0
                    END as anticipo
                FROM compras_v2 c2
                WHERE c2.fecha_pedido IS NOT NULL
            """
            
            params = [moneda, moneda, moneda]  # Parámetros para los CASE statements
            
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
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            cursor.close()
            
            if not resultados:
                return {'labels': [], 'datasets': [], 'titulo': 'Sin datos'}
            
            # Procesar resultados por semana (simplificado)
            semanas_data = {}
            
            for row in resultados:
                semana_pedido = row['semana_pedido']
                liquidaciones = float(row['liquidaciones']) if row['liquidaciones'] else 0
                gastos_importacion = float(row['gastos_importacion']) if row['gastos_importacion'] else 0
                anticipo = float(row['anticipo']) if row['anticipo'] else 0
                
                # Usar semana de pedido para todos los montos
                if semana_pedido:
                    semana_key = f"Semana {semana_pedido.isocalendar()[1]}"
                    if semana_key not in semanas_data:
                        semanas_data[semana_key] = {'liquidaciones': 0, 'gastos_importacion': 0, 'anticipo': 0}
                    
                    semanas_data[semana_key]['liquidaciones'] += liquidaciones
                    semanas_data[semana_key]['gastos_importacion'] += gastos_importacion
                    semanas_data[semana_key]['anticipo'] += anticipo
            
            # Ordenar semanas y preparar datos
            from datetime import datetime, timedelta
            import locale
            
            # Configurar locale para español
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
                except:
                    pass  # Usar locale por defecto
            
            # Obtener semana actual
            hoy = datetime.now()
            semana_actual = hoy.isocalendar()[1]
            año_actual = hoy.year
            
            # Generar semanas futuras (desde la semana actual hacia adelante)
            semanas_futuras = []
            for i in range(12):  # Mostrar próximas 12 semanas
                semana_num = semana_actual + i
                año_semana = año_actual
                
                # Si la semana excede 52, ajustar al año siguiente
                if semana_num > 52:
                    semana_num = semana_num - 52
                    año_semana = año_actual + 1
                
                # Calcular fecha de inicio de la semana
                # isocalendar() retorna (año, semana, día)
                fecha_inicio_semana = datetime.strptime(f"{año_semana}-W{semana_num:02d}-1", "%Y-W%W-%w")
                
                # Si no funciona el formato anterior, usar una aproximación
                if fecha_inicio_semana.year != año_semana:
                    # Calcular manualmente el lunes de la semana
                    fecha_inicio_semana = datetime.strptime(f"{año_semana}-W{semana_num:02d}-1", "%Y-W%U-%w")
                
                # Formatear como S## dd-mmm
                dia_mes = fecha_inicio_semana.strftime("%d")
                mes_abr = fecha_inicio_semana.strftime("%b")
                etiqueta_semana = f"S{semana_num:02d} {dia_mes}-{mes_abr}"
                
                semanas_futuras.append({
                    'etiqueta': etiqueta_semana,
                    'semana_num': semana_num,
                    'fecha_inicio': fecha_inicio_semana,
                    'datos': semanas_data.get(f"Semana {semana_num}", {'liquidaciones': 0, 'gastos_importacion': 0, 'anticipo': 0})
                })
            
            # Ordenar por número de semana
            semanas_futuras.sort(key=lambda x: x['semana_num'])
            
            # Extraer datos para el gráfico
            etiquetas = [semana['etiqueta'] for semana in semanas_futuras]
            liquidaciones_data = [semana['datos']['liquidaciones'] for semana in semanas_futuras]
            gastos_data = [semana['datos']['gastos_importacion'] for semana in semanas_futuras]
            anticipos_data = [semana['datos']['anticipo'] for semana in semanas_futuras]
            
            titulo = "Flujo de Pagos Semanal"
            
            return {
                'labels': etiquetas,
                'datasets': [
                    {
                        'label': 'Liquidaciones',
                        'data': liquidaciones_data,
                        'backgroundColor': '#10b981'
                    },
                    {
                        'label': 'Gastos de Importación',
                        'data': gastos_data,
                        'backgroundColor': '#f59e0b'
                    },
                    {
                        'label': 'Anticipo',
                        'data': anticipos_data,
                        'backgroundColor': '#3b82f6'
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
    
    def get_compras_por_material(self, limite: int = 10, filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene compras agrupadas por material - Versión corregida"""
        conn = self.get_connection()
        if not conn:
            return {'labels': [], 'data': [], 'titulo': 'Sin datos'}
        
        try:
            cursor = conn.cursor()
            
            # Query para obtener materiales con más compras
            query = """
                SELECT 
                    c2m.material_codigo,
                    SUM(c2m.kg) as total_kg,
                    SUM(c2m.costo_total_con_iva) as total_costo,
                    COUNT(DISTINCT c2.imi) as total_compras,
                    AVG(c2m.pu_mxn) as precio_promedio_kg
                FROM compras_v2_materiales c2m
                JOIN compras_v2 c2 ON c2m.compra_imi = c2.imi
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
                GROUP BY c2m.material_codigo
                ORDER BY total_costo DESC
                LIMIT %s
            """
            params.append(limite)
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            cursor.close()
            
            if not resultados:
                return {'labels': [], 'data': [], 'data_kg': [], 'titulo': 'Sin datos'}
            
            # Procesar resultados
            labels = []
            data_costo = []
            data_kg = []
            
            for row in resultados:
                material_codigo = row['material_codigo']
                total_costo = float(row['total_costo']) if row['total_costo'] else 0
                total_kg = float(row['total_kg']) if row['total_kg'] else 0
                
                # Crear etiqueta solo con código de material
                etiqueta = f"{material_codigo}"
                
                labels.append(etiqueta)
                data_costo.append(total_costo)
                data_kg.append(total_kg)
            
            return {
                'labels': labels,
                'data': data_costo,  # Mantener compatibilidad
                'data_kg': data_kg,  # Nuevos datos de kg
                'titulo': f'Top {len(labels)} Materiales'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo compras por material: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'labels': [], 'data': [], 'data_kg': [], 'titulo': 'Sin datos'}
    
    def __del__(self):
        """Destructor para cerrar conexión"""
        self.close_connection()
