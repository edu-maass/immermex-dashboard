import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { KPICard } from './KPICard';
import { UnitEconomicsCard } from './UnitEconomicsCard';
import { ActivityIndicatorsCard } from './ActivityIndicatorsCard';
import { LoadingSpinner } from './LoadingSpinner';
import { Tooltip } from './ui/tooltip';
import { ComprasV2EvolucionPreciosChart } from './Charts/ComprasV2EvolucionPreciosChart';
import { ComprasV2FlujoPagosChart } from './Charts/ComprasV2FlujoPagosChart';
import { ComprasV2AgingCuentasPagarChart } from './Charts/ComprasV2AgingCuentasPagarChart';
import { TopProveedoresChart } from './Charts/TopProveedoresChart';
import { ComprasPorMaterialChart } from './Charts/ComprasPorMaterialChart';
import { MaterialChips } from './MaterialChips';
import { Pagination } from './Pagination';
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
  Calendar
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
  // Unit Economics
  precio_unitario_promedio?: number;
  costo_unitario_promedio?: number;
  utilidad_por_kg?: number;
  margen_por_kg?: number;
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
  const [topProveedores, setTopProveedores] = useState<any>(null);
  const [comprasPorMaterial, setComprasPorMaterial] = useState<any>(null);
  const [materiales, setMateriales] = useState<string[]>([]);
  const [proveedores, setProveedores] = useState<string[]>([]);
  const [añosDisponibles, setAñosDisponibles] = useState<number[]>([]);
  const [monedaPrecios, setMonedaPrecios] = useState<'USD' | 'MXN'>('USD');
  const [monedaFlujoPagos, setMonedaFlujoPagos] = useState<'USD' | 'MXN'>('USD');
  const [updatingFechas, setUpdatingFechas] = useState(false);
  
  // Estados para paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  const [totalItems, setTotalItems] = useState(0);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Cargar KPIs, datos y gráficos en paralelo
      const [kpisResponse, dataResponse, evolucionResponse, flujoResponse, agingResponse, materialesResponse, proveedoresResponse, añosResponse, topProveedoresResponse, comprasPorMaterialResponse] = await Promise.all([
        apiService.getComprasV2KPIs(filtros),
        apiService.getComprasV2Data(filtros, itemsPerPage, (currentPage - 1) * itemsPerPage),
        apiService.getComprasV2EvolucionPrecios(filtros.material, monedaPrecios),
        apiService.getComprasV2FlujoPagos(filtros, monedaFlujoPagos),
        apiService.getComprasV2AgingCuentasPagar(filtros),
        apiService.getComprasV2MaterialesList(),
        apiService.getComprasV2Proveedores(),
        apiService.getComprasV2AñosDisponibles(),
        apiService.getComprasV2TopProveedores(10, filtros),
        apiService.getComprasV2PorMaterial(10, filtros)
      ]);

      setKpis(kpisResponse);
      setComprasData(dataResponse);
      setTotalItems(dataResponse.total_compras || 0);
      setEvolucionPrecios(evolucionResponse);
      setFlujoPagos(flujoResponse);
      setAgingCuentasPagar(agingResponse);
      setMateriales(materialesResponse);
      setProveedores(proveedoresResponse);
      setAñosDisponibles(añosResponse);
      setTopProveedores(topProveedoresResponse);
      setComprasPorMaterial(comprasPorMaterialResponse);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
      console.error('Error loading compras_v2 data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filtros, monedaPrecios, monedaFlujoPagos, currentPage, itemsPerPage]);


  const handleFilterChange = (key: string, value: any) => {
    setFiltros(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value
    }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Reset to first page when changing items per page
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
    if (!confirm('¿Está seguro de que desea recalcular fechas estimadas y columnas automáticas basándose en los datos de fecha de compra, proveedores y tipos de cambio? Esta operación puede tardar unos momentos.')) {
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


  if (loading && !comprasData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">

      {/* Filtros y Acciones */}
      <div className="flex gap-6 mb-8">
        {/* Filtros */}
        <div className="bg-white rounded-lg shadow-md p-6 flex-1">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
        </div>

        {/* Acciones */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex flex-col gap-3">
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
              content={`🔄 Actualización Automática de Datos

📅 Fechas Estimadas:
   • Fecha de salida
   • Fecha de arribo
   • Fecha en planta

💰 Columnas Automáticas:
   • pu_usd (Precio Unitario en USD)
   • Conversión basada en tipo de cambio real/estimado

📊 Basado en:
   • Datos de proveedores (tiempos de producción y transporte)
   • Tipos de cambio registrados
   • Fecha de pedido

⏱️ Esta operación puede tardar unos momentos`}
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
                {updatingFechas ? 'Actualizando...' : 'Actualizar Datos'}
              </Button>
            </Tooltip>

            <Tooltip 
              content={`📂 Carga de Archivos de Compras

📋 Pasos a seguir:
   1. Ir a la pestaña "Carga de Archivos"
   2. Ubicar la sección "Compras"
   3. Descargar el layout Excel
   4. Completar con sus datos
   5. Subir el archivo completado

💡 El sistema procesará automáticamente:
   • Validación de datos
   • Cálculos de costos
   • Fechas estimadas
   • Conversiones de moneda`}
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

      {/* KPIs Principales y Indicadores de Actividad */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Total Compras KPI - Más visible */}
        <div className="lg:col-span-1">
          <Card className="backdrop-blur-sm bg-gradient-to-r from-blue-50 to-blue-100 border-2 border-blue-200 hover:shadow-xl transition-all duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg font-semibold text-blue-800">
                Total Compras
              </CardTitle>
              <div className="p-3 bg-blue-500 rounded-xl shadow-lg">
                <Package className="h-6 w-6 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-blue-900 mb-2">
                {formatCurrency(kpis.total_costo_mxn || 0)}
              </div>
              <div className="text-lg font-semibold text-blue-700">
                {kpis.total_kilogramos ? kpis.total_kilogramos.toLocaleString() : '0'} kg
              </div>
              <div className="text-sm text-blue-600 mt-1">
                Total de compras realizadas
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Indicadores de Actividad Consolidados */}
        <ActivityIndicatorsCard
          diasCreditoPromedio={kpis.dias_credito_promedio}
          diasTransportePromedio={kpis.dias_transporte_promedio}
          diasPuertoPlantaPromedio={kpis.dias_puerto_planta_promedio}
          diasCreditoNeto={kpis.dias_credito_neto}
        />
      </div>

      {/* Unit Economics KPI */}
      <div className="mb-8">
        <UnitEconomicsCard
          precioUnitarioPromedio={kpis.precio_unitario_promedio}
          costoUnitarioPromedio={kpis.costo_unitario_promedio}
          costoBasePorKg={kpis.costo_base_por_kg}
          gastosImportacionPorKg={kpis.gastos_importacion_por_kg}
          utilidadPorKg={kpis.utilidad_por_kg}
          margenPorKg={kpis.margen_por_kg}
        />
      </div>

      {/* KPIs de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <KPICard
          title="Total Proveedores"
          value={kpis.proveedores_unicos || 0}
          description="proveedores activos"
          icon={Truck}
          iconColor="text-green-600"
          iconBgColor="bg-green-100"
          raw={true}
        />
        <KPICard
          title="Compras con Anticipo"
          value={kpis.compras_con_anticipo || 0}
          icon={CheckCircle}
          iconColor="text-emerald-600"
          iconBgColor="bg-emerald-100"
        />
        <KPICard
          title="Tipo Cambio Promedio"
          value={kpis.tipo_cambio_promedio ? kpis.tipo_cambio_promedio.toFixed(2) : '0.00'}
          icon={DollarSign}
          iconColor="text-purple-600"
          iconBgColor="bg-purple-100"
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
          data={flujoPagos ? flujoPagos.labels?.map((label: string, index: number) => ({
            semana: label || `Semana ${index + 1}`,
            liquidaciones: flujoPagos.datasets[0]?.data?.[index] || 0,
            gastos_importacion: flujoPagos.datasets[1]?.data?.[index] || 0,
            anticipo: flujoPagos.datasets[2]?.data?.[index] || 0
          })) : []}
          moneda={monedaFlujoPagos}
          onMonedaChange={handleMonedaFlujoPagosChange}
          titulo={flujoPagos?.titulo}
        />
      </div>

      {/* Nuevos Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Top Proveedores por KG */}
        <TopProveedoresChart
          data={topProveedores ? (Array.isArray(topProveedores) ? topProveedores : Object.entries(topProveedores).map(([proveedor, total_kg]) => ({
            proveedor,
            total_kg: total_kg as number
          }))) : []}
          titulo="Top Proveedores por KG Comprados"
        />

        {/* Compras por Material */}
        <ComprasPorMaterialChart
          data={comprasPorMaterial ? Object.entries(comprasPorMaterial).map(([material, data]) => ({
            material,
            total_compras: (data as any).total_compras,
            total_kg: (data as any).total_kg
          })) : []}
          titulo="Compras por Material"
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
                      Fecha Salida
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha Arribo
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
                        {compra.fecha_salida_real ? 
                          new Date(compra.fecha_salida_real).toLocaleDateString('es') : 
                          compra.fecha_salida_estimada ? 
                            new Date(compra.fecha_salida_estimada).toLocaleDateString('es') : 
                            'N/A'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {compra.fecha_arribo_real ? 
                          new Date(compra.fecha_arribo_real).toLocaleDateString('es') : 
                          compra.fecha_arribo_estimada ? 
                            new Date(compra.fecha_arribo_estimada).toLocaleDateString('es') : 
                            'N/A'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <MaterialChips materiales={compra.materiales_codigos || []} />
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
          
          {/* Paginación */}
          {comprasData.compras.length > 0 && (
            <Pagination
              currentPage={currentPage}
              totalItems={totalItems}
              itemsPerPage={itemsPerPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          )}
        </div>
      )}
    </div>
  );
};
