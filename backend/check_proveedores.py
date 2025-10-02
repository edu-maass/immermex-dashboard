#!/usr/bin/env python3
"""
Script temporal para verificar datos de proveedores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from database import Compras
from sqlalchemy import func

def check_proveedores():
    db = SessionLocal()
    try:
        # Verificar si hay datos de compras
        total_compras = db.query(func.count(Compras.id)).scalar()
        print(f'Total de compras: {total_compras}')
        
        if total_compras == 0:
            print("No hay datos de compras en la base de datos")
            return
        
        # Verificar proveedores únicos
        proveedores = db.query(Compras.proveedor).filter(Compras.proveedor.isnot(None)).distinct().all()
        print(f'Proveedores únicos: {len(proveedores)}')
        
        if len(proveedores) == 0:
            print("No hay proveedores en la base de datos")
            # Mostrar algunos registros para ver qué hay
            sample_compras = db.query(Compras).limit(3).all()
            print("Muestra de compras:")
            for compra in sample_compras:
                print(f"  - ID: {compra.id}, Proveedor: '{compra.proveedor}', Concepto: '{compra.concepto}'")
        else:
            print("Proveedores encontrados:")
            for p in proveedores:
                print(f'  - {p[0]}')
        
        # Verificar si hay datos con proveedor no nulo
        compras_con_proveedor = db.query(func.count(Compras.id)).filter(Compras.proveedor.isnot(None)).scalar()
        print(f'Compras con proveedor: {compras_con_proveedor}')
        
    finally:
        db.close()

if __name__ == "__main__":
    check_proveedores()
