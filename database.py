"""
Configuración de base de datos PostgreSQL/SQLite para Immermex Dashboard
Soporte para persistencia en la nube
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./immermex.db")

# Validar URL de base de datos
if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///./immermex.db"

# Verificar si hay una URL PostgreSQL directa configurada
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
if POSTGRES_URL and POSTGRES_URL.startswith("postgresql://"):
    DATABASE_URL = POSTGRES_URL
    logger.info("Usando URL PostgreSQL directa de POSTGRES_URL")
elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_PASSWORD"):
    # Construir URL PostgreSQL desde variables de Supabase
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_PASSWORD")
        
        # Extraer project ref de la URL de Supabase
        # Formato: https://your-project-ref.supabase.co
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
            # Usar pooler de Supabase para IPv4 compatibility
            DATABASE_URL = f"postgresql://postgres.{project_ref}:{supabase_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
            logger.info(f"Construida URL PostgreSQL desde Supabase pooler: aws-1-us-west-1.pooler.supabase.com")
        else:
            logger.warning("Formato de SUPABASE_URL no reconocido, usando SQLite")
            DATABASE_URL = "sqlite:///./immermex.db"
    except Exception as e:
        logger.error(f"Error construyendo URL de Supabase: {str(e)}")
        DATABASE_URL = "sqlite:///./immermex.db"
elif DATABASE_URL.startswith("https://supabase.com/"):
    # Extraer información de la URL de Supabase
    # Formato: https://supabase.com/project/ref/rest/v1/
    # Convertir a: postgresql://postgres:[password]@db.ref.supabase.co:5432/postgres
    try:
        parts = DATABASE_URL.split('/')
        if len(parts) >= 4:
            project_ref = parts[4]  # El ref del proyecto
            # Construir URL PostgreSQL (necesitará password en variable separada)
            postgres_password = os.getenv("SUPABASE_PASSWORD", "")
            if postgres_password:
                # Usar pooler de Supabase para IPv4 compatibility
                DATABASE_URL = f"postgresql://postgres.{project_ref}:{postgres_password}@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
                logger.info(f"Convertida URL de Supabase a PostgreSQL pooler: aws-1-us-west-1.pooler.supabase.com")
            else:
                logger.warning("SUPABASE_PASSWORD no configurada, usando SQLite")
                DATABASE_URL = "sqlite:///./immermex.db"
    except Exception as e:
        logger.error(f"Error convirtiendo URL de Supabase: {str(e)}")
        DATABASE_URL = "sqlite:///./immermex.db"

# Configuración específica para Supabase/PostgreSQL en la nube
if DATABASE_URL.startswith("postgresql://"):
    try:
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
    except Exception as e:
        logger.error(f"Error creando engine PostgreSQL: {str(e)}")
        logger.info("Fallando a SQLite local")
        DATABASE_URL = "sqlite:///./immermex.db"
        engine = create_engine(DATABASE_URL, echo=False)
    else:
        logger.info("Conectando a Supabase/PostgreSQL en la nube")
else:
    # Para SQLite local (desarrollo)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    logger.info("Conectando a SQLite local")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Facturacion(Base):
    __tablename__ = "facturacion"
    
    folio_factura = Column(Integer, primary_key=True, index=True)
    serie_factura = Column(String, index=True)
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
    folio_factura = Column(Integer, index=True)
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

class PedidosCompras(Base):
    __tablename__ = "pedidos_compras"
    
    id = Column(Integer, primary_key=True, index=True)
    compra_imi = Column(Integer, index=True)
    folio_factura = Column(Integer, index=True)
    material_codigo = Column(String, index=True)
    kg = Column(Float, default=0.0)
    precio_unitario = Column(Float, default=0.0)
    importe_sin_iva = Column(Float, default=0.0)
    importe_con_iva = Column(Float, default=0.0)
    dias_credito = Column(Integer, default=30)
    fecha_factura = Column(DateTime, index=True)
    fecha_pago = Column(DateTime)
    archivo_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices optimizados para consultas frecuentes
    __table_args__ = (
        Index('idx_pedidos_compras_fecha', 'fecha_factura'),
        Index('idx_pedidos_compras_material', 'material_codigo'),
        Index('idx_pedidos_compras_folio', 'folio_factura'),
        Index('idx_pedidos_compras_archivo', 'archivo_id'),
        Index('idx_pedidos_compras_compra_imi', 'compra_imi'),
    )


class Proveedores(Base):
    __tablename__ = "proveedores"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    promedio_dias_produccion = Column(Float, default=0.0)
    promedio_dias_transporte_maritimo = Column(Float, default=0.0)
    pais_origen = Column(String)
    contacto = Column(String)
    email = Column(String)
    telefono = Column(String)
    direccion = Column(Text)
    notas = Column(Text)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_proveedor_nombre', 'nombre'),
        Index('idx_proveedor_activo', 'activo'),
    )

class ComprasV2(Base):
    __tablename__ = "compras_v2"

    id = Column(Integer, primary_key=True, index=True)
    imi = Column(String, unique=True, index=True)
    proveedor = Column(String, index=True)
    fecha_pedido = Column(Date)
    puerto_origen = Column(String)
    fecha_salida_estimada = Column(Date)
    fecha_arribo_estimada = Column(Date)
    fecha_planta_estimada = Column(Date)
    moneda = Column(String, default='USD')
    dias_credito = Column(Integer, default=0)
    anticipo_pct = Column(Float, default=0.0)  # NUMERIC(5,4)
    anticipo_monto = Column(Float, default=0.0)
    fecha_anticipo = Column(Date)
    fecha_pago_factura = Column(Date)
    tipo_cambio_estimado = Column(Float, default=0.0)
    tipo_cambio_real = Column(Float, default=0.0)
    gastos_importacion_divisa = Column(Float, default=0.0)
    gastos_importacion_mxn = Column(Float, default=0.0)
    gastos_importacion_estimado = Column(Float, default=0.0)
    porcentaje_gastos_importacion = Column(Float, default=0.0)  # NUMERIC(5,4)
    iva_monto_mxn = Column(Float, default=0.0)
    total_con_iva_mxn = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con materiales
    materiales = relationship("ComprasV2Materiales", back_populates="compra")

    __table_args__ = (
        Index('idx_compras_v2_imi', 'imi'),
        Index('idx_compras_v2_proveedor', 'proveedor'),
        Index('idx_compras_v2_fecha_pedido', 'fecha_pedido'),
    )

class ComprasV2Materiales(Base):
    __tablename__ = "compras_v2_materiales"

    id = Column(Integer, primary_key=True, index=True)
    compra_id = Column(Integer, ForeignKey('compras_v2.id'), index=True)
    material_codigo = Column(String, index=True)
    kg = Column(Float, default=0.0)
    pu_divisa = Column(Float, default=0.0)
    pu_mxn = Column(Float, default=0.0)
    pu_usd = Column(Float, default=0.0)
    costo_total_divisa = Column(Float, default=0.0)
    costo_total_mxn = Column(Float, default=0.0)
    pu_mxn_importacion = Column(Float, default=0.0)
    costo_total_mxn_imporacion = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    costo_total_con_iva = Column(Float, default=0.0)
    compra_imi = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con compra
    compra = relationship("ComprasV2", back_populates="materiales")

    __table_args__ = (
        Index('idx_compras_v2_mat_compra_id', 'compra_id'),
        Index('idx_compras_v2_mat_material', 'material_codigo'),
        Index('idx_compras_v2_mat_imi', 'compra_imi'),
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

def get_or_create_proveedor(db, nombre_proveedor: str):
    """Obtiene o crea un proveedor"""
    proveedor = db.query(Proveedores).filter(Proveedores.nombre == nombre_proveedor).first()
    if not proveedor:
        proveedor = Proveedores(
            nombre=nombre_proveedor,
            activo=True
        )
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
    return proveedor

def update_proveedor_averages(db, nombre_proveedor: str, dias_produccion: float = None, dias_transporte: float = None):
    """Actualiza los promedios de días de producción y transporte marítimo de un proveedor"""
    try:
        proveedor = db.query(Proveedores).filter(Proveedores.nombre == nombre_proveedor).first()
        if proveedor:
            if dias_produccion is not None:
                proveedor.promedio_dias_produccion = dias_produccion
            if dias_transporte is not None:
                proveedor.promedio_dias_transporte_maritimo = dias_transporte
            proveedor.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error actualizando promedios del proveedor {nombre_proveedor}: {str(e)}")
        db.rollback()
        return False

def get_proveedor_stats(db, nombre_proveedor: str):
    """Obtiene estadísticas de un proveedor específico"""
    try:
        proveedor = db.query(Proveedores).filter(Proveedores.nombre == nombre_proveedor).first()
        if not proveedor:
            return None
        
        # Obtener estadísticas de compras
        compras_stats = db.query(Compras).filter(Compras.proveedor == nombre_proveedor).all()
        
        return {
            "proveedor": {
                "id": proveedor.id,
                "nombre": proveedor.nombre,
                "promedio_dias_produccion": proveedor.promedio_dias_produccion,
                "promedio_dias_transporte_maritimo": proveedor.promedio_dias_transporte_maritimo,
                "pais_origen": proveedor.pais_origen,
                "activo": proveedor.activo,
                "created_at": proveedor.created_at,
                "updated_at": proveedor.updated_at
            },
            "estadisticas": {
                "total_compras": len(compras_stats),
                "total_monto": sum(compra.total for compra in compras_stats if compra.total),
                "ultima_compra": max((compra.fecha_compra for compra in compras_stats if compra.fecha_compra), default=None)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del proveedor {nombre_proveedor}: {str(e)}")
        return None

# Inicializar base de datos
def init_db():
    try:
        create_tables()
        logger.info("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        return False
