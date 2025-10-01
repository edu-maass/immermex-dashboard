#!/usr/bin/env python3
"""
Script para verificar datos en Supabase
"""

import os
from sqlalchemy import create_engine, text

def check_supabase_data():
    """Verifica los datos en Supabase"""
    
    # Cargar variables de entorno
    with open('production.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    # Conectar a Supabase
    engine = create_engine(os.environ['DATABASE_URL'], connect_args={'sslmode': 'require'})
    
    with engine.connect() as conn:
        # Verificar tablas
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print('Tablas en Supabase:', tables)
        
        # Verificar registros en cada tabla
        for table in ['compras', 'archivos_procesados', 'facturacion', 'cobranza', 'pedidos']:
            if table in tables:
                result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count = result.scalar()
                print(f'{table}: {count} registros')
        
        # Verificar archivos procesados
        if 'archivos_procesados' in tables:
            result = conn.execute(text('SELECT * FROM archivos_procesados ORDER BY fecha_procesamiento DESC LIMIT 5'))
            print('\nUltimos archivos procesados:')
            for row in result:
                print(f'  ID: {row[0]}, Archivo: {row[1]}, Registros: {row[3]}, Estado: {row[4]}')
        
        # Verificar si hay registros de compras
        if 'compras' in tables:
            result = conn.execute(text('SELECT proveedor, concepto, cantidad, total, estado_pago FROM compras LIMIT 5'))
            compras = list(result)
            if compras:
                print('\nRegistros de compras:')
                for compra in compras:
                    print(f'  - {compra[0]}: {compra[1]} | {compra[2]} KG | ${compra[3]} | {compra[4]}')
            else:
                print('\nNo hay registros de compras')

if __name__ == "__main__":
    check_supabase_data()
