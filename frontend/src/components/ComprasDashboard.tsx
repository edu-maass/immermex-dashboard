import { FC, useState, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Calendar,
  ShoppingCart,
  AlertCircle,
  RefreshCw,
  Building,
  FileText,
  Clock,
  Percent
} from 'lucide-react';
import { apiService } from '../services/api';
import { LoadingSpinner } from './LoadingSpinner';
import { EvolucionPreciosChart } from './Charts/EvolucionPreciosChart';
import { FlujoPagosChart } from './Charts/FlujoPagosChart';
import { AgingCuentasPagarChart } from './Charts/AgingCuentasPagarChart';

interface ComprasDashboardProps {
  onUploadSuccess?: () => void;
  dataLoaded?: boolean;
}

export const ComprasDashboard: FC<ComprasDashboardProps> = ({ onUploadSuccess, dataLoaded }) => {
  const [kpis, setKpis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<{ mes?: number; año?: number; material?: string; proveedor?: string }>({});
  const [materiales, setMateriales] = useState<string[]>([]);
  const [proveedores, setProveedores] = useState<string[]>([]);
  const [monedaPrecios, setMonedaPrecios] = useState<'USD' | 'MXN'>('USD');
  const [monedaFlujoPagos, setMonedaFlujoPagos] = useState<'USD' | 'MXN'>('USD');
  const [evolucionPrecios, setEvolucionPrecios] = useState<any>(null);
  const [flujoPagos, setFlujoPagos] = useState<any>(null);
  const [agingCuentasPagar, setAgingCuentasPagar] = useState<any>(null);

  const loadComprasData = async (filtrosAplicados: any = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const comprasKpis = await apiService.getComprasKPIs(filtrosAplicados);
      setKpis(comprasKpis);
    } catch (err) {
      console.error('Error cargando datos de compras:', err);
      setError('Error cargando datos de compras');
    } finally {
      setLoading(false);
    }
  };

  const loadMateriales = async () => {
    try {
      const materialesData = await apiService.getMaterialesCompras();
      setMateriales(materialesData);
    } catch (err) {
      console.error('Error cargando materiales:', err);
    }
  };

  const loadProveedores = async () => {
    try {
      const proveedoresData = await apiService.getProveedoresCompras();
      setProveedores(proveedoresData);
    } catch (err) {
      console.error('Error cargando proveedores:', err);
    }
  };

  const loadChartData = async () => {
    try {
      // Cargar evolución de precios
      const evolucionData = await apiService.getEvolucionPrecios(filtros.material, monedaPrecios);
      setEvolucionPrecios(evolucionData);

      // Cargar flujo de pagos
      const flujoData = await apiService.getFlujoPagosCompras(filtros, monedaFlujoPagos);
      setFlujoPagos(flujoData);

      // Cargar aging de cuentas por pagar
      const agingData = await apiService.getAgingCuentasPagar(filtros);
      setAgingCuentasPagar(agingData);
    } catch (err) {
      console.error('Error cargando datos de gráficos:', err);
    }
  };

  useEffect(() => {
    loadComprasData(filtros);
    loadMateriales();
    loadProveedores();
    loadChartData();
  }, [filtros, monedaPrecios, monedaFlujoPagos]);

  const handleFiltroChange = (campo: string, valor: any) => {
    setFiltros(prev => ({
      ...prev,
      [campo]: valor || undefined
    }));
  };

  const handleClearFilters = () => {
    setFiltros({});
  };

  const handleMonedaFlujoPagosChange = async (nuevaMoneda: string) => {
    setMonedaFlujoPagos(nuevaMoneda as 'USD' | 'MXN');
    // Recargar datos del flujo de pagos con la nueva moneda
    try {
      const flujoData = await apiService.getFlujoPagosCompras(filtros, nuevaMoneda);
      setFlujoPagos(flujoData);
    } catch (err) {
      console.error('Error recargando flujo de pagos:', err);
    }
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

  if (loading && !kpis) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Cargando datos de compras...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={() => loadComprasData(filtros)}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Reintentar
        </Button>
      </div>
    );
  }

  if (!kpis) {
    return (
      <div className="text-center py-8">
        <ShoppingCart className="h-12 w-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600">No hay datos de compras disponibles. Sube un archivo para comenzar.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mes</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filtros.mes || ''}
                onChange={(e) => handleFiltroChange('mes', e.target.value ? parseInt(e.target.value) : undefined)}
              >
                <option value="">Todos los meses</option>
                <option value="1">Enero</option>
                <option value="2">Febrero</option>
                <option value="3">Marzo</option>
                <option value="4">Abril</option>
                <option value="5">Mayo</option>
                <option value="6">Junio</option>
                <option value="7">Julio</option>
                <option value="8">Agosto</option>
                <option value="9">Septiembre</option>
                <option value="10">Octubre</option>
                <option value="11">Noviembre</option>
                <option value="12">Diciembre</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Año</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filtros.año || ''}
                onChange={(e) => handleFiltroChange('año', e.target.value ? parseInt(e.target.value) : undefined)}
              >
                <option value="">Todos los años</option>
                {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(año => (
                  <option key={año} value={año}>{año}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Proveedor</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filtros.proveedor || ''}
                onChange={(e) => handleFiltroChange('proveedor', e.target.value || undefined)}
              >
                <option value="">Todos los proveedores</option>
                {proveedores.map((proveedor, index) => (
                  <option key={index} value={proveedor}>{proveedor}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Material</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filtros.material || ''}
                onChange={(e) => handleFiltroChange('material', e.target.value || undefined)}
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
          <div className="mt-4">
            <Button variant="outline" onClick={handleClearFilters}>
              Limpiar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* KPIs Principales de Compras */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Compras */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Compras</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(kpis.total_compras || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {kpis.total_compras_usd ? formatCurrencyUSD(kpis.total_compras_usd) : ''}
            </p>
          </CardContent>
        </Card>

        {/* Compras Pendientes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compras Pendientes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(kpis.compras_pendientes || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {kpis.compras_pendientes_count || 0} facturas pendientes
            </p>
          </CardContent>
        </Card>

        {/* Promedio por Proveedor */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Promedio por Proveedor</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(kpis.promedio_por_proveedor || 0)}</div>
            <p className="text-xs text-muted-foreground">
              {kpis.proveedores_unicos || 0} proveedores activos
            </p>
          </CardContent>
        </Card>

        {/* Días Promedio de Crédito */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Días Promedio Crédito</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.dias_credito_promedio || 0}</div>
            <p className="text-xs text-muted-foreground">
              días promedio
            </p>
          </CardContent>
        </Card>
      </div>

      {/* KPIs Adicionales - Combinando Compras y Pedidos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Margen Bruto Promedio */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Margen Bruto Promedio</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(kpis.margen_bruto_promedio || 0).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Precio venta vs costo compra
            </p>
          </CardContent>
        </Card>

        {/* Rotación de Inventario */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rotación Inventario</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(kpis.rotacion_inventario || 0).toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">
              veces por año
            </p>
          </CardContent>
        </Card>

        {/* Ciclo de Compras */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ciclo de Compras</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.ciclo_compras || 0}</div>
            <p className="text-xs text-muted-foreground">
              días promedio
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Evolución de Precios */}
        <EvolucionPreciosChart
          data={evolucionPrecios ? evolucionPrecios.labels.map((label: string, index: number) => ({
            name: label,
            value: evolucionPrecios.data[index] || 0
          })) : []}
          moneda={monedaPrecios}
          onMonedaChange={setMonedaPrecios}
          titulo={evolucionPrecios?.titulo}
        />

        {/* Flujo de Pagos */}
        <FlujoPagosChart
          data={flujoPagos || { labels: [], datasets: [] }}
          titulo={flujoPagos?.titulo}
          moneda={monedaFlujoPagos}
          onMonedaChange={handleMonedaFlujoPagosChange}
        />
      </div>

      {/* Aging de Cuentas por Pagar */}
      <AgingCuentasPagarChart
        data={agingCuentasPagar ? agingCuentasPagar.labels.map((label: string, index: number) => ({
          name: label,
          value: agingCuentasPagar.data[index] || 0
        })) : []}
        titulo={agingCuentasPagar?.titulo}
      />
    </div>
  );
};
