import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { KPICard } from './KPICard';
import { FileUpload } from './FileUpload';
import { LoadingSpinner } from './LoadingSpinner';
import { Tooltip } from './ui/tooltip';
import { apiService } from '../services/api';
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Truck,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  Upload,
  FileSpreadsheet
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
}

interface ComprasV2Data {
  success: boolean;
  compras: any[];
  total_compras: number;
  filtros_aplicados: any;
}

export const ComprasV2Dashboard: React.FC<ComprasV2DashboardProps> = ({ onUploadSuccess }) => {
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

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Cargar KPIs y datos en paralelo
      const [kpisResponse, dataResponse] = await Promise.all([
        apiService.getComprasV2KPIs(filtros),
        apiService.getComprasV2Data(filtros, 50)
      ]);

      setKpis(kpisResponse);
      setComprasData(dataResponse);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
      console.error('Error loading compras_v2 data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filtros]);


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

  const hasActiveFilters = Object.values(filtros).some(value => value !== undefined);


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
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Proveedor
              </label>
              <input
                type="text"
                value={filtros.proveedor || ''}
                onChange={(e) => handleFilterChange('proveedor', e.target.value)}
                placeholder="Filtrar por proveedor..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Material
              </label>
              <input
                type="text"
                value={filtros.material || ''}
                onChange={(e) => handleFilterChange('material', e.target.value)}
                placeholder="Filtrar por material..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
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

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Total Compras"
          value={kpis.total_compras || 0}
          icon={Package}
          color="blue"
          loading={loading}
        />
        <KPICard
          title="Total Proveedores"
          value={kpis.total_proveedores || 0}
          icon={Truck}
          color="green"
          loading={loading}
        />
        <KPICard
          title="Total KG"
          value={kpis.total_kilogramos ? kpis.total_kilogramos.toLocaleString() : '0'}
          icon={TrendingUp}
          color="purple"
          loading={loading}
        />
        <KPICard
          title="Costo Total MXN"
          value={kpis.total_costo_mxn ? `$${kpis.total_costo_mxn.toLocaleString()}` : '$0'}
          icon={DollarSign}
          color="orange"
          loading={loading}
        />
      </div>

      {/* KPIs adicionales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Compras con Anticipo"
          value={kpis.compras_con_anticipo || 0}
          icon={CheckCircle}
          color="green"
          loading={loading}
        />
        <KPICard
          title="Compras Pagadas"
          value={kpis.compras_pagadas || 0}
          icon={CheckCircle}
          color="blue"
          loading={loading}
        />
        <KPICard
          title="Tipo Cambio Promedio"
          value={kpis.tipo_cambio_promedio ? kpis.tipo_cambio_promedio.toFixed(2) : '0.00'}
          icon={TrendingUp}
          color="purple"
          loading={loading}
        />
        <KPICard
          title="Costo Total USD"
          value={kpis.total_costo_divisa ? `$${kpis.total_costo_divisa.toLocaleString()}` : '$0'}
          icon={DollarSign}
          color="orange"
          loading={loading}
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
