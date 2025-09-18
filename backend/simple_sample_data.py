#!/usr/bin/env python3
"""
Script simple para crear datos de prueba sin dependencias externas
"""

import csv
import random
from datetime import datetime, timedelta

def create_simple_sample_data():
    """Crea datos de muestra simples para probar el dashboard"""
    
    # Configurar semilla para datos reproducibles
    random.seed(42)
    
    # Fechas base
    start_date = datetime(2024, 1, 1)
    
    # Clientes de muestra
    clientes = [
        "ACME Corp", "Tech Solutions", "Industrial Supplies", "Manufacturing Co",
        "Global Systems", "Premium Materials", "Quality Products", "Advanced Tech"
    ]
    
    # Agentes
    agentes = ["Juan Pérez", "María García", "Carlos López", "Ana Martínez"]
    
    # Materiales
    materiales = [
        "Acero Inoxidable 304", "Aluminio 6061", "Cobre C11000", "Bronce C83600",
        "Titanio Grade 2", "Níquel 200", "Zinc Z1", "Plomo 99.9%"
    ]
    
    # Generar datos de facturación
    facturacion_data = []
    for i in range(100):  # 100 facturas
        fecha = start_date + timedelta(days=random.randint(0, 300))
        cliente = random.choice(clientes)
        agente = random.choice(agentes)
        material = random.choice(materiales)
        
        cantidad = round(random.uniform(100, 2000), 2)
        precio_unitario = round(random.uniform(50, 300), 2)
        subtotal = cantidad * precio_unitario
        iva = subtotal * 0.16
        total = subtotal + iva
        
        facturacion_data.append({
            'Folio': f'FAC-{i+1:04d}',
            'Fecha': fecha.strftime('%Y-%m-%d'),
            'Cliente': cliente,
            'Agente': agente,
            'Importe': total,
            'UUID': f'uuid-{i+1:06d}-{random.randint(1000, 9999)}',
            'Pedido': f'PED-{i+1:04d}',
            'Material': material,
            'Cantidad': cantidad,
            'Precio Unitario': precio_unitario,
            'Subtotal': subtotal,
            'IVA': iva,
            'Total': total
        })
    
    # Generar datos de cobranza (70% de las facturas cobradas)
    cobranza_data = []
    facturas_cobradas = random.sample(facturacion_data, int(len(facturacion_data) * 0.7))
    
    for factura in facturas_cobradas:
        fecha_cobro = datetime.strptime(factura['Fecha'], '%Y-%m-%d') + timedelta(days=random.randint(1, 45))
        cobranza_data.append({
            'Folio': factura['Folio'],
            'Fecha Cobro': fecha_cobro.strftime('%Y-%m-%d'),
            'Cliente': factura['Cliente'],
            'Importe Cobrado': factura['Total'],
            'Forma Pago': random.choice(['Transferencia', 'Efectivo', 'Cheque']),
            'Referencia': f'REF-{random.randint(100000, 999999)}',
            'UUID': factura['UUID']
        })
    
    # Generar CFDIs relacionados (anticipos)
    cfdi_data = []
    for i in range(20):  # 20 anticipos
        cliente = random.choice(clientes)
        fecha = start_date + timedelta(days=random.randint(0, 300))
        importe = round(random.uniform(10000, 50000), 2)
        
        cfdi_data.append({
            'UUID': f'anticipo-{i+1:04d}-{random.randint(1000, 9999)}',
            'Tipo': 'Anticipo',
            'Fecha': fecha.strftime('%Y-%m-%d'),
            'Cliente': cliente,
            'Importe': importe,
            'Folio Relacionado': f'FAC-{random.randint(1, 100):04d}',
            'Concepto': f'Anticipo para {cliente}'
        })
    
    # Generar datos de inventario
    inventario_data = []
    for material in materiales:
        cantidad_inicial = random.randint(1000, 5000)
        entradas = random.randint(200, 2000)
        salidas = random.randint(300, 1500)
        cantidad_final = cantidad_inicial + entradas - salidas
        costo_unitario = round(random.uniform(20, 150), 2)
        valor_inventario = cantidad_final * costo_unitario
        
        inventario_data.append({
            'Material': material,
            'Cantidad Inicial': cantidad_inicial,
            'Entradas': entradas,
            'Salidas': salidas,
            'Cantidad Final': cantidad_final,
            'Costo Unitario': costo_unitario,
            'Valor Inventario': valor_inventario
        })
    
    # Crear archivos CSV (más simple que Excel)
    with open('facturacion.csv', 'w', newline='', encoding='utf-8') as f:
        if facturacion_data:
            writer = csv.DictWriter(f, fieldnames=facturacion_data[0].keys())
            writer.writeheader()
            writer.writerows(facturacion_data)
    
    with open('cobranza.csv', 'w', newline='', encoding='utf-8') as f:
        if cobranza_data:
            writer = csv.DictWriter(f, fieldnames=cobranza_data[0].keys())
            writer.writeheader()
            writer.writerows(cobranza_data)
    
    with open('cfdi_relacionados.csv', 'w', newline='', encoding='utf-8') as f:
        if cfdi_data:
            writer = csv.DictWriter(f, fieldnames=cfdi_data[0].keys())
            writer.writeheader()
            writer.writerows(cfdi_data)
    
    with open('inventario.csv', 'w', newline='', encoding='utf-8') as f:
        if inventario_data:
            writer = csv.DictWriter(f, fieldnames=inventario_data[0].keys())
            writer.writeheader()
            writer.writerows(inventario_data)
    
    print("✅ Datos de prueba creados exitosamente:")
    print(f"   - Facturación: {len(facturacion_data)} registros")
    print(f"   - Cobranza: {len(cobranza_data)} registros")
    print(f"   - CFDIs relacionados: {len(cfdi_data)} registros")
    print(f"   - Inventario: {len(inventario_data)} registros")
    print("   - Archivos CSV creados en el directorio backend/")
    
    return True

if __name__ == "__main__":
    create_simple_sample_data()
