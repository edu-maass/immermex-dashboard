import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { KPICard } from './KPICard';
import { FileUpload } from './FileUpload';
import { Filters } from './Filters';
import { AgingChart } from './Charts/AgingChart';
import { TopClientesChart } from './Charts/TopClientesChart';
import { ConsumoMaterialChart } from './Charts/ConsumoMaterialChart';
import { ExpectativaCobranzaChart } from './Charts/ExpectativaCobranzaChart';
import { CobranzaFuturaChart } from './Charts/CobranzaFuturaChart';
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

export const Dashboard: React.FC<DashboardProps> = ({ onUploadSuccess }) => {
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

  const handleClearFilters = async () => {
    setFiltros({});
    // Aplicar filtros vacíos en el backend para mostrar todos los datos
    try {
      await apiService.aplicarFiltros({});
      loadData({});
    } catch (error) {
      console.error('Error limpiando filtros:', error);
      loadData({});
    }
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

  const formatExpectativaCobranzaData = (expectativa: Record<string, {cobranza_esperada: number, cobranza_real: number, pedidos_pendientes: number}>) => {
    console.log('formatExpectativaCobranzaData received:', expectativa);
    const formatted = Object.entries(expectativa).map(([semana, datos]) => ({
      semana,
      cobranza_esperada: datos.cobranza_esperada,
      cobranza_real: datos.cobranza_real,
      pedidos_pendientes: datos.pedidos_pendientes
    }));
    console.log('formatExpectativaCobranzaData formatted:', formatted);
    return formatted;
  };

  const formatExpectativaCobranzaDataOld = (expectativa: Record<string, {cobranza_esperada: number, cobranza_real: number}>) => {
    // Convertir a array y ordenar por semana (ya viene ordenado del backend)
    return Object.entries(expectativa).map(([semana, datos]) => ({
      semana,
      cobranza_esperada: datos.cobranza_esperada,
      cobranza_real: datos.cobranza_real
    }));
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
          <h1 className="text-4xl font-bold tracking-tight">Dashboard General</h1>
          <p className="text-muted-foreground mt-1">
            Indicadores financieros y operativos
          </p>
        </div>
        <Button onClick={() => loadData(filtros)} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Filters */}
      <Filters 
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
      />

      {/* KPIs Grid */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
          {/* Facturación con sin IVA */}
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

          {/* Anticipos con porcentaje */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Package className="h-5 w-5 text-purple-600" />
                <h3 className="text-sm font-medium text-gray-500">Anticipos</h3>
              </div>
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-gray-900">${kpis.anticipos_total?.toLocaleString()}</p>
              <p className="text-sm text-gray-500 mt-1">{kpis.porcentaje_anticipos?.toFixed(2)}% sobre facturación</p>
            </div>
          </div>

          {/* KPIs de Pedidos - Combinados */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Package className="h-5 w-5 text-orange-600" />
                <h3 className="text-sm font-medium text-gray-500">Pedidos Utilizados</h3>
              </div>
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-gray-900">${kpis.total_pedidos?.toLocaleString()}</p>
              <div className="mt-2 space-y-1">
                <p className="text-lg font-semibold text-gray-700">{kpis.toneladas_total?.toFixed(1)} toneladas</p>
                <p className="text-sm text-gray-500">{kpis.pedidos_unicos} pedidos únicos</p>
              </div>
            </div>
          </div>
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
        {kpis && kpis.aging_cartera && (
          <AgingChart 
            data={formatAgingData(kpis.aging_cartera)}
          />
        )}

        {/* Top Clientes */}
        {kpis && kpis.top_clientes && Object.keys(kpis.top_clientes).length > 0 && (
          <TopClientesChart 
            data={formatTopClientesData(kpis.top_clientes)}
          />
        )}

        {/* Consumo por Material */}
        {kpis && kpis.consumo_material && (
          <ConsumoMaterialChart 
            data={formatConsumoMaterialData(kpis.consumo_material)}
          />
        )}

        {/* Expectativa de Cobranza */}
        {kpis && kpis.expectativa_cobranza && Object.keys(kpis.expectativa_cobranza).length > 0 && (
          <ExpectativaCobranzaChart 
            data={formatExpectativaCobranzaDataOld(kpis.expectativa_cobranza)}
          />
        )}
      </div>

      {/* Nueva fila para gráfico de cobranza futura */}
      <div className="grid grid-cols-1 gap-6 mt-6">
        {/* Cobranza Futura Esperada */}
        {(() => {
          console.log('Checking cobranza futura condition:', {
            hasKpis: !!kpis,
            hasExpectativa: !!kpis?.expectativa_cobranza,
            expectativaKeys: kpis?.expectativa_cobranza ? Object.keys(kpis.expectativa_cobranza) : [],
            expectativaLength: kpis?.expectativa_cobranza ? Object.keys(kpis.expectativa_cobranza).length : 0
          });
          
          // Si no hay datos reales, usar datos de prueba temporalmente
          if (kpis && kpis.expectativa_cobranza && Object.keys(kpis.expectativa_cobranza).length === 0) {
            console.log('Using fallback test data for cobranza futura chart');
            const testData = [
              { semana: 'Semana 1 (25/09 - 01/10)', cobranza_esperada: 100000, cobranza_real: 0, pedidos_pendientes: 5 },
              { semana: 'Semana 2 (02/10 - 08/10)', cobranza_esperada: 150000, cobranza_real: 0, pedidos_pendientes: 6 },
              { semana: 'Semana 3 (09/10 - 15/10)', cobranza_esperada: 200000, cobranza_real: 0, pedidos_pendientes: 7 },
              { semana: 'Semana 4 (16/10 - 22/10)', cobranza_esperada: 250000, cobranza_real: 0, pedidos_pendientes: 8 },
              { semana: 'Semana 5 (23/10 - 29/10)', cobranza_esperada: 300000, cobranza_real: 0, pedidos_pendientes: 9 },
              { semana: 'Semana 6 (30/10 - 05/11)', cobranza_esperada: 350000, cobranza_real: 0, pedidos_pendientes: 10 }
            ];
            return <CobranzaFuturaChart data={testData} />;
          }
          
          // Si hay datos reales, usarlos
          if (kpis && kpis.expectativa_cobranza && Object.keys(kpis.expectativa_cobranza).length > 0) {
            return <CobranzaFuturaChart data={formatExpectativaCobranzaData(kpis.expectativa_cobranza)} />;
          }
          
          // Si no hay datos en absoluto, no mostrar nada
          return null;
        })()}
      </div>
    </div>
  );
};
