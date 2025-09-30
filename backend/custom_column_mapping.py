"""
Mapeo de columnas personalizado para archivo de compras
Archivo analizado: ../docs/IMM-Compras de  importacion (Compartido).xlsx
"""

# Mapeo encontrado automaticamente
AUTO_MAPPING = {
}

# Columnas no mapeadas - revisar manualmente
UNMAPPED_COLUMNS = [
    'CONCENTRADOS DE PEDIMENTOS',
    'Unnamed: 1',
    'Unnamed: 2',
    'Unnamed: 3',
    'Unnamed: 4',
    'Unnamed: 5',
    'Unnamed: 6',
    'Unnamed: 7',
    'Unnamed: 8',
    'Unnamed: 9',
    'Unnamed: 10',
    'Unnamed: 11',
    'Unnamed: 12',
    'Unnamed: 13',
    'Unnamed: 14',
    'Unnamed: 15',
    'Unnamed: 16',
    'Unnamed: 17',
    'Unnamed: 18',
    'Unnamed: 19',
    'Unnamed: 20',
    'Unnamed: 21',
    'Unnamed: 22',
    'Unnamed: 23',
    'Unnamed: 24',
    'Unnamed: 25',
    'Unnamed: 26',
    'Unnamed: 27',
    'Unnamed: 28',
    'Unnamed: 29',
    'Unnamed: 30',
    'Unnamed: 31',
    'Unnamed: 32',
    'Unnamed: 33',
    'Unnamed: 34',
    'Unnamed: 35',
    'Unnamed: 36',
    'Unnamed: 37',
    'Unnamed: 38',
    'Unnamed: 39',
]

# Mapeo manual adicional (completar segun necesidad)
MANUAL_MAPPING = {
    # Ejemplo: 'campo_personalizado': 'columna_excel',
}

# Mapeo final combinado
FINAL_MAPPING = {**AUTO_MAPPING, **MANUAL_MAPPING}
