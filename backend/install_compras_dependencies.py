"""
Script de instalación de dependencias para el sistema de compras
Instala todas las dependencias necesarias para la integración con OneDrive
"""

import subprocess
import sys
import os

def install_package(package):
    """Instala un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {package}: {e}")
        return False

def main():
    """Función principal de instalación"""
    print("="*60)
    print("📦 INSTALADOR DE DEPENDENCIAS - SISTEMA DE COMPRAS")
    print("="*60)
    
    # Dependencias necesarias para OneDrive y compras
    packages = [
        "aiohttp>=3.8.0",           # Para requests asíncronos a OneDrive
        "pandas>=1.5.0",            # Para procesamiento de datos Excel
        "openpyxl>=3.0.0",         # Para leer archivos Excel
        "schedule>=1.2.0",         # Para programación de tareas
        "python-dotenv>=0.19.0",   # Para variables de entorno
        "requests>=2.28.0",        # Para requests HTTP
        "asyncio",                 # Para programación asíncrona
    ]
    
    print(f"📋 Instalando {len(packages)} paquetes...")
    print()
    
    success_count = 0
    failed_packages = []
    
    for package in packages:
        print(f"📦 Instalando {package}...")
        if install_package(package):
            success_count += 1
        else:
            failed_packages.append(package)
        print()
    
    print("="*60)
    print("📊 RESUMEN DE INSTALACIÓN")
    print("="*60)
    
    print(f"✅ Paquetes instalados correctamente: {success_count}")
    print(f"❌ Paquetes con errores: {len(failed_packages)}")
    
    if failed_packages:
        print("\n❌ Paquetes que fallaron:")
        for package in failed_packages:
            print(f"   - {package}")
    
    if len(failed_packages) == 0:
        print("\n🎉 ¡Todas las dependencias se instalaron correctamente!")
        print("✅ El sistema de compras está listo para configurar.")
    else:
        print(f"\n⚠️ {len(failed_packages)} paquetes fallaron. Revisa los errores arriba.")
        print("💡 Puedes intentar instalarlos manualmente:")
        for package in failed_packages:
            print(f"   pip install {package}")
    
    print("\n📚 Próximos pasos:")
    print("1. Configura las variables de entorno en tu archivo .env")
    print("2. Ejecuta: python get_onedrive_token.py")
    print("3. Ejecuta: python create_compras_table.py")
    print("4. Ejecuta: python test_compras_integration.py")
    
    print("="*60)

if __name__ == "__main__":
    main()
