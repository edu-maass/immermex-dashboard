"""
Script para migrar la base de datos a Supabase
Ejecuta este script después de configurar las variables de entorno
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import Base, DATABASE_URL, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Prueba la conexión a Supabase"""
    try:
        # Crear una conexión de prueba
        test_engine = create_engine(DATABASE_URL, echo=True)
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Conexión exitosa a PostgreSQL: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Error conectando a Supabase: {str(e)}")
        return False

def create_tables():
    """Crea todas las tablas en Supabase"""
    try:
        logger.info("Creando tablas en Supabase...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {str(e)}")
        return False

def verify_tables():
    """Verifica que las tablas se crearon correctamente"""
    try:
        with engine.connect() as conn:
            # Verificar que las tablas existen
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            result = conn.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'facturacion', 'cobranza', 'cfdi_relacionados', 
                'inventario', 'pedidos', 'kpis', 'archivos_procesados'
            ]
            
            logger.info("📋 Tablas encontradas:")
            for table in tables:
                status = "✅" if table in expected_tables else "❓"
                logger.info(f"  {status} {table}")
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                logger.warning(f"⚠️  Tablas faltantes: {missing_tables}")
                return False
            else:
                logger.info("✅ Todas las tablas esperadas están presentes")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error verificando tablas: {str(e)}")
        return False

def create_indexes():
    """Crea índices adicionales para optimizar consultas"""
    try:
        with engine.connect() as conn:
            # Índices adicionales para optimización
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_facturacion_uuid ON facturacion(uuid_factura);",
                "CREATE INDEX IF NOT EXISTS idx_cobranza_uuid_rel ON cobranza(uuid_factura_relacionada);",
                "CREATE INDEX IF NOT EXISTS idx_pedidos_material_kg ON pedidos(material, kg);",
                "CREATE INDEX IF NOT EXISTS idx_archivos_fecha ON archivos_procesados(fecha_procesamiento DESC);"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"✅ Índice creado: {index_sql.split()[-1].rstrip(';')}")
                except Exception as e:
                    logger.warning(f"⚠️  Error creando índice: {str(e)}")
            
            conn.commit()
            logger.info("✅ Índices creados exitosamente")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creando índices: {str(e)}")
        return False

def main():
    """Función principal de migración"""
    logger.info("🚀 Iniciando migración a Supabase...")
    
    # Verificar que DATABASE_URL esté configurada
    if not DATABASE_URL or DATABASE_URL == "sqlite:///./immermex.db":
        logger.error("❌ DATABASE_URL no está configurada para Supabase")
        logger.error("Por favor, configura la variable de entorno DATABASE_URL con tu conexión de Supabase")
        logger.error("Ejemplo: postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres")
        sys.exit(1)
    
    # Verificar que sea PostgreSQL
    if not DATABASE_URL.startswith("postgresql://"):
        logger.error("❌ DATABASE_URL debe ser una conexión PostgreSQL para Supabase")
        sys.exit(1)
    
    # Paso 1: Probar conexión
    logger.info("🔍 Paso 1: Probando conexión a Supabase...")
    if not test_connection():
        sys.exit(1)
    
    # Paso 2: Crear tablas
    logger.info("🔧 Paso 2: Creando tablas...")
    if not create_tables():
        sys.exit(1)
    
    # Paso 3: Verificar tablas
    logger.info("✅ Paso 3: Verificando tablas...")
    if not verify_tables():
        sys.exit(1)
    
    # Paso 4: Crear índices
    logger.info("📈 Paso 4: Creando índices de optimización...")
    create_indexes()  # No crítico si falla
    
    logger.info("🎉 ¡Migración a Supabase completada exitosamente!")
    logger.info("💡 Tu dashboard ahora está conectado a la base de datos en la nube")
    logger.info("🔄 Los datos se mantendrán persistentes entre sesiones")

if __name__ == "__main__":
    main()
