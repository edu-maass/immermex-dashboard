#!/usr/bin/env python3
"""
Script para crear datos de prueba para el dashboard de Immermex
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def create_sample_data():
    """Crea datos de muestra para probar el dashboard"""
    
    # Configurar semilla para datos reproducibles
    np.random.seed(42)
    random.seed(42)
    
    # Fechas base
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    # Clientes de muestra
    clientes = [
        "ACME Corp", "Tech Solutions", "Industrial Supplies", "Manufacturing Co",
        "Global Systems", "Premium Materials", "Quality Products", "Advanced Tech",
        "Enterprise Solutions", "Innovation Labs", "Smart Industries", "Future Corp"
    ]
    
    # Agentes
    agentes = ["Juan Pérez", "María García", "Carlos López", "Ana Martínez", "Luis Rodríguez"]
    
    # Materiales
    materiales = [
        "Acero Inoxidable 304", "Aluminio 6061", "Cobre C11000", "Bronce C83600",
        "Titanio Grade 2", "Níquel 200", "Zinc Z1", "Plomo 99.9%",
        "Estaño 99.9%", "Magnesio AZ31B", "Cromo 99.9%", "Molibdeno 99.9%"
    ]
    
    # Generar datos de facturación
    facturacion_data = []
    for i in range(500):  # 500 facturas
        fecha = start_date + timedelta(days=random.randint(0, 365))
        cliente = random.choice(clientes)
        agente = random.choice(agentes)
        material = random.choice(materiales)
        
        cantidad = round(random.uniform(100, 5000), 2)
        precio_unitario = round(random.uniform(50, 500), 2)
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
    
    # Generar datos de cobranza (80% de las facturas cobradas)
    cobranza_data = []
    facturas_cobradas = random.sample(facturacion_data, int(len(facturacion_data) * 0.8))
    
    for factura in facturas_cobradas:
        fecha_cobro = datetime.strptime(factura['Fecha'], '%Y-%m-%d') + timedelta(days=random.randint(1, 60))
        cobranza_data.append({
            'Folio': factura['Folio'],
            'Fecha Cobro': fecha_cobro.strftime('%Y-%m-%d'),
            'Cliente': factura['Cliente'],
            'Importe Cobrado': factura['Total'],
            'Forma Pago': random.choice(['Transferencia', 'Efectivo', 'Cheque', 'Tarjeta']),
            'Referencia': f'REF-{random.randint(100000, 999999)}',
            'UUID': factura['UUID']
        })
    
    # Generar CFDIs relacionados (anticipos)
    cfdi_data = []
    for i in range(50):  # 50 anticipos
        cliente = random.choice(clientes)
        fecha = start_date + timedelta(days=random.randint(0, 365))
        importe = round(random.uniform(10000, 100000), 2)
        
        cfdi_data.append({
            'UUID': f'anticipo-{i+1:04d}-{random.randint(1000, 9999)}',
            'Tipo': 'Anticipo',
            'Fecha': fecha.strftime('%Y-%m-%d'),
            'Cliente': cliente,
            'Importe': importe,
            'Folio Relacionado': f'FAC-{random.randint(1, 500):04d}',
            'Concepto': f'Anticipo para {cliente}'
        })
    
    # Generar datos de inventario
    inventario_data = []
    for material in materiales:
        cantidad_inicial = random.randint(1000, 10000)
        entradas = random.randint(500, 5000)
        salidas = random.randint(800, 4000)
        cantidad_final = cantidad_inicial + entradas - salidas
        costo_unitario = round(random.uniform(20, 200), 2)
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
    
    # Crear archivo Excel
    with pd.ExcelWriter('datos_prueba_immermex.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(facturacion_data).to_excel(writer, sheet_name='facturacion', index=False)
        pd.DataFrame(cobranza_data).to_excel(writer, sheet_name='cobranza', index=False)
        pd.DataFrame(cfdi_data).to_excel(writer, sheet_name='cfdi relacionados', index=False)
        pd.DataFrame(inventario_data).to_excel(writer, sheet_name='1-14 sep', index=False)
    
    print("✅ Datos de prueba creados exitosamente:")
    print(f"   - Facturación: {len(facturacion_data)} registros")
    print(f"   - Cobranza: {len(cobranza_data)} registros")
    print(f"   - CFDIs relacionados: {len(cfdi_data)} registros")
    print(f"   - Inventario: {len(inventario_data)} registros")
    print(f"   - Archivo: datos_prueba_immermex.xlsx")
    
    return 'datos_prueba_immermex.xlsx'

if __name__ == "__main__":
    create_sample_data()
