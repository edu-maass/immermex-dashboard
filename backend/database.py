"""
Configuración de base de datos PostgreSQL/SQLite para Immermex Dashboard
Soporte para persistencia en la nube
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")

# Configuración específica para Supabase/PostgreSQL en la nube
if DATABASE_URL.startswith("postgresql://"):
    # Para Supabase/PostgreSQL en la nube
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,          # Reducido para Supabase
        max_overflow=10,      # Reducido para Supabase
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,           # Cambiar a True para debug
        connect_args={
            "sslmode": "require"  # SSL requerido para Supabase
        }
    )
    logger.info("Conectando a Supabase/PostgreSQL en la nube")
else:
    # Para SQLite local (desarrollo)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    logger.info("Conectando a SQLite local")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Facturacion(Base):
    __tablename__ = "facturacion"
    
    id = Column(Integer, primary_key=True, index=True)
    serie_factura = Column(String, index=True)
    folio_factura = Column(String, index=True)
    fecha_factura = Column(DateTime, index=True)
    cliente = Column(String, index=True)
    agente = Column(String)
    monto_neto = Column(Float, default=0.0)
    monto_total = Column(Float, default=0.0)
    saldo_pendiente = Column(Float, default=0.0)
    dias_credito = Column(Integer, default=30)
    uuid_factura = Column(String, index=True)
    importe_cobrado = Column(Float, default=0.0)
    fecha_cobro = Column(DateTime)
    dias_cobro = Column(Integer, default=0)
    mes = Column(Integer, index=True)
    año = Column(Integer, index=True)
    archivo_id = Column(Integer, index=True)  # Referencia al archivo que procesó estos datos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices compuestos para mejor performance
    __table_args__ = (
        Index('idx_factura_fecha_cliente', 'fecha_factura', 'cliente'),
        Index('idx_factura_mes_año', 'mes', 'año'),
        Index('idx_factura_uuid_cliente', 'uuid_factura', 'cliente'),
        Index('idx_factura_folio_serie', 'folio_factura', 'serie_factura'),
        Index('idx_factura_archivo_fecha', 'archivo_id', 'fecha_factura'),
    )

class Cobranza(Base):
    __tablename__ = "cobranza"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha_pago = Column(DateTime, index=True)
    serie_pago = Column(String)
    folio_pago = Column(String)
    cliente = Column(String, index=True)
    moneda = Column(String, default="MXN")
    tipo_cambio = Column(Float, default=1.0)
    forma_pago = Column(String)
    parcialidad = Column(Integer, default=1)
    importe_pagado = Column(Float, default=0.0)
    uuid_factura_relacionada = Column(String, index=True)
    archivo_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_cobranza_fecha_cliente', 'fecha_pago', 'cliente'),
        Index('idx_cobranza_uuid', 'uuid_factura_relacionada'),
        Index('idx_cobranza_archivo_fecha', 'archivo_id', 'fecha_pago'),
        Index('idx_cobranza_cliente_importe', 'cliente', 'importe_pagado'),
    )

class CFDIRelacionado(Base):
    __tablename__ = "cfdi_relacionados"
    
    id = Column(Integer, primary_key=True, index=True)
    xml = Column(String, index=True)  # UUID del CFDI
    cliente_receptor = Column(String, index=True)
    tipo_relacion = Column(String, index=True)
    importe_relacion = Column(Float, default=0.0)
    uuid_factura_relacionada = Column(String, index=True)
    archivo_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_cfdi_cliente_tipo', 'cliente_receptor', 'tipo_relacion'),
    )

class Inventario(Base):
    __tablename__ = "inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    material = Column(String, index=True)
    cantidad_inicial = Column(Float)
    entradas = Column(Float)
    salidas = Column(Float)
    cantidad_final = Column(Float)
    costo_unitario = Column(Float)
    valor_inventario = Column(Float)
    mes = Column(Integer)
    año = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class KPI(Base):
    __tablename__ = "kpis"
    
    id = Column(Integer, primary_key=True, index=True)
    mes = Column(Integer)
    año = Column(Integer)
    facturacion_total = Column(Float)
    cobranza_total = Column(Float)
    anticipos_total = Column(Float)
    porcentaje_cobrado = Column(Float)
    rotacion_inventario = Column(Float)
    total_facturas = Column(Integer)
    clientes_unicos = Column(Integer)
    aging_0_30 = Column(Integer)
    aging_31_60 = Column(Integer)
    aging_61_90 = Column(Integer)
    aging_90_plus = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    folio_factura = Column(String, index=True)
    pedido = Column(String, index=True)
    kg = Column(Float, default=0.0)
    precio_unitario = Column(Float, default=0.0)
    importe_sin_iva = Column(Float, default=0.0)
    material = Column(String, index=True)
    dias_credito = Column(Integer, default=30)
    fecha_factura = Column(DateTime)
    fecha_pago = Column(DateTime)
    archivo_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_pedido_material', 'material'),
        Index('idx_pedido_fecha', 'fecha_factura'),
        Index('idx_pedido_folio_archivo', 'folio_factura', 'archivo_id'),
        Index('idx_pedido_fecha_credito', 'fecha_factura', 'dias_credito'),
        Index('idx_pedido_material_fecha', 'material', 'fecha_factura'),
    )

class ArchivoProcesado(Base):
    __tablename__ = "archivos_procesados"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String, unique=True, index=True)
    fecha_procesamiento = Column(DateTime, default=datetime.utcnow)
    registros_procesados = Column(Integer, default=0)
    estado = Column(String, default="procesado")  # 'procesado', 'error', 'en_proceso'
    error_message = Column(Text)
    mes = Column(Integer, index=True)
    año = Column(Integer, index=True)
    hash_archivo = Column(String, unique=True, index=True)  # Para evitar duplicados
    tamaño_archivo = Column(Integer)  # En bytes
    algoritmo_usado = Column(String, default="advanced_cleaning")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_archivo_mes_año', 'mes', 'año'),
        Index('idx_archivo_fecha', 'fecha_procesamiento'),
    )

# Crear todas las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency para obtener sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Funciones de utilidad para gestión de datos
def get_or_create_archivo(db, nombre_archivo: str, hash_archivo: str, tamaño: int):
    """Obtiene o crea un registro de archivo procesado"""
    archivo = db.query(ArchivoProcesado).filter(ArchivoProcesado.hash_archivo == hash_archivo).first()
    if not archivo:
        archivo = ArchivoProcesado(
            nombre_archivo=nombre_archivo,
            hash_archivo=hash_archivo,
            tamaño_archivo=tamaño,
            estado="en_proceso"
        )
        db.add(archivo)
        db.commit()
        db.refresh(archivo)
    return archivo

def clear_data_by_archivo(db, archivo_id: int):
    """Limpia todos los datos asociados a un archivo específico"""
    try:
        # Eliminar datos en orden para evitar problemas de foreign key
        db.query(Pedido).filter(Pedido.archivo_id == archivo_id).delete()
        db.query(CFDIRelacionado).filter(CFDIRelacionado.archivo_id == archivo_id).delete()
        db.query(Cobranza).filter(Cobranza.archivo_id == archivo_id).delete()
        db.query(Facturacion).filter(Facturacion.archivo_id == archivo_id).delete()
        db.commit()
        logger.info(f"Datos limpiados para archivo_id: {archivo_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error limpiando datos: {str(e)}")
        return False

def get_latest_data_summary(db):
    """Obtiene resumen de los datos más recientes"""
    try:
        # Obtener el archivo más reciente
        latest_archivo = db.query(ArchivoProcesado).filter(
            ArchivoProcesado.estado == "procesado"
        ).order_by(ArchivoProcesado.fecha_procesamiento.desc()).first()
        
        if not latest_archivo:
            return {
                "has_data": False,
                "message": "No hay datos disponibles"
            }
        
        # Contar registros
        facturas_count = db.query(Facturacion).filter(
            Facturacion.archivo_id == latest_archivo.id
        ).count()
        
        cobranzas_count = db.query(Cobranza).filter(
            Cobranza.archivo_id == latest_archivo.id
        ).count()
        
        pedidos_count = db.query(Pedido).filter(
            Pedido.archivo_id == latest_archivo.id
        ).count()
        
        return {
            "has_data": True,
            "archivo": {
                "id": latest_archivo.id,
                "nombre": latest_archivo.nombre_archivo,
                "fecha_procesamiento": latest_archivo.fecha_procesamiento,
                "registros_procesados": latest_archivo.registros_procesados
            },
            "conteos": {
                "facturas": facturas_count,
                "cobranzas": cobranzas_count,
                "pedidos": pedidos_count
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo resumen de datos: {str(e)}")
        return {
            "has_data": False,
            "message": f"Error: {str(e)}"
        }

# Inicializar base de datos
def init_db():
    try:
        create_tables()
        logger.info("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        return False
