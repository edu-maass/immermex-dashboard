#!/usr/bin/env python3
"""
Script alternativo para extraer texto de los PDFs de documentación de Immermex
"""

try:
    import fitz  # PyMuPDF
    print("PyMuPDF disponible")
    pdf_lib = "fitz"
except ImportError:
    try:
        import pdfplumber
        print("pdfplumber disponible")
        pdf_lib = "pdfplumber"
    except ImportError:
        print("Instalando pdfplumber...")
        import subprocess
        subprocess.check_call(["pip", "install", "pdfplumber"])
        import pdfplumber
        pdf_lib = "pdfplumber"

def extract_pdf_text_fitz(pdf_path):
    """Extrae texto usando PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"Error con PyMuPDF en {pdf_path}: {e}")
        return ""

def extract_pdf_text_plumber(pdf_path):
    """Extrae texto usando pdfplumber"""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error con pdfplumber en {pdf_path}: {e}")
        return ""

if __name__ == "__main__":
    # Extraer contenido de ambos PDFs
    if pdf_lib == "fitz":
        diccionario_text = extract_pdf_text_fitz("Diccionario_Extraccion_Immermex.pdf")
        documentacion_text = extract_pdf_text_fitz("Documentacion_Dashboard_Immermex.pdf")
    else:
        diccionario_text = extract_pdf_text_plumber("Diccionario_Extraccion_Immermex.pdf")
        documentacion_text = extract_pdf_text_plumber("Documentacion_Dashboard_Immermex.pdf")
    
    print("=" * 50)
    print("DICCIONARIO EXTRACCIÓN IMMERMEX")
    print("=" * 50)
    print(diccionario_text[:1000] + "..." if len(diccionario_text) > 1000 else diccionario_text)
    
    print("\n" + "=" * 50)
    print("DOCUMENTACIÓN DASHBOARD IMMERMEX")
    print("=" * 50)
    print(documentacion_text[:1000] + "..." if len(documentacion_text) > 1000 else documentacion_text)
    
    # Guardar en archivos de texto para análisis
    with open("diccionario_extracto.txt", "w", encoding="utf-8") as f:
        f.write(diccionario_text)
    
    with open("documentacion_extracto.txt", "w", encoding="utf-8") as f:
        f.write(documentacion_text)
    
    print(f"\nArchivos guardados: diccionario_extracto.txt, documentacion_extracto.txt")
    print(f"Usando librería: {pdf_lib}")
