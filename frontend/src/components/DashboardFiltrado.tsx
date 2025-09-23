import { FC, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
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
}

export const DashboardFiltrado: FC<DashboardFiltradoProps> = ({ onUploadSuccess }) => {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pedidosSeleccionados, setPedidosSeleccionados] = useState<string[]>([]);

  const loadData = async (pedidosAplicar?: string[]) => {
    console.log('loadData llamado con pedidos:', pedidosAplicar);
    setLoading(true);
    setError(null);
    
    try {
      // Aplicar filtros de pedido si existen
      if (pedidosAplicar && pedidosAplicar.length > 0) {
        console.log('Aplicando filtros de pedido:', pedidosAplicar);
        await apiService.aplicarFiltrosPedido(pedidosAplicar);
      } else {
        console.log('Sin filtros de pedido, usando datos originales');
        // Si no hay pedidos seleccionados, no aplicar filtros (usar datos originales)
        // No llamar a aplicarFiltrosPedido([]) para evitar limpiar los datos
      }
      
      // Obtener KPIs
      console.log('Obteniendo KPIs...');
      const kpisData = await apiService.getKPIs();
      console.log('KPIs obtenidos:', kpisData);
      setKpis(kpisData);
      
    } catch (err) {
      console.error('Error cargando datos:', err);
      setError('Error cargando datos del dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePedidosChange = (pedidos: string[]) => {
    console.log('DashboardFiltrado recibiendo pedidos:', pedidos);
    setPedidosSeleccionados(pedidos);
    loadData(pedidos);
  };

  const handleClearPedidos = async () => {
    console.log('DashboardFiltrado limpiando pedidos');
    setPedidosSeleccionados([]);
    // No llamar a aplicarFiltrosPedido([]) para evitar limpiar los datos
    // Solo recargar con datos originales
    loadData();
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
        <Button onClick={() => loadData(filtros, pedidosSeleccionados)}>
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
        />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Facturación */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Facturación Total</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(kpis.facturacion_total || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {kpis.total_facturas || 0} facturas
            </p>
          </CardContent>
        </Card>

        {/* Cobranza */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cobranza Total</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(kpis.cobranza_total || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {(kpis.porcentaje_cobrado || 0).toFixed(1)}% cobrado
            </p>
          </CardContent>
        </Card>

        {/* Pedidos */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pedidos Utilizados</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.pedidos_unicos || 0}</div>
            <p className="text-xs text-muted-foreground">
              {(kpis.toneladas_total || 0).toFixed(1)} toneladas
            </p>
          </CardContent>
        </Card>

        {/* Clientes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Clientes Únicos</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.clientes_unicos || 0}</div>
            <p className="text-xs text-muted-foreground">
              clientes activos
            </p>
          </CardContent>
        </Card>
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
