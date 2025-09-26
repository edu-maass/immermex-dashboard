import { FC, useState, useEffect } from 'react';
import { Button } from './ui/button';
import { RefreshCw, Upload, TrendingUp, DollarSign, Package, Users, BarChart3 } from 'lucide-react';
import { apiService } from '../services/api';
import { KPIs } from '../types';
import { PedidoFilter } from './PedidoFilter';
import { AgingChart } from './Charts/AgingChart';
import { TopClientesChart } from './Charts/TopClientesChart';
import { ConsumoMaterialChart } from './Charts/ConsumoMaterialChart';
import { ExpectativaCobranzaChart } from './Charts/ExpectativaCobranzaChart';

interface DashboardFiltradoProps {
  onUploadSuccess?: () => void;
  dataLoaded?: boolean;
}

export const DashboardFiltrado: FC<DashboardFiltradoProps> = ({ onUploadSuccess, dataLoaded }) => {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pedidosSeleccionados, setPedidosSeleccionados] = useState<string[]>([]);

  const loadData = async (pedidosAplicar?: string[]) => {
    console.log('loadData llamado con pedidos:', pedidosAplicar);
    setLoading(true);
    setError(null);
    
    try {
      // Aplicar filtros de pedido (incluso si es array vacío)
      console.log('Aplicando filtros de pedido:', pedidosAplicar || []);
      await apiService.aplicarFiltrosPedido(pedidosAplicar || []);
      
      // Obtener KPIs con filtros de pedidos
      console.log('Obteniendo KPIs...');
      const kpisData = await apiService.getKPIs({ pedidos: pedidosAplicar?.join(',') });
      console.log('KPIs obtenidos:', kpisData);
      setKpis(kpisData as KPIs);
      
    } catch (err) {
      console.error('Error cargando datos:', err);
      setError('Error cargando datos del dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Verificar si hay datos disponibles antes de inicializar
    const checkDataAvailability = async () => {
      try {
        // Si ya sabemos que hay datos cargados, cargar directamente
        if (dataLoaded) {
          console.log('Datos ya cargados, mostrando dashboard general');
          await apiService.aplicarFiltrosPedido([]); // Limpiar filtros para mostrar todos los datos
          const kpisData = await apiService.getKPIs({ pedidos: '' });
          setKpis(kpisData as KPIs);
          return;
        }

        // Si no sabemos el estado, verificar si hay pedidos disponibles
        const pedidos = await apiService.getPedidosFiltro();
        if (pedidos.length > 0) {
          // Si hay pedidos, cargar datos generales (sin filtro)
          console.log('Datos disponibles encontrados, cargando dashboard general');
          await apiService.aplicarFiltrosPedido([]); // Limpiar filtros para mostrar todos los datos
          const kpisData = await apiService.getKPIs({ pedidos: '' });
          setKpis(kpisData as KPIs);
        } else {
          // Si no hay pedidos, mostrar datos en cero
          console.log('No hay datos disponibles, mostrando datos en cero');
          loadData([]);
        }
      } catch (error) {
        console.error('Error verificando disponibilidad de datos:', error);
        // En caso de error, mostrar datos en cero
        loadData([]);
      }
    };
    
    checkDataAvailability();
  }, [dataLoaded]);

  // Efecto adicional para verificar datos cuando se monta el componente
  useEffect(() => {
    const verifyDataOnMount = async () => {
      // Si no hay dataLoaded pero el componente se monta, verificar si hay datos
      if (!dataLoaded) {
        try {
          const pedidos = await apiService.getPedidosFiltro();
          if (pedidos.length > 0) {
            console.log('Datos encontrados al montar componente, cargando...');
            await apiService.aplicarFiltrosPedido([]);
            const kpisData = await apiService.getKPIs({ pedidos: '' });
            setKpis(kpisData as KPIs);
          }
        } catch (error) {
          console.error('Error verificando datos al montar:', error);
        }
      }
    };
    
    verifyDataOnMount();
  }, []); // Solo se ejecuta al montar el componente

  // Recargar pedidos cuando hay un upload exitoso
  useEffect(() => {
    if (onUploadSuccess) {
      loadData([]);
    }
  }, [onUploadSuccess]);

  const handlePedidosChange = (pedidos: string[]) => {
    console.log('DashboardFiltrado recibiendo pedidos:', pedidos);
    setPedidosSeleccionados(pedidos);
    loadData(pedidos);
  };

  const handleClearPedidos = async () => {
    console.log('DashboardFiltrado limpiando pedidos');
    setPedidosSeleccionados([]);
    // Llamar a loadData con array vacío para establecer KPIs en cero
    loadData([]);
  };

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

  const formatExpectativaCobranzaData = (expectativa: Record<string, {cobranza_esperada: number, cobranza_real: number}>) => {
    return Object.entries(expectativa).map(([semana, datos]) => ({
      semana,
      cobranza_esperada: datos.cobranza_esperada,
      cobranza_real: datos.cobranza_real
    }));
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
        <span className="ml-2">Cargando datos filtrados...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={() => loadData(pedidosSeleccionados)}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Reintentar
        </Button>
      </div>
    );
  }

  if (!kpis) {
    return (
      <div className="text-center py-8">
        <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600">No hay datos disponibles. Sube un archivo para comenzar.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Indicador de filtrado */}
      {pedidosSeleccionados.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-600" />
            <span className="font-medium text-blue-800">
              Dashboard filtrado por {pedidosSeleccionados.length} pedido(s) seleccionado(s)
            </span>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="grid grid-cols-1 gap-6">
        <PedidoFilter
          onPedidosChange={handlePedidosChange}
          onClearPedidos={handleClearPedidos}
          onUploadSuccess={!!onUploadSuccess}
          dataLoaded={dataLoaded}
        />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {/* Facturación */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-blue-600" />
              <h3 className="text-sm font-medium text-gray-500">Facturación Total</h3>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.facturacion_total || 0)}</p>
            <p className="text-sm text-gray-500 mt-1">Sin IVA: {formatCurrency(kpis.facturacion_sin_iva || 0)}</p>
            <p className="text-sm text-gray-500">{kpis.total_facturas || 0} facturas</p>
          </div>
        </div>

        {/* Cobranza */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <h3 className="text-sm font-medium text-gray-500">Cobranza Total</h3>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.cobranza_total || 0)}</p>
            <p className="text-sm text-gray-500 mt-1">Sin IVA: {formatCurrency(kpis.cobranza_sin_iva || 0)}</p>
            <p className="text-sm text-green-600 mt-1 font-medium">% Cobrado: {(kpis.porcentaje_cobrado || 0).toFixed(1)}%</p>
          </div>
        </div>

        {/* Anticipos */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5 text-purple-600" />
              <h3 className="text-sm font-medium text-gray-500">Anticipos</h3>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(kpis.anticipos_total || 0)}</p>
            <p className="text-sm text-gray-500">{kpis.anticipos_porcentaje?.toFixed(1)}% sobre facturación</p>
          </div>
        </div>

        {/* Pedidos */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5 text-orange-600" />
              <h3 className="text-sm font-medium text-gray-500">Pedidos Utilizados</h3>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold text-gray-900">{kpis.pedidos_unicos || 0}</p>
            <p className="text-sm text-gray-500">{(kpis.toneladas_total || 0).toFixed(1)} toneladas</p>
          </div>
        </div>

        {/* Clientes */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-indigo-600" />
              <h3 className="text-sm font-medium text-gray-500">Clientes Únicos</h3>
            </div>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold text-gray-900">{kpis.clientes_unicos || 0}</p>
            <p className="text-sm text-gray-500">clientes activos</p>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {kpis.aging_cartera && Object.keys(kpis.aging_cartera).length > 0 && (
          <AgingChart data={formatAgingData(kpis.aging_cartera)} />
        )}
        
        {kpis.top_clientes && Object.keys(kpis.top_clientes).length > 0 && (
          <TopClientesChart data={formatTopClientesData(kpis.top_clientes)} />
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {kpis.consumo_material && Object.keys(kpis.consumo_material).length > 0 && (
          <ConsumoMaterialChart data={formatConsumoMaterialData(kpis.consumo_material)} />
        )}
        
        {kpis.expectativa_cobranza && Object.keys(kpis.expectativa_cobranza).length > 0 && (
          <ExpectativaCobranzaChart data={formatExpectativaCobranzaData(kpis.expectativa_cobranza)} />
        )}
      </div>
    </div>
  );
};
