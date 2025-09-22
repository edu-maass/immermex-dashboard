import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { KPICard } from './KPICard';
import { FileUpload } from './FileUpload';
import { Filters } from './Filters';
import { AgingChart } from './Charts/AgingChart';
import { TopClientesChart } from './Charts/TopClientesChart';
import { ConsumoMaterialChart } from './Charts/ConsumoMaterialChart';
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

export const Dashboard: React.FC = () => {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [agingData, setAgingData] = useState<GraficoDatos | null>(null);
  const [topClientesData, setTopClientesData] = useState<GraficoDatos | null>(null);
  const [consumoMaterialData, setConsumoMaterialData] = useState<GraficoDatos | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<FiltrosDashboard>({});

  const loadData = async (filtrosAplicados: FiltrosDashboard = {}) => {
    try {
      setLoading(true);
      setError(null);

      // Cargar KPIs
      const kpisData = await apiService.getKPIs(filtrosAplicados);
      setKpis(kpisData as KPIs);

      // Cargar gráficos con manejo individual de errores
      try {
        const [aging, topClientes, consumoMaterial] = await Promise.allSettled([
          apiService.getGraficoAging(filtrosAplicados),
          apiService.getGraficoTopClientes(10, filtrosAplicados),
          apiService.getGraficoConsumoMaterial(10, filtrosAplicados)
        ]);

        // Procesar resultados de gráficos
        if (aging.status === 'fulfilled') {
          setAgingData(aging.value as GraficoDatos);
        } else {
          console.warn('Error cargando aging:', aging.reason);
        }

        if (topClientes.status === 'fulfilled') {
          setTopClientesData(topClientes.value as GraficoDatos);
        } else {
          console.warn('Error cargando top clientes:', topClientes.reason);
        }

        if (consumoMaterial.status === 'fulfilled') {
          setConsumoMaterialData(consumoMaterial.value as GraficoDatos);
        } else {
          console.warn('Error cargando consumo material:', consumoMaterial.reason);
        }

      } catch (chartError) {
        console.warn('Error cargando gráficos:', chartError);
        // No establecer error global para gráficos, solo KPIs son críticos
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFiltersChange = (nuevosFiltros: FiltrosDashboard) => {
    setFiltros(nuevosFiltros);
    loadData(nuevosFiltros);
  };

  const handleClearFilters = () => {
    setFiltros({});
    loadData({});
  };

  const handleUploadSuccess = () => {
    // Recargar datos después de subir archivo
    loadData(filtros);
  };

  const formatAgingData = (aging: Record<string, number>) => {
    return Object.entries(aging).map(([name, value]) => ({ name, value }));
  };

  const formatTopClientesData = (clientes: Record<string, number>) => {
    return Object.entries(clientes).map(([name, value]) => ({ name, value }));
  };

  const formatConsumoMaterialData = (materiales: Record<string, number>) => {
    return Object.entries(materiales).map(([name, value]) => ({ name, value }));
  };

  if (loading && !kpis) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Cargando datos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <AlertCircle className="h-8 w-8 text-red-500" />
        <span className="ml-2 text-red-500">{error}</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Dashboard Immermex</h1>
          <p className="text-muted-foreground mt-1">
            Indicadores financieros y operativos
          </p>
        </div>
        <Button onClick={() => loadData(filtros)} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Upload Section */}
      <FileUpload 
        onUploadSuccess={handleUploadSuccess}
        onUploadError={(error) => setError(error)}
      />

      {/* Filters */}
      <Filters 
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
      />

      {/* KPIs Grid */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          <KPICard
            title="Facturación Total"
            value={kpis.facturacion_total}
            icon={DollarSign}
            description="Total facturado en el período"
          />
          <KPICard
            title="Cobranza Total"
            value={kpis.cobranza_total}
            icon={TrendingUp}
            description="Total cobrado en el período"
          />
          <KPICard
            title="% Cobrado"
            value={`${kpis.porcentaje_cobrado}%`}
            icon={Percent}
            description="Porcentaje de cobranza"
          />
          <KPICard
            title="Anticipos"
            value={kpis.anticipos_total}
            icon={Package}
            description="Total de anticipos recibidos"
          />
          <KPICard
            title="Total Facturas"
            value={kpis.total_facturas}
            icon={FileText}
            description="Número de facturas emitidas"
            raw
          />
          <KPICard
            title="Clientes Únicos"
            value={kpis.clientes_unicos}
            icon={Users}
            description="Clientes únicos en el período"
            raw
          />
          <KPICard
            title="Rotación Inventario"
            value={kpis.rotacion_inventario}
            icon={Package}
            description="Veces que se rotó el inventario"
            raw
          />
          <KPICard
            title="Días CxC Ajustado"
            value={kpis.dias_cxc_ajustado || 0}
            icon={Clock}
            description="Días promedio de cobro ajustado"
            raw
          />
          <KPICard
            title="Ciclo de Efectivo"
            value={kpis.ciclo_efectivo || 0}
            icon={RefreshCw}
            description="Inventario + Cuentas por Cobrar"
            raw
          />
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Aging de Cartera */}
        {agingData && agingData.data && agingData.data.length > 0 && (
          <AgingChart 
            data={formatAgingData(agingData.data.reduce((acc, value, index) => {
              acc[agingData.labels[index]] = value;
              return acc;
            }, {} as Record<string, number>))}
          />
        )}

        {/* Top Clientes */}
        {topClientesData && topClientesData.data && topClientesData.data.length > 0 && (
          <TopClientesChart 
            data={formatTopClientesData(topClientesData.data.reduce((acc, value, index) => {
              acc[topClientesData.labels[index]] = value;
              return acc;
            }, {} as Record<string, number>))}
          />
        )}

        {/* Consumo por Material */}
        {consumoMaterialData && consumoMaterialData.data && consumoMaterialData.data.length > 0 && (
          <ConsumoMaterialChart 
            data={formatConsumoMaterialData(consumoMaterialData.data.reduce((acc, value, index) => {
              acc[consumoMaterialData.labels[index]] = value;
              return acc;
            }, {} as Record<string, number>))}
          />
        )}
      </div>
    </div>
  );
};
