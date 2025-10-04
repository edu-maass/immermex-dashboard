"""
Pedidos endpoints for Immermex Dashboard
Separate file to avoid import issues
"""

from fastapi import HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from database_service import DatabaseService

def add_pedidos_routes(app):
    """Add pedidos endpoints to the FastAPI app"""

    @app.get("/api/pedidos/top-proveedores")
    async def get_top_proveedores(
        limite: int = Query(10, description="Número máximo de proveedores a retornar"),
        mes: Optional[int] = Query(None, description="Filtrar por mes"),
        año: Optional[int] = Query(None, description="Filtrar por año"),
        pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
        db: Session = Depends(get_db)
    ):
        """Obtiene top proveedores por monto de compras"""
        try:
            db_service = DatabaseService(db)

            # Preparar filtros
            filtros = {}
            if mes:
                filtros['mes'] = mes
            if año:
                filtros['año'] = año
            if pedidos:
                filtros['pedidos'] = pedidos

            # Usar el servicio de pedidos para obtener los datos
            pedidos_service = db_service.pedidos_service
            result = pedidos_service.get_top_proveedores(limite, filtros)

            return result

        except Exception as e:
            print(f"Error obteniendo top proveedores: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/pedidos/compras-por-material")
    async def get_compras_por_material(
        limite: int = Query(10, description="Número máximo de materiales a retornar"),
        mes: Optional[int] = Query(None, description="Filtrar por mes"),
        año: Optional[int] = Query(None, description="Filtrar por año"),
        pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
        db: Session = Depends(get_db)
    ):
        """Obtiene compras agrupadas por material"""
        try:
            db_service = DatabaseService(db)

            # Preparar filtros
            filtros = {}
            if mes:
                filtros['mes'] = mes
            if año:
                filtros['año'] = año
            if pedidos:
                filtros['pedidos'] = pedidos

            # Usar el servicio de pedidos para obtener los datos
            pedidos_service = db_service.pedidos_service
            result = pedidos_service.get_compras_por_material(limite, filtros)

            return result

        except Exception as e:
            print(f"Error obteniendo compras por material: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/pedidos/evolucion-precios")
    async def get_evolucion_precios(
        mes: Optional[int] = Query(None, description="Filtrar por mes"),
        año: Optional[int] = Query(None, description="Filtrar por año"),
        pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
        db: Session = Depends(get_db)
    ):
        """Obtiene evolución de precios por período"""
        try:
            db_service = DatabaseService(db)

            # Preparar filtros
            filtros = {}
            if mes:
                filtros['mes'] = mes
            if año:
                filtros['año'] = año
            if pedidos:
                filtros['pedidos'] = pedidos

            # Usar el servicio de pedidos para obtener los datos
            pedidos_service = db_service.pedidos_service
            result = pedidos_service.get_evolucion_precios(filtros)

            return result

        except Exception as e:
            print(f"Error obteniendo evolución de precios: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/pedidos/flujo-pagos-semanal")
    async def get_flujo_pagos_semanal(
        mes: Optional[int] = Query(None, description="Filtrar por mes"),
        año: Optional[int] = Query(None, description="Filtrar por año"),
        pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
        db: Session = Depends(get_db)
    ):
        """Obtiene flujo de pagos semanal"""
        try:
            db_service = DatabaseService(db)

            # Preparar filtros
            filtros = {}
            if mes:
                filtros['mes'] = mes
            if año:
                filtros['año'] = año
            if pedidos:
                filtros['pedidos'] = pedidos

            # Usar el servicio de pedidos para obtener los datos
            pedidos_service = db_service.pedidos_service
            result = pedidos_service.get_flujo_pagos_semanal(filtros)

            return result

        except Exception as e:
            print(f"Error obteniendo flujo de pagos semanal: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/pedidos/datos-filtrados")
    async def get_datos_filtrados(
        mes: Optional[int] = Query(None, description="Filtrar por mes"),
        año: Optional[int] = Query(None, description="Filtrar por año"),
        pedidos: Optional[str] = Query(None, description="Lista de pedidos separados por coma"),
        db: Session = Depends(get_db)
    ):
        """Obtiene datos filtrados para tabla"""
        try:
            db_service = DatabaseService(db)

            # Preparar filtros
            filtros = {}
            if mes:
                filtros['mes'] = mes
            if año:
                filtros['año'] = año
            if pedidos:
                filtros['pedidos'] = pedidos

            # Usar el servicio de pedidos para obtener los datos
            pedidos_service = db_service.pedidos_service
            result = pedidos_service.get_datos_filtrados(filtros)

            return result

        except Exception as e:
            print(f"Error obteniendo datos filtrados: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return app
