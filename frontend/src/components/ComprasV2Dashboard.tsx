import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { KPICard } from './KPICard';
import { LoadingSpinner } from './LoadingSpinner';
import { Tooltip } from './ui/tooltip';
import { ComprasV2EvolucionPreciosChart } from './Charts/ComprasV2EvolucionPreciosChart';
import { ComprasV2FlujoPagosChart } from './Charts/ComprasV2FlujoPagosChart';
import { ComprasV2AgingCuentasPagarChart } from './Charts/ComprasV2AgingCuentasPagarChart';
import { apiService } from '../services/api';
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Truck,
  AlertCircle,
  CheckCircle,
  Upload,
  RefreshCw,
  Clock,
  Building,
  Calendar,
  Percent
} from 'lucide-react';

interface ComprasV2DashboardProps {
  onUploadSuccess?: () => void;
}

interface ComprasV2KPIs {
  total_compras?: number;
  total_proveedores?: number;
  total_kilogramos?: number;
  total_costo_divisa?: number;
  total_costo_mxn?: number;
  compras_con_anticipo?: number;
  compras_pagadas?: number;
  tipo_cambio_promedio?: number;
  // KPIs adicionales del dashboard legacy
  dias_credito_promedio?: number;
  compras_pendientes?: number;
  compras_pendientes_count?: number;
  promedio_por_proveedor?: number;
  proveedores_unicos?: number;
  margen_bruto_promedio?: number;
  rotacion_inventario?: number;
  ciclo_compras?: number;
  materiales_unicos?: number;
}

interface ComprasV2Data {
  success: boolean;
  compras: any[];
  total_compras: number;
  filtros_aplicados: any;
}

