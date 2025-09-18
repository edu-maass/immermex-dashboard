"""
Procesador de datos simplificado sin dependencias externas
"""

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class SimpleDataProcessor:
    """
    Procesador de datos simplificado para archivos CSV
    """
    
    def __init__(self):
        self.facturacion_data = []
        self.cobranza_data = []
        self.cfdi_data = []
        self.inventario_data = []
        self.maestro_data = []
        
    def load_csv_file(self, file_path: str) -> List[Dict]:
        """Carga archivo CSV y retorna lista de diccionarios"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append(row)
            print(f"Archivo {file_path} cargado: {len(data)} registros")
            return data
        except Exception as e:
            print(f"Error cargando {file_path}: {e}")
            return []
    
    def normalize_facturacion(self, data: List[Dict]) -> List[Dict]:
        """Normaliza datos de facturación"""
        print("Normalizando datos de facturación...")
        
        normalized = []
        for row in data:
            # Convertir valores numéricos
            try:
                row['Total'] = float(row.get('Total', 0))
                row['Cantidad'] = float(row.get('Cantidad', 0))
                row['Precio Unitario'] = float(row.get('Precio Unitario', 0))
                row['Subtotal'] = float(row.get('Subtotal', 0))
                row['IVA'] = float(row.get('IVA', 0))
                
                # Convertir fecha
                if 'Fecha' in row:
                    try:
                        row['fecha_factura'] = datetime.strptime(row['Fecha'], '%Y-%m-%d')
                    except:
                        row['fecha_factura'] = None
                
                # Agregar campos calculados
                if row['fecha_factura']:
                    row['mes'] = row['fecha_factura'].month
                    row['año'] = row['fecha_factura'].year
                else:
                    row['mes'] = None
                    row['año'] = None
                
                normalized.append(row)
            except Exception as e:
                print(f"Error normalizando fila: {e}")
                continue
        
        self.facturacion_data = normalized
        print(f"Facturación normalizada: {len(normalized)} registros")
        return normalized
    
    def normalize_cobranza(self, data: List[Dict]) -> List[Dict]:
        """Normaliza datos de cobranza"""
        print("Normalizando datos de cobranza...")
        
        normalized = []
        for row in data:
            try:
                row['importe_cobrado'] = float(row.get('Importe Cobrado', 0))
                
                # Convertir fecha
                if 'Fecha Cobro' in row:
                    try:
                        row['fecha_cobro'] = datetime.strptime(row['Fecha Cobro'], '%Y-%m-%d')
                    except:
                        row['fecha_cobro'] = None
                
                normalized.append(row)
            except Exception as e:
                print(f"Error normalizando cobranza: {e}")
                continue
        
        self.cobranza_data = normalized
        print(f"Cobranza normalizada: {len(normalized)} registros")
        return normalized
    
    def normalize_cfdi_relacionados(self, data: List[Dict]) -> List[Dict]:
        """Normaliza datos de CFDIs relacionados"""
        print("Normalizando datos de CFDIs relacionados...")
        
        normalized = []
        for row in data:
            try:
                row['importe_cfdi'] = float(row.get('Importe', 0))
                
                # Convertir fecha
                if 'Fecha' in row:
                    try:
                        row['fecha_cfdi'] = datetime.strptime(row['Fecha'], '%Y-%m-%d')
                    except:
                        row['fecha_cfdi'] = None
                
                normalized.append(row)
            except Exception as e:
                print(f"Error normalizando CFDI: {e}")
                continue
        
        self.cfdi_data = normalized
        print(f"CFDIs normalizados: {len(normalized)} registros")
        return normalized
    
    def normalize_inventario(self, data: List[Dict]) -> List[Dict]:
        """Normaliza datos de inventario"""
        print("Normalizando datos de inventario...")
        
        normalized = []
        for row in data:
            try:
                # Convertir valores numéricos
                row['cantidad_inicial'] = float(row.get('Cantidad Inicial', 0))
                row['entradas'] = float(row.get('Entradas', 0))
                row['salidas'] = float(row.get('Salidas', 0))
                row['cantidad_final'] = float(row.get('Cantidad Final', 0))
                row['costo_unitario'] = float(row.get('Costo Unitario', 0))
                row['valor_inventario'] = float(row.get('Valor Inventario', 0))
                
                normalized.append(row)
            except Exception as e:
                print(f"Error normalizando inventario: {e}")
                continue
        
        self.inventario_data = normalized
        print(f"Inventario normalizado: {len(normalized)} registros")
        return normalized
    
    def create_master_dataframe(self) -> List[Dict]:
        """Crea DataFrame maestro uniendo todas las tablas"""
        print("Creando DataFrame maestro...")
        
        # Empezar con facturación como base
        master = []
        
        for factura in self.facturacion_data:
            # Buscar cobranza correspondiente
            cobranza = None
            for cobro in self.cobranza_data:
                if cobro.get('Folio') == factura.get('Folio'):
                    cobranza = cobro
                    break
            
            # Buscar anticipos
            anticipos = 0
            for cfdi in self.cfdi_data:
                if (cfdi.get('UUID') == factura.get('UUID') and 
                    'anticipo' in cfdi.get('Tipo', '').lower()):
                    anticipos += cfdi.get('importe_cfdi', 0)
            
            # Crear registro maestro
            record = {
                'folio': factura.get('Folio'),
                'fecha_factura': factura.get('fecha_factura'),
                'cliente': factura.get('Cliente'),
                'agente': factura.get('Agente'),
                'total': factura.get('Total', 0),
                'uuid': factura.get('UUID'),
                'numero_pedido': factura.get('Pedido'),
                'material': factura.get('Material'),
                'cantidad_kg': factura.get('Cantidad', 0),
                'precio_unitario': factura.get('Precio Unitario', 0),
                'subtotal': factura.get('Subtotal', 0),
                'iva': factura.get('IVA', 0),
                'mes': factura.get('mes'),
                'año': factura.get('año'),
                'importe_cobrado': cobranza.get('importe_cobrado', 0) if cobranza else 0,
                'fecha_cobro': cobranza.get('fecha_cobro') if cobranza else None,
                'anticipos': anticipos,
                'estado_cobro': 'Cobrado' if cobranza else 'Pendiente'
            }
            
            # Calcular días de vencimiento
            if record['fecha_factura'] and record['fecha_cobro']:
                record['dias_vencimiento'] = (record['fecha_cobro'] - record['fecha_factura']).days
            elif record['fecha_factura']:
                record['dias_vencimiento'] = (datetime.now() - record['fecha_factura']).days
            else:
                record['dias_vencimiento'] = None
            
            master.append(record)
        
        self.maestro_data = master
        print(f"DataFrame maestro creado: {len(master)} registros")
        return master
    
    def calculate_kpis(self) -> Dict:
        """Calcula KPIs principales del dashboard"""
        if not self.maestro_data:
            return {}
        
        # KPIs básicos
        facturacion_total = sum(row.get('total', 0) for row in self.maestro_data)
        cobranza_total = sum(row.get('importe_cobrado', 0) for row in self.maestro_data)
        anticipos_total = sum(row.get('anticipos', 0) for row in self.maestro_data)
        
        # Porcentaje cobrado
        porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
        
        # Aging de cartera
        aging = {'0-30 días': 0, '31-60 días': 0, '61-90 días': 0, '90+ días': 0}
        for row in self.maestro_data:
            if row.get('estado_cobro') == 'Pendiente' and row.get('dias_vencimiento'):
                dias = row['dias_vencimiento']
                if dias <= 30:
                    aging['0-30 días'] += 1
                elif dias <= 60:
                    aging['31-60 días'] += 1
                elif dias <= 90:
                    aging['61-90 días'] += 1
                else:
                    aging['90+ días'] += 1
        
        # Top clientes
        clientes = {}
        for row in self.maestro_data:
            cliente = row.get('cliente', '')
            if cliente:
                clientes[cliente] = clientes.get(cliente, 0) + row.get('total', 0)
        
        top_clientes = dict(sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Consumo por material
        materiales = {}
        for row in self.maestro_data:
            material = row.get('material', '')
            if material:
                materiales[material] = materiales.get(material, 0) + row.get('cantidad_kg', 0)
        
        consumo_material = dict(sorted(materiales.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Rotación de inventario
        if self.inventario_data:
            total_salidas = sum(row.get('salidas', 0) for row in self.inventario_data)
            total_inicial = sum(row.get('cantidad_inicial', 0) for row in self.inventario_data)
            rotacion_inventario = total_salidas / total_inicial if total_inicial > 0 else 0
        else:
            rotacion_inventario = 0
        
        kpis = {
            'facturacion_total': facturacion_total,
            'cobranza_total': cobranza_total,
            'anticipos_total': anticipos_total,
            'porcentaje_cobrado': round(porcentaje_cobrado, 2),
            'rotacion_inventario': round(rotacion_inventario, 2),
            'total_facturas': len(self.maestro_data),
            'clientes_unicos': len(set(row.get('cliente', '') for row in self.maestro_data if row.get('cliente'))),
            'aging_cartera': aging,
            'top_clientes': top_clientes,
            'consumo_material': consumo_material
        }
        
        print("KPIs calculados exitosamente")
        return kpis
    
    def process_files(self) -> Tuple[List[Dict], Dict]:
        """Procesa todos los archivos CSV"""
        print("Iniciando procesamiento de archivos...")
        
        # Cargar archivos
        facturacion = self.load_csv_file('facturacion.csv')
        cobranza = self.load_csv_file('cobranza.csv')
        cfdi = self.load_csv_file('cfdi_relacionados.csv')
        inventario = self.load_csv_file('inventario.csv')
        
        # Normalizar datos
        self.normalize_facturacion(facturacion)
        self.normalize_cobranza(cobranza)
        self.normalize_cfdi_relacionados(cfdi)
        self.normalize_inventario(inventario)
        
        # Crear DataFrame maestro
        master = self.create_master_dataframe()
        
        # Calcular KPIs
        kpis = self.calculate_kpis()
        
        print("Procesamiento completado exitosamente")
        return master, kpis
    
    def export_to_json(self, output_path: str):
        """Exporta datos procesados a JSON"""
        if not self.maestro_data:
            print("No hay datos para exportar")
            return
        
        # Convertir fechas a string para JSON
        data_export = []
        for row in self.maestro_data:
            export_row = row.copy()
            if export_row.get('fecha_factura'):
                export_row['fecha_factura'] = export_row['fecha_factura'].isoformat()
            if export_row.get('fecha_cobro'):
                export_row['fecha_cobro'] = export_row['fecha_cobro'].isoformat()
            data_export.append(export_row)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_export, f, indent=2, ensure_ascii=False)
        
        print(f"Datos exportados a: {output_path}")

# Función de utilidad para uso directo
def process_immermex_files() -> Tuple[List[Dict], Dict]:
    """Función de utilidad para procesar archivos de Immermex"""
    processor = SimpleDataProcessor()
    master_data, kpis = processor.process_files()
    return master_data, kpis

if __name__ == "__main__":
    # Ejemplo de uso
    try:
        master_data, kpis = process_immermex_files()
        print(f"\nProcesamiento exitoso: {len(master_data)} registros")
        print(f"KPIs calculados: {len(kpis)} métricas")
        print(f"\nResumen de KPIs:")
        print(f"  - Facturación total: ${kpis.get('facturacion_total', 0):,.2f}")
        print(f"  - Cobranza total: ${kpis.get('cobranza_total', 0):,.2f}")
        print(f"  - % Cobrado: {kpis.get('porcentaje_cobrado', 0)}%")
        print(f"  - Anticipos: ${kpis.get('anticipos_total', 0):,.2f}")
        print(f"  - Total facturas: {kpis.get('total_facturas', 0)}")
        print(f"  - Clientes únicos: {kpis.get('clientes_unicos', 0)}")
        
    except Exception as e:
        print(f"Error en el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
