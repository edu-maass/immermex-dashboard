import { FC, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ComprasV2EvolucionPreciosChartProps {
  data: Array<{ fecha: string; precio_promedio: number; precio_min: number; precio_max: number }>;
  moneda: 'USD' | 'MXN';
  titulo?: string;
  onMonedaChange?: (moneda: 'USD' | 'MXN') => void;
}

export const ComprasV2EvolucionPreciosChart: FC<ComprasV2EvolucionPreciosChartProps> = ({ 
  data, 
  moneda, 
  titulo = "Evolucion Precio Unitario",
  onMonedaChange 
}) => {
  const [periodo, setPeriodo] = useState<'todos' | 'ytd' | '2años' | '3meses' | '1mes'>('todos');

  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{titulo}</CardTitle>
          <div className="flex gap-2 mt-2">
            {onMonedaChange && (
              <>
                <button
                  onClick={() => onMonedaChange('USD')}
                  className={`px-3 py-1 text-xs rounded ${
                    moneda === 'USD' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  USD
                </button>
                <button
                  onClick={() => onMonedaChange('MXN')}
                  className={`px-3 py-1 text-xs rounded ${
                    moneda === 'MXN' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  MXN
                </button>
              </>
            )}
            <select
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value as any)}
              className="px-2 py-1 text-xs rounded border border-gray-300 bg-white"
            >
              <option value="todos">Todos los datos</option>
              <option value="ytd">YTD</option>
              <option value="2años">2 años</option>
              <option value="3meses">3 meses</option>
              <option value="1mes">1 mes</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información de precios</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (value: number) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0';
    }
    return new Intl.NumberFormat(moneda === 'USD' ? 'en-US' : 'es-MX', {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-MX', {
        month: 'short',
        year: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  // Filter data based on selected period
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const now = new Date();
    let cutoffDate: Date;
    
    switch (periodo) {
      case 'ytd':
        cutoffDate = new Date(now.getFullYear(), 0, 1); // Start of current year
        break;
      case '2años':
        cutoffDate = new Date(now.getFullYear() - 2, now.getMonth(), now.getDate());
        break;
      case '3meses':
        cutoffDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
        break;
      case '1mes':
        cutoffDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
        break;
      default:
        return data; // Return all data for 'todos'
    }
    
    return data.filter(item => {
      try {
        const itemDate = new Date(item.fecha);
        return itemDate >= cutoffDate;
      } catch {
        return true; // Keep item if date parsing fails
      }
    });
  }, [data, periodo]);

  // Format data for the chart
  const chartData = filteredData.map(item => ({
    fecha: formatDate(item.fecha),
    precio_promedio: item.precio_promedio,
    precio_min: item.precio_min,
    precio_max: item.precio_max
  }));

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const allValues = chartData.flatMap(item => [item.precio_promedio, item.precio_min, item.precio_max]);
  const maxValue = Math.max(...allValues);
  const minValue = Math.min(...allValues);
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
        <div className="flex gap-2 mt-2">
          {onMonedaChange && (
            <>
              <button
                onClick={() => onMonedaChange('USD')}
                className={`px-3 py-1 text-xs rounded ${
                  moneda === 'USD' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                USD
              </button>
              <button
                onClick={() => onMonedaChange('MXN')}
                className={`px-3 py-1 text-xs rounded ${
                  moneda === 'MXN' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                }`}
              >
                MXN
              </button>
            </>
          )}
          <select
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value as any)}
            className="px-2 py-1 text-xs rounded border border-gray-300 bg-white"
          >
            <option value="todos">Todos los datos</option>
            <option value="ytd">YTD</option>
            <option value="2años">2 años</option>
            <option value="3meses">3 meses</option>
            <option value="1mes">1 mes</option>
          </select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 30, right: 40, left: 30, bottom: 90 }}
            >
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="#e5e7eb"
                strokeOpacity={0.7}
                verticalFill={['#f9fafb', '#ffffff']}
              />
              <XAxis
                dataKey="fecha"
                tick={{ fontSize: 13 }}
                angle={-45}
                textAnchor="end"
                height={80}
                stroke="#6b7280"
              />
              <YAxis
                tick={{ fontSize: 13 }}
                tickFormatter={formatCurrency}
                domain={yAxisDomain}
                stroke="#6b7280"
                tickCount={8}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  formatCurrency(value),
                  name === 'precio_promedio' ? 'Precio Promedio' :
                  name === 'precio_min' ? 'Precio Mínimo' :
                  name === 'precio_max' ? 'Precio Máximo' : name
                ]}
                labelStyle={{ color: '#374151', fontWeight: 600 }}
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  padding: '12px'
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '10px' }}
              />
              <Line
                type="monotone"
                dataKey="precio_promedio"
                stroke="#2563eb"
                strokeWidth={3}
                dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#2563eb', strokeWidth: 2 }}
                name="Precio Promedio"
              />
              <Line
                type="monotone"
                dataKey="precio_min"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#10b981', strokeWidth: 2, r: 3 }}
                name="Precio Mínimo"
              />
              <Line
                type="monotone"
                dataKey="precio_max"
                stroke="#ef4444"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 3 }}
                name="Precio Máximo"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};




