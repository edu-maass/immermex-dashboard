"""
Servicio especializado para operaciones de pedidos
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from database import Pedido, PedidosCompras, Facturacion
from utils.validators import DataValidator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PedidosService:
    """Servicio para operaciones relacionadas con pedidos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_pedidos(self, pedidos_data: list, archivo_id: int) -> int:
        """Guarda datos de pedidos con asignación automática de fechas y días de crédito"""
        print(f"🔥🔥🔥 === INICIANDO save_pedidos === 🔥🔥🔥")
        print(f"🔥 Total de pedidos recibidos: {len(pedidos_data)}")
        print(f"🔥 Archivo ID: {archivo_id}")
        logger.info(f"=== INICIANDO save_pedidos ===")
        logger.info(f"Total de pedidos recibidos: {len(pedidos_data)}")
        logger.info(f"Archivo ID: {archivo_id}")
        
        count = 0
        
        # Obtener facturas para asignar fechas y días de crédito automáticamente
        facturas = self.db.query(Facturacion).all()
        fechas_por_folio = {}
        dias_credito_por_folio = {}
        
        for factura in facturas:
            if factura.folio_factura:
                folio_limpio = str(factura.folio_factura).strip()
                
                if factura.fecha_factura:
                    fechas_por_folio[folio_limpio] = factura.fecha_factura
                
                if factura.dias_credito is not None:
                    dias_credito_por_folio[folio_limpio] = factura.dias_credito
        
        fechas_asignadas = 0
        dias_credito_asignados = 0
        
        for pedido_data in pedidos_data:
            try:
                # Convertir fechas de forma segura
                fecha_factura = DataValidator.safe_date(pedido_data.get('fecha_factura'))
                fecha_pago = DataValidator.safe_date(pedido_data.get('fecha_pago'))
                
                # Asignar fecha_factura automáticamente si no existe
                if not fecha_factura:
                    folio_factura = pedido_data.get('folio_factura', '')
                    if folio_factura:
                        folio_limpio = str(folio_factura).strip()
                        if folio_limpio in fechas_por_folio:
                            fecha_factura = fechas_por_folio[folio_limpio]
                            fechas_asignadas += 1
                
                # Asignar días de crédito automáticamente
                dias_credito_pedido = DataValidator.safe_int(pedido_data.get('dias_credito', 30))
                folio_factura = pedido_data.get('folio_factura', '')
                
                if folio_factura:
                    folio_limpio = str(folio_factura).strip()
                    if folio_limpio in dias_credito_por_folio:
                        dias_credito_pedido = dias_credito_por_folio[folio_limpio]
                        dias_credito_asignados += 1
                
                # Extraer folio_factura numérico de la cadena completa
                folio_raw = pedido_data.get('folio_factura', '')
                folio_factura_num = self._extract_numeric_folio(folio_raw)
                
                # Ignorar registro si no se puede extraer un folio numérico válido
                if folio_factura_num is None:
                    print(f"[SKIP] Saltando pedido - folio_factura no numerico: '{folio_raw}'")
                    logger.warning(f"Saltando pedido - folio_factura no numérico: '{folio_raw}'")
                    continue
                
                # Obtener IMI de la columna "Pedido"
                imi = DataValidator.safe_int(pedido_data.get('pedido', 0))
                
                # Crear registro en pedidos_compras (tabla optimizada de Supabase)
                pedido_compras = PedidosCompras(
                    compra_imi=imi,  # Usar IMI de la columna "Pedido"
                    folio_factura=folio_factura_num,  # Folio numérico extraído
                    material_codigo=DataValidator.safe_string(pedido_data.get('material', '')),  # Mapear material a material_codigo
                    kg=DataValidator.safe_float(pedido_data.get('kg', 0)),
                    precio_unitario=DataValidator.safe_float(pedido_data.get('precio_unitario', 0)),
                    importe_sin_iva=DataValidator.safe_float(pedido_data.get('importe_sin_iva', 0)),
                    importe_con_iva=DataValidator.safe_float(pedido_data.get('importe_sin_iva', 0)) * 1.16,  # Calcular IVA 16%
                    dias_credito=dias_credito_pedido,
                    fecha_factura=fecha_factura,
                    fecha_pago=fecha_pago,
                    archivo_id=archivo_id
                )
                self.db.add(pedido_compras)
                count += 1
                
                # Log cada 10 pedidos para seguimiento
                if count % 10 == 0:
                    print(f"[PROGRESS] Procesados {count} pedidos...")
                    logger.info(f"Procesados {count} pedidos...")
                    
            except Exception as e:
                print(f"[ERROR] Error guardando pedido: {str(e)}")
                print(f"[ERROR] Datos del pedido que fallo: {pedido_data}")
                logger.error(f"Error guardando pedido: {str(e)}")
                logger.error(f"Datos del pedido que falló: {pedido_data}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        # No hacer commit aquí - dejar que el método principal maneje la transacción
        
        print(f"🔥🔥🔥 === FINALIZANDO save_pedidos === 🔥🔥🔥")
        print(f"🔥 Total de pedidos guardados exitosamente: {count}")
        logger.info(f"=== FINALIZANDO save_pedidos ===")
        logger.info(f"Total de pedidos guardados exitosamente: {count}")
        if fechas_asignadas > 0:
            logger.info(f"Se asignaron automáticamente {fechas_asignadas} fechas de factura a pedidos_compras")
        if dias_credito_asignados > 0:
            logger.info(f"Se asignaron automáticamente {dias_credito_asignados} días de crédito a pedidos_compras")
        
        return count
    
    def _extract_numeric_folio(self, folio_raw: str) -> int:
        """Extrae el número de folio de una cadena que contiene texto adicional
        
        Ejemplo: '29,975 PT.202506124013IM251849/10' -> 29975
        """
        if not folio_raw:
            return None
            
        # Convertir a string y limpiar
        folio_str = str(folio_raw).strip()
        
        # Remover comas y espacios
        folio_str = folio_str.replace(',', '')
        
        # Extraer solo la parte numérica al inicio (antes del primer espacio o caracter no numérico)
        import re
        match = re.match(r'^(\d+)', folio_str)
        
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        
        return None
    
    def _categorize_material(self, material: str) -> str:
        """Categoriza el material basado en su código o nombre"""
        if not material:
            return 'Sin categoría'
        
        material_upper = material.upper()
        
        # Lógica de categorización basada en códigos comunes
        if any(code in material_upper for code in ['ACERO', 'STEEL', 'IRON']):
            return 'Acero'
        elif any(code in material_upper for code in ['ALUMINIO', 'ALUMINIUM', 'AL']):
            return 'Aluminio'
        elif any(code in material_upper for code in ['COBRE', 'COPPER', 'CU']):
            return 'Cobre'
        elif any(code in material_upper for code in ['ZINC', 'ZN']):
            return 'Zinc'
        elif any(code in material_upper for code in ['PLOMO', 'LEAD', 'PB']):
            return 'Plomo'
        elif any(code in material_upper for code in ['NICKEL', 'NI']):
            return 'Níquel'
        else:
            return 'Otros Metales'

    def _subcategorize_material(self, material: str) -> str:
        """Subcategoriza el material con más detalle"""
        if not material:
            return 'Sin subcategoría'
        
        material_upper = material.upper()
        
        # Lógica de subcategorización
        if any(code in material_upper for code in ['LAMINA', 'SHEET', 'PLATE']):
            return 'Lámina'
        elif any(code in material_upper for code in ['VARILLA', 'ROD', 'BAR']):
            return 'Varilla'
        elif any(code in material_upper for code in ['TUBO', 'TUBE', 'PIPE']):
            return 'Tubo'
        elif any(code in material_upper for code in ['ALAMBRE', 'WIRE']):
            return 'Alambre'
        elif any(code in material_upper for code in ['PERFIL', 'PROFILE']):
            return 'Perfil'
        else:
            return 'General'

    def _calculate_trimestre(self, fecha: datetime) -> int:
        """Calcula el trimestre basado en la fecha"""
        if not fecha:
            return None
        return (fecha.month - 1) // 3 + 1

    def get_pedidos_by_filtros(self, filtros: dict = None):
        """Obtiene pedidos aplicando filtros - ahora usa pedidos_compras de Supabase"""
        query = self.db.query(PedidosCompras)
        
        if filtros:
            # Solo aplicar filtro de mes si también hay año seleccionado
            if filtros.get('mes') and filtros.get('año'):
                query = query.filter(func.extract('month', PedidosCompras.fecha_factura) == filtros['mes'])
            elif filtros.get('mes') and not filtros.get('año'):
                # Si hay mes pero no año, ignorar el filtro de mes
                logger.warning("Filtro de mes ignorado porque no hay año seleccionado")
            
            if filtros.get('año'):
                query = query.filter(func.extract('year', PedidosCompras.fecha_factura) == filtros['año'])
            if filtros.get('pedidos'):
                pedidos_list = filtros['pedidos']
                query = query.filter(PedidosCompras.material_codigo.in_(pedidos_list))
        
        return query.all()
    
    def calculate_consumo_material(self, pedidos: list) -> dict:
        """Calcula consumo por material - ahora usa pedidos_compras"""
        materiales_consumo = {}
        pedidos_omitidos = 0
        
        for pedido in pedidos:
            if not pedido.material_codigo or pedido.material_codigo.strip() == "":
                pedidos_omitidos += 1
                continue
            
            material = pedido.material_codigo.strip()
            # Truncar código de material a primeros 7 dígitos para agrupación útil
            if len(material) > 7:
                material = material[:7]
            
            if material not in materiales_consumo:
                materiales_consumo[material] = 0
            materiales_consumo[material] += pedido.kg
        
        # Ordenar y tomar top 10
        sorted_materiales = sorted(materiales_consumo.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_materiales[:10])
    
    def get_folios_pedidos(self, pedidos: list) -> list:
        """Obtiene folios únicos de pedidos - ahora usa pedidos_compras"""
        return list(set(p.folio_factura for p in pedidos if p.folio_factura))

    def get_top_proveedores(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene top proveedores por monto de compras o pedidos"""
        # Si hay filtro de pedidos específico, calcular desde pedidos
        if filtros and filtros.get('pedidos'):
            return self._get_top_proveedores_from_pedidos(limite, filtros)
        else:
            # Usar datos de compras_v2
            return self.db_service.get_top_proveedores_compras_v2(limite, filtros)

    def _get_top_proveedores_from_pedidos(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene top proveedores calculados desde pedidos (lógica legacy)"""
        # Esta es una implementación simplificada - en un escenario real
        # se calcularía desde los pedidos relacionados
        return {"Proveedor Ejemplo": 10000.0}

    def get_top_proveedores_compras_v2(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene top proveedores por monto de compras_v2"""
        return self.db_service.get_top_proveedores_compras_v2(limite, filtros)

    def get_ventas_por_material(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene ventas por material desde pedidos"""
        # Los pedidos representan ventas, no compras
        return self._get_ventas_por_material_from_pedidos(limite, filtros)

    def _get_ventas_por_material_from_pedidos(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene ventas por material calculadas desde pedidos"""
        try:
            from sqlalchemy import func

            # Query para obtener ventas por material desde pedidos
            query = self.db.query(
                Pedido.material,
                func.sum(Pedido.importe_sin_iva).label('total_ventas'),
                func.sum(Pedido.kg).label('total_kg')
            ).filter(
                Pedido.material.isnot(None),
                Pedido.material != ""
            ).group_by(Pedido.material)

            # Aplicar filtros
            if filtros:
                if filtros.get('mes') and filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(
                        extract('month', Pedido.fecha_factura) == filtros['mes'],
                        extract('year', Pedido.fecha_factura) == filtros['año']
                    )
                elif filtros.get('año'):
                    from sqlalchemy import extract
                    query = query.filter(extract('year', Pedido.fecha_factura) == filtros['año'])

            # Ordenar por total de ventas y limitar
            result = query.order_by(func.sum(Pedido.importe_sin_iva).desc()).limit(limite).all()

            return {material: {
                'total_ventas': float(total or 0),
                'total_kg': float(total_kg or 0)
            } for material, total, total_kg in result}

        except Exception as e:
            logger.error(f"Error obteniendo ventas por material desde pedidos: {str(e)}")
            return {}

    def get_compras_por_material_v2(self, limite: int = 10, filtros: dict = None) -> dict:
        """Obtiene compras agrupadas por material en compras_v2"""
        return self.db_service.get_compras_por_material_v2(limite, filtros)

    def get_evolucion_precios_compras_v2(self, material: str = None, moneda: str = 'USD') -> list:
        """Obtiene evolución de precios por período desde compras_v2"""
        result = self.db_service.get_evolucion_precios_compras_v2(material, moneda)
        # Convertir el formato para compatibilidad
        evolucion = []
        for i, label in enumerate(result.get('labels', [])):
            precio = result.get('data', [])[i] if i < len(result.get('data', [])) else 0
            evolucion.append({
                'fecha': label,
                'precio_promedio': precio,
                'precio_min': precio * 0.9,  # Estimación
                'precio_max': precio * 1.1   # Estimación
            })
        return evolucion