export const ComprasV2Dashboard: React.FC<ComprasV2DashboardProps> = ({ onUploadSuccess: _onUploadSuccess }) => {
  const [kpis, setKpis] = useState<ComprasV2KPIs>({});
  const [comprasData, setComprasData] = useState<ComprasV2Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtros, setFiltros] = useState({
    mes: undefined as number | undefined,
    año: undefined as number | undefined,
    proveedor: undefined as string | undefined,
    material: undefined as string | undefined
  });
  
  // Estados para gráficos
  const [evolucionPrecios, setEvolucionPrecios] = useState<any>(null);
  const [flujoPagos, setFlujoPagos] = useState<any>(null);
  const [agingCuentasPagar, setAgingCuentasPagar] = useState<any>(null);
  const [materiales, setMateriales] = useState<string[]>([]);
  const [proveedores, setProveedores] = useState<string[]>([]);
  const [añosDisponibles, setAñosDisponibles] = useState<number[]>([]);
  const [monedaPrecios, setMonedaPrecios] = useState<'USD' | 'MXN'>('USD');
  const [monedaFlujoPagos, setMonedaFlujoPagos] = useState<'USD' | 'MXN'>('USD');
  const [updatingFechas, setUpdatingFechas] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Cargar KPIs, datos y gráficos en paralelo
      const [kpisResponse, dataResponse, evolucionResponse, flujoResponse, agingResponse, materialesResponse, proveedoresResponse, añosResponse] = await Promise.all([
        apiService.getComprasV2KPIs(filtros),
        apiService.getComprasV2Data(filtros, 50),
        apiService.getComprasV2EvolucionPrecios(filtros.material, monedaPrecios),
        apiService.getComprasV2FlujoPagos(filtros, monedaFlujoPagos),
        apiService.getComprasV2AgingCuentasPagar(filtros),
        apiService.getComprasV2MaterialesList(),
        apiService.getComprasV2Proveedores(),
        apiService.getComprasV2AñosDisponibles()
      ]);

      setKpis(kpisResponse);
      setComprasData(dataResponse);
      setEvolucionPrecios(evolucionResponse);
      setFlujoPagos(flujoResponse);
      setAgingCuentasPagar(agingResponse);
      setMateriales(materialesResponse);
      setProveedores(proveedoresResponse);
      setAñosDisponibles(añosResponse);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
      console.error('Error loading compras_v2 data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filtros, monedaPrecios, monedaFlujoPagos]);


  const handleFilterChange = (key: string, value: any) => {
    setFiltros(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value
    }));
  };

  const clearFilters = () => {
    setFiltros({
      mes: undefined,
      año: undefined,
      proveedor: undefined,
      material: undefined
    });
  };

  const handleMonedaPreciosChange = async (nuevaMoneda: 'USD' | 'MXN') => {
    setMonedaPrecios(nuevaMoneda);
    // Recargar datos de evolución de precios con la nueva moneda
    try {
      const evolucionData = await apiService.getComprasV2EvolucionPrecios(filtros.material, nuevaMoneda);
      setEvolucionPrecios(evolucionData);
    } catch (err) {
      console.error('Error recargando evolución de precios:', err);
    }
  };

  const handleMonedaFlujoPagosChange = async (nuevaMoneda: 'USD' | 'MXN') => {
    setMonedaFlujoPagos(nuevaMoneda);
    // Recargar datos del flujo de pagos con la nueva moneda
    try {
      const flujoData = await apiService.getComprasV2FlujoPagos(filtros, nuevaMoneda);
      setFlujoPagos(flujoData);
    } catch (err) {
      console.error('Error recargando flujo de pagos:', err);
    }
  };

  const handleUpdateFechasEstimadas = async () => {
    if (!confirm('¿Está seguro de que desea recalcular todas las fechas estimadas basándose en los datos de fecha de compra y proveedores? Esta operación puede tardar unos momentos.')) {
      return;
    }

    try {
      setUpdatingFechas(true);
      setError(null);
      
      const result = await apiService.updateComprasV2FechasEstimadas();
      
      alert(`Actualización completada:\n- Total de registros: ${result.total_records}\n- Registros actualizados: ${result.updated}\n- Registros sin cambios: ${result.skipped}`);
      
      // Recargar datos después de la actualización
      await loadData();
      
    } catch (err: any) {
      console.error('Error actualizando fechas estimadas:', err);
      setError(err.message || 'Error al actualizar fechas estimadas');
      alert('Error al actualizar fechas estimadas. Por favor, intente nuevamente.');
    } finally {
      setUpdatingFechas(false);
    }
  };

  const hasActiveFilters = Object.values(filtros).some(value => value !== undefined);

  const formatCurrency = (value: number) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0';
    }
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatCurrencyUSD = (value: number) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0 USD';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };


  if (loading && !comprasData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Dashboard de Compras V2
        </h1>
        <p className="text-gray-600">
          Sistema optimizado de gestión de compras con cálculo automático de fechas
        </p>
      </div>

      {/* Filtros y Carga de Archivos */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 flex-1">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mes
              </label>
              <select
                value={filtros.mes || ''}
                onChange={(e) => handleFilterChange('mes', e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {new Date(2024, i).toLocaleString('es', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Año
              </label>
              <select
                value={filtros.año || ''}
                onChange={(e) => handleFilterChange('año', e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                {añosDisponibles.map((año) => (
                  <option key={año} value={año}>
                    {año}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Proveedor
              </label>
              <select
                value={filtros.proveedor || ''}
                onChange={(e) => handleFilterChange('proveedor', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos los proveedores</option>
                {proveedores.length > 0 ? proveedores.map((proveedor, index) => (
                  <option key={index} value={proveedor}>{proveedor}</option>
                )) : (
                  <option value="" disabled>Sube un archivo de compras para ver proveedores</option>
                )}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Material
              </label>
              <select
                value={filtros.material || ''}
                onChange={(e) => handleFilterChange('material', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos los materiales</option>
                {materiales.map((material, index) => (
                  <option key={index} value={material}>
                    {material}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
            <Button 
              onClick={loadData} 
              disabled={loading}
              variant="outline" 
              size="sm"
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>

            <Tooltip 
              content="Recalcular todas las fechas estimadas (salida, arribo y planta) basándose en la fecha de compra y los datos de proveedores"
              position="left"
            >
              <Button 
                onClick={handleUpdateFechasEstimadas} 
                disabled={loading || updatingFechas}
                variant="outline" 
                size="sm"
                className="flex items-center gap-2"
              >
                <Calendar className={`h-4 w-4 ${updatingFechas ? 'animate-pulse' : ''}`} />
                {updatingFechas ? 'Actualizando...' : 'Actualizar Fechas'}
              </Button>
            </Tooltip>

            <Tooltip 
              content="Para cargar archivos de Compras V2:\n• Ve a la pestaña 'Carga de Archivos'\n• Busca la sección 'Compras V2'\n• Descarga el layout Excel\n• Completa y sube el archivo"
              position="left"
            >
              <Button 
                variant="outline" 
                size="sm"
                className="flex items-center gap-2"
                onClick={() => {
                  // Scroll to upload section or show modal
                  const uploadTab = document.querySelector('[data-tab="upload"]') as HTMLElement;
                  if (uploadTab) {
                    uploadTab.click();
                  }
                }}
              >
                <Upload className="h-4 w-4" />
              </Button>
            </Tooltip>

            {hasActiveFilters && (
              <Button onClick={clearFilters} variant="outline" size="sm">
                Limpiar
              </Button>
            )}
          </div>
        </div>
      </div>


      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Total Compras"
          value={formatCurrency(kpis.total_costo_mxn || 0)}
          description={kpis.total_costo_divisa ? formatCurrencyUSD(kpis.total_costo_divisa) : ''}
          icon={Package}
          raw={true}
        />
        <KPICard
          title="Compras Pendientes"
          value={formatCurrency(kpis.compras_pendientes || 0)}
          description={`${kpis.compras_pendientes_count || 0} facturas pendientes`}
          icon={Clock}
          raw={true}
        />
        <KPICard
          title="Promedio por Proveedor"
          value={formatCurrency(kpis.promedio_por_proveedor || 0)}
          description={`${kpis.proveedores_unicos || 0} proveedores activos`}
          icon={Building}
          raw={true}
        />
        <KPICard
          title="Días Promedio Crédito"
          value={kpis.dias_credito_promedio ? kpis.dias_credito_promedio.toFixed(0) : '0'}
          description="días promedio"
          icon={Calendar}
          raw={true}
        />
      </div>

      {/* KPIs Adicionales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <KPICard
          title="Margen Bruto Promedio"
          value={`${(kpis.margen_bruto_promedio || 0).toFixed(1)}%`}
          description="Precio venta vs costo compra"
          icon={Percent}
          raw={true}
        />
        <KPICard
          title="Rotación Inventario"
          value={`${(kpis.rotacion_inventario || 0).toFixed(1)}`}
          description="veces por año"
          icon={Package}
          raw={true}
        />
        <KPICard
          title="Ciclo de Compras"
          value={`${(kpis.ciclo_compras || 0).toFixed(0)}`}
          description="días promedio"
          icon={TrendingUp}
          raw={true}
        />
      </div>

      {/* KPIs de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Total Proveedores"
          value={kpis.total_proveedores || 0}
          icon={Truck}
        />
        <KPICard
          title="Total KG"
          value={kpis.total_kilogramos ? kpis.total_kilogramos.toLocaleString() : '0'}
          icon={TrendingUp}
          raw={true}
        />
        <KPICard
          title="Compras con Anticipo"
          value={kpis.compras_con_anticipo || 0}
          icon={CheckCircle}
        />
        <KPICard
          title="Tipo Cambio Promedio"
          value={kpis.tipo_cambio_promedio ? kpis.tipo_cambio_promedio.toFixed(2) : '0.00'}
          icon={DollarSign}
          raw={true}
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Evolución de Precios */}
        <ComprasV2EvolucionPreciosChart
          data={evolucionPrecios ? evolucionPrecios.data : []}
          moneda={monedaPrecios}
          onMonedaChange={handleMonedaPreciosChange}
          titulo={evolucionPrecios?.titulo}
        />

        {/* Flujo de Pagos */}
        <ComprasV2FlujoPagosChart
          data={flujoPagos ? flujoPagos.datasets?.[0]?.data?.map((pagos: number, index: number) => ({
            semana: flujoPagos.labels[index] || `Semana ${index + 1}`,
            pagos: pagos,
            pendiente: flujoPagos.datasets?.[1]?.data?.[index] || 0
          })) : []}
          moneda={monedaFlujoPagos}
          onMonedaChange={handleMonedaFlujoPagosChange}
          titulo={flujoPagos?.titulo}
        />
      </div>

      {/* Aging de Cuentas por Pagar */}
      <div className="mb-8">
        <ComprasV2AgingCuentasPagarChart
          data={agingCuentasPagar ? agingCuentasPagar.labels.map((label: string, index: number) => ({
            name: label,
            value: agingCuentasPagar.data[index] || 0
          })) : []}
          titulo={agingCuentasPagar?.titulo}
        />
      </div>

      {/* Datos de compras */}
      {comprasData && (
        <div className="bg-white rounded-lg shadow-md p-6">
          
          {comprasData.compras.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IMI
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Proveedor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Puerto Origen
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha Pedido
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Salida Estimada
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Arribo Estimado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Materiales
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {comprasData.compras.map((compra, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {compra.imi}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.proveedor}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.puerto_origen || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.fecha_pedido ? new Date(compra.fecha_pedido).toLocaleDateString('es') : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.fecha_salida_estimada ? new Date(compra.fecha_salida_estimada).toLocaleDateString('es') : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.fecha_arribo_estimada ? new Date(compra.fecha_arribo_estimada).toLocaleDateString('es') : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.materiales_count || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No hay datos de compras disponibles</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
