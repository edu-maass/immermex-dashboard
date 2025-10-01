import { useState, useEffect, useCallback, memo } from 'react';
import { Button } from './ui/button';
import { KPICard } from './KPICard';
import { Filters } from './Filters';
import { 
  LazyAgingChart,
  LazyTopClientesChart,
  LazyConsumoMaterialChart,
  LazyExpectativaCobranzaChart
} from './LazyCharts';
import { LoadingSpinner, ChartLoader } from './LoadingSpinner';
import { useKPIs, useChartData } from '../hooks/useOptimizedAPI';
import { useFiltersState, useLoadingState } from '../hooks/useOptimizedState';
import { apiService } from '../services/api';
import { KPIs, FiltrosDashboard, GraficoDatos } from '../types';
import { 
  DollarSign, 
  TrendingUp, 
  Percent, 
  Package, 
  Users, 
  FileText,
  RefreshCw,
  AlertCircle,
  Clock
} from 'lucide-react';

interface DashboardProps {
  onUploadSuccess?: () => void;
  dataLoaded?: boolean;
}

// Componente memoizado para KPIs
const KPIsSection = memo(({ kpis, loading }: { kpis: KPIs | null; loading: boolean }) => {
  if (loading) {
    return <LoadingSpinner text="Cargando KPIs..." />;
  }

  if (!kpis) {
    return (
      <div className="text-center p-8">
        <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">No hay datos de KPIs disponibles</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
      {/* Facturación Total */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5 text-blue-600" />
            <h3 className="text-sm font-medium text-gray-500">Facturación Total</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">${kpis.facturacion_total?.toLocaleString()}</p>
          <p className="text-sm text-gray-500 mt-1">Sin IVA: ${kpis.facturacion_sin_iva?.toLocaleString()}</p>
        </div>
      </div>

      {/* Cobranza Relacionada */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <h3 className="text-sm font-medium text-gray-500">Cobranza Relacionada</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">${kpis.cobranza_total?.toLocaleString()}</p>
          <p className="text-sm text-gray-500 mt-1">Sin IVA: ${kpis.cobranza_sin_iva?.toLocaleString()}</p>
          <p className="text-sm text-green-600 mt-1 font-medium">% Cobrado: {kpis.porcentaje_cobrado?.toFixed(2)}%</p>
        </div>
      </div>

      {/* Cobranza General */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <h3 className="text-sm font-medium text-gray-500">Cobranza General</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">${kpis.cobranza_general_total?.toLocaleString()}</p>
          <p className="text-sm text-gray-500 mt-1">Todas las cobranzas</p>
          <p className="text-sm text-blue-600 mt-1 font-medium">% vs Facturación: {kpis.porcentaje_cobrado_general?.toFixed(2)}%</p>
        </div>
      </div>

      {/* Anticipos */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-orange-600" />
            <h3 className="text-sm font-medium text-gray-500">Anticipos</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">${kpis.anticipos_total?.toLocaleString()}</p>
          <p className="text-sm text-orange-600 mt-1 font-medium">% Anticipos: {kpis.porcentaje_anticipos?.toFixed(2)}%</p>
        </div>
      </div>

      {/* Métricas adicionales */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5 text-purple-600" />
            <h3 className="text-sm font-medium text-gray-500">Facturas</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">{kpis.total_facturas}</p>
          <p className="text-sm text-gray-500 mt-1">Total facturas</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="h-5 w-5 text-indigo-600" />
            <h3 className="text-sm font-medium text-gray-500">Clientes</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">{kpis.clientes_unicos}</p>
          <p className="text-sm text-gray-500 mt-1">Clientes únicos</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Package className="h-5 w-5 text-red-600" />
            <h3 className="text-sm font-medium text-gray-500">Pedidos</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">{kpis.pedidos_unicos}</p>
          <p className="text-sm text-gray-500 mt-1">Pedidos únicos</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Percent className="h-5 w-5 text-teal-600" />
            <h3 className="text-sm font-medium text-gray-500">Toneladas</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">{kpis.toneladas_total?.toFixed(1)}</p>
          <p className="text-sm text-gray-500 mt-1">Toneladas totales</p>
        </div>
      </div>

      {/* Precio Unitario Promedio */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5 text-green-600" />
            <h3 className="text-sm font-medium text-gray-500">Precio Unitario</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">${kpis.precio_unitario_promedio?.toFixed(2)}</p>
          <p className="text-sm text-gray-500 mt-1">Promedio por kg</p>
        </div>
      </div>

      {/* Costo Unitario Promedio */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-red-600" />
            <h3 className="text-sm font-medium text-gray-500">Costo Unitario</h3>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-bold text-gray-900">${kpis.costo_unitario_promedio?.toFixed(2)}</p>
          <p className="text-sm text-gray-500 mt-1">Promedio por kg</p>
        </div>
      </div>
    </div>
  );
});

KPIsSection.displayName = 'KPIsSection';

export const OptimizedDashboard: React.FC<DashboardProps> = ({ onUploadSuccess }) => {
  // Hooks optimizados
  const { kpis, fetchKPIs, loading: kpisLoading } = useKPIs();
  const { chartData, fetchAllCharts, loading: chartsLoading } = useChartData();
  const { filters, updateFilter, clearFilters, hasActiveFilters } = useFiltersState();
  const { setLoading, isLoading } = useLoadingState();
  
  const [error, setError] = useState<string | null>(null);

  // Cargar datos iniciales
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading('initial', true);
      try {
        await Promise.all([
          fetchKPIs(),
          fetchAllCharts()
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error cargando datos');
      } finally {
        setLoading('initial', false);
      }
    };

    loadInitialData();
  }, [fetchKPIs, fetchAllCharts, setLoading]);

  // Manejar cambios en filtros
  const handleFilterChange = useCallback(async (newFilters: FiltrosDashboard) => {
    setLoading('filters', true);
    try {
      await Promise.all([
        fetchKPIs(newFilters),
        fetchAllCharts(newFilters)
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error aplicando filtros');
    } finally {
      setLoading('filters', false);
    }
  }, [fetchKPIs, fetchAllCharts, setLoading]);

  // Manejar upload exitoso
  const handleUploadSuccess = useCallback(async () => {
    if (onUploadSuccess) onUploadSuccess();
    
    // Recargar datos después del upload
    setLoading('upload', true);
    try {
      await Promise.all([
        fetchKPIs(),
        fetchAllCharts()
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error recargando datos');
    } finally {
      setLoading('upload', false);
    }
  }, [onUploadSuccess, fetchKPIs, fetchAllCharts, setLoading]);

  // Función para formatear datos de expectativa de cobranza
  const formatExpectativaCobranzaData = useCallback((expectativaData: any) => {
    if (!expectativaData || typeof expectativaData !== 'object') return [];
    
    return Object.entries(expectativaData).map(([semana, data]: [string, any]) => ({
      semana,
      cobranza_esperada: data.cobranza_esperada || 0,
      cobranza_real: data.cobranza_real || 0,
      pedidos_pendientes: data.pedidos_pendientes || 0
    }));
  }, []);

  // Función para transformar GraficoDatos a formato de array para charts
  const transformChartData = useCallback((chartData: any) => {
    if (!chartData || !Array.isArray(chartData.labels) || !Array.isArray(chartData.data)) {
      return [];
    }
    
    return chartData.labels.map((label: string, index: number) => ({
      name: label,
      value: chartData.data[index] || 0
    }));
  }, []);

  const loading = isLoading('initial') || isLoading('upload');

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <LoadingSpinner text="Cargando dashboard..." />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard Immermex</h1>
          <p className="text-gray-600">Análisis de facturación, cobranza y pedidos</p>
        </div>


        {/* Filtros */}
        <div className="mb-8">
          <Filters 
            onFilterChange={handleFilterChange}
            onClearFilters={clearFilters}
            hasActiveFilters={hasActiveFilters}
          />
        </div>

        {/* Error display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              <p className="text-red-800">{error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setError(null)}
                className="ml-auto"
              >
                Cerrar
              </Button>
            </div>
          </div>
        )}

        {/* KPIs */}
        <KPIsSection kpis={kpis} loading={kpisLoading || isLoading('filters')} />

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Aging de Cartera */}
          {chartData.aging && (
            <LazyAgingChart data={transformChartData(chartData.aging)} />
          )}

          {/* Top Clientes */}
          {chartData['top-clientes'] && (
            <LazyTopClientesChart data={transformChartData(chartData['top-clientes'])} />
          )}

          {/* Consumo de Material */}
          {chartData['consumo-material'] && (
            <LazyConsumoMaterialChart data={transformChartData(chartData['consumo-material'])} />
          )}

          {/* Expectativa de Cobranza */}
          {kpis?.expectativa_cobranza && Object.keys(kpis.expectativa_cobranza).length > 0 && (
            <div className="lg:col-span-2">
              <LazyExpectativaCobranzaChart 
                data={formatExpectativaCobranzaData(kpis.expectativa_cobranza)}
              />
            </div>
          )}
        </div>

        {/* Loading indicator para gráficos */}
        {(chartsLoading || isLoading('filters')) && (
          <div className="mt-8 flex justify-center">
            <LoadingSpinner text="Actualizando gráficos..." />
          </div>
        )}
      </div>
    </div>
  );
};
