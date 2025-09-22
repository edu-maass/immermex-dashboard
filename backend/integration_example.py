"""
Ejemplo de integración del procesador de Excel con el backend de Immermex
"""

from excel_processor import load_and_clean_excel
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_immermex_file(file_path: str):
    """
    Procesa un archivo Excel de Immermex y retorna datos listos para el dashboard
    
    Args:
        file_path: Ruta del archivo Excel
        
    Returns:
        dict: Diccionario con DataFrames procesados
    """
    try:
        logger.info(f"Procesando archivo Immermex: {file_path}")
        
        # Cargar y limpiar datos
        data = load_and_clean_excel(file_path)
        
        # Validar que se obtuvieron datos
        if all(df.empty for df in data.values()):
            logger.warning("No se obtuvieron datos del archivo")
            return None
        
        # Log de resumen
        logger.info("Datos procesados exitosamente:")
        for key, df in data.items():
            logger.info(f"  {key}: {len(df)} registros")
        
        return data
        
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        return None

def get_kpis_from_data(data: dict):
    """
    Calcula KPIs básicos a partir de los datos procesados
    
    Args:
        data: Diccionario con DataFrames procesados
        
    Returns:
        dict: KPIs calculados
    """
    try:
        kpis = {}
        
        # KPIs de facturación
        if not data['facturacion_clean'].empty:
            fact_df = data['facturacion_clean']
            
            kpis['total_facturado'] = fact_df['monto_total'].sum()
            kpis['total_pendiente'] = fact_df['saldo_pendiente'].sum()
            kpis['num_facturas'] = len(fact_df)
            kpis['promedio_factura'] = fact_df['monto_total'].mean()
            
            # Facturas vencidas (más de 30 días)
            if 'fecha_factura' in fact_df.columns:
                from datetime import datetime, timedelta
                hoy = datetime.now()
                facturas_vencidas = fact_df[
                    (fact_df['fecha_factura'] < hoy - timedelta(days=30)) &
                    (fact_df['saldo_pendiente'] > 0)
                ]
                kpis['facturas_vencidas'] = len(facturas_vencidas)
                kpis['monto_vencido'] = facturas_vencidas['saldo_pendiente'].sum()
        
        # KPIs de cobranza
        if not data['cobranza_clean'].empty:
            cob_df = data['cobranza_clean']
            
            kpis['total_cobrado'] = cob_df['importe_pagado'].sum()
            kpis['num_pagos'] = len(cob_df)
        
        # KPIs de pedidos
        if not data['pedidos_clean'].empty:
            ped_df = data['pedidos_clean']
            
            kpis['total_kg'] = ped_df['kg'].sum()
            kpis['num_pedidos'] = len(ped_df)
            kpis['promedio_kg_pedido'] = ped_df['kg'].mean()
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error calculando KPIs: {str(e)}")
        return {}

# Ejemplo de uso
if __name__ == "__main__":
    # Procesar archivo de ejemplo
    file_path = "docs/0925_material_pedido (4).xlsx"
    
    data = process_immermex_file(file_path)
    if data:
        kpis = get_kpis_from_data(data)
        print("\n📊 KPIs CALCULADOS:")
        for key, value in kpis.items():
            print(f"  {key}: {value}")
    else:
        print("❌ No se pudieron procesar los datos")
