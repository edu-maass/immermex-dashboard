#!/usr/bin/env python3
"""
Script para extraer texto de los PDFs de documentación de Immermex
"""

try:
    import PyPDF2
    print("PyPDF2 disponible")
except ImportError:
    print("Instalando PyPDF2...")
    import subprocess
    subprocess.check_call(["pip", "install", "PyPDF2"])
    import PyPDF2

def extract_pdf_text(pdf_path):
    """Extrae texto de un archivo PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extrayendo {pdf_path}: {e}")
        return ""

if __name__ == "__main__":
    # Extraer contenido de ambos PDFs
    diccionario_text = extract_pdf_text("Diccionario_Extraccion_Immermex.pdf")
    documentacion_text = extract_pdf_text("Documentacion_Dashboard_Immermex.pdf")
    
    print("=" * 50)
    print("DICCIONARIO EXTRACCIÓN IMMERMEX")
    print("=" * 50)
    print(diccionario_text)
    
    print("\n" + "=" * 50)
    print("DOCUMENTACIÓN DASHBOARD IMMERMEX")
    print("=" * 50)
    print(documentacion_text)
    
    # Guardar en archivos de texto para análisis
    with open("diccionario_extracto.txt", "w", encoding="utf-8") as f:
        f.write(diccionario_text)
    
    with open("documentacion_extracto.txt", "w", encoding="utf-8") as f:
        f.write(documentacion_text)
    
    print("\nArchivos guardados: diccionario_extracto.txt, documentacion_extracto.txt")
