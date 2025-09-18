"""
Configuración de base de datos SQLite para Immermex Dashboard
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")

# Crear engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Facturacion(Base):
    __tablename__ = "facturacion"
    
    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String, index=True)
    fecha_factura = Column(DateTime)
    cliente = Column(String, index=True)
    agente = Column(String)
    importe_factura = Column(Float)
    uuid = Column(String, index=True)
    numero_pedido = Column(String, index=True)
    material = Column(String)
    cantidad_kg = Column(Float)
    precio_unitario = Column(Float)
    subtotal = Column(Float)
    iva = Column(Float)
    total = Column(Float)
    mes = Column(Integer)
    año = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Cobranza(Base):
    __tablename__ = "cobranza"
    
    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String, index=True)
    fecha_cobro = Column(DateTime)
    cliente = Column(String, index=True)
    importe_cobrado = Column(Float)
    forma_pago = Column(String)
    referencia_pago = Column(String)
    uuid = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CFDIRelacionado(Base):
    __tablename__ = "cfdi_relacionados"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, index=True)
    tipo_cfdi = Column(String)
    fecha_cfdi = Column(DateTime)
    cliente = Column(String, index=True)
    importe_cfdi = Column(Float)
    folio_relacionado = Column(String)
    concepto = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

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

class ArchivoProcesado(Base):
    __tablename__ = "archivos_procesados"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String)
    fecha_procesamiento = Column(DateTime, default=datetime.utcnow)
    registros_procesados = Column(Integer)
    estado = Column(String)  # 'procesado', 'error', 'en_proceso'
    error_message = Column(Text)
    mes = Column(Integer)
    año = Column(Integer)

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

# Inicializar base de datos
def init_db():
    create_tables()
    print("Base de datos inicializada correctamente")
