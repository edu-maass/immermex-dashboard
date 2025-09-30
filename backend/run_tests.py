#!/usr/bin/env python3
"""
Script para ejecutar tests del backend
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{'='*50}")
    print(f"Ejecutando: {description}")
    print(f"Comando: {command}")
    print(f"{'='*50}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Error en: {description}")
        return False
    else:
        print(f"✅ Éxito en: {description}")
        return True

def main():
    """Función principal"""
    print("🧪 Ejecutando tests del backend Immermex Dashboard")
    
    # Cambiar al directorio del backend
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("main_with_db.py"):
        print("❌ Error: No se encontró main_with_db.py. Asegúrate de estar en el directorio backend/")
        sys.exit(1)
    
    # Instalar dependencias de testing si no están instaladas
    print("\n📦 Verificando dependencias de testing...")
    try:
        import pytest
        import pytest_cov
        print("✅ Dependencias de testing ya están instaladas")
    except ImportError:
        print("📥 Instalando dependencias de testing...")
        if not run_command("pip install -r requirements-test.txt", "Instalación de dependencias de testing"):
            print("❌ Error instalando dependencias de testing")
            sys.exit(1)
    
    # Ejecutar tests
    tests_passed = True
    
    # 1. Tests unitarios básicos
    if not run_command("pytest tests/test_api.py -v", "Tests de API"):
        tests_passed = False
    
    # 2. Tests de base de datos
    if not run_command("pytest tests/test_database.py -v", "Tests de Base de Datos"):
        tests_passed = False
    
    # 3. Tests de procesamiento de datos
    if not run_command("pytest tests/test_data_processing.py -v", "Tests de Procesamiento de Datos"):
        tests_passed = False
    
    # 4. Tests con coverage
    if not run_command("pytest --cov=. --cov-report=term-missing", "Tests con Coverage"):
        tests_passed = False
    
    # 5. Tests de linting (opcional)
    print(f"\n{'='*50}")
    print("Ejecutando: Linting (opcional)")
    print(f"{'='*50}")
    
    try:
        # Black (formatter)
        run_command("black --check .", "Verificación de formato con Black")
        
        # Flake8 (linter)
        run_command("flake8 .", "Verificación de estilo con Flake8")
        
        # MyPy (type checking)
        run_command("mypy .", "Verificación de tipos con MyPy")
        
    except FileNotFoundError as e:
        print(f"⚠️  Herramienta de linting no encontrada: {e}")
        print("Puedes instalarla con: pip install black flake8 mypy")
    
    # Resumen final
    print(f"\n{'='*50}")
    if tests_passed:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        print("✅ El sistema está listo para deployment")
    else:
        print("❌ Algunos tests fallaron")
        print("🔧 Revisa los errores arriba y corrige los problemas")
    print(f"{'='*50}")
    
    return 0 if tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
