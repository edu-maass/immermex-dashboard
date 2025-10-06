import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ComprasV2FlujoPagosChartProps {
  data: Array<{ semana: string; pagos: number; pendiente: number }>;
  moneda: 'USD' | 'MXN';
  titulo?: string;
  onMonedaChange?: (moneda: 'USD' | 'MXN') => void;
}

export const ComprasV2FlujoPagosChart: FC<ComprasV2FlujoPagosChartProps> = ({ 
  data, 
  moneda, 
  titulo = "Flujo de Pagos Semanal",
  onMonedaChange 
}) => {
  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{titulo}</CardTitle>
          {onMonedaChange && (
            <div className="flex gap-2 mt-2">
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
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información de pagos</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${Math.round(value / 1000000)}M`;
    if (value >= 1000) return `$${Math.round(value / 1000)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatWeek = (weekString: string) => {
    // Format week string like "Semana 1" or "Week 1"
    if (weekString.includes('Semana')) return weekString;
    if (weekString.includes('Week')) return weekString.replace('Week', 'Semana');
    return `Semana ${weekString}`;
  };

  // Format data for the chart
  const chartData = data.map(item => ({
    semana: formatWeek(item.semana),
    pagos: item.pagos,
    pendiente: item.pendiente
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
        {onMonedaChange && (
          <div className="flex gap-2 mt-2">
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
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="semana"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  formatCurrency(value),
                  name === 'pagos' ? 'Pagos Realizados' : 'Pendiente'
                ]}
                labelStyle={{ color: '#374151' }}
                contentStyle={{
                  backgroundColor: '#f9fafb',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Bar
                dataKey="pagos"
                fill="#10b981"
                name="Pagos Realizados"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="pendiente"
                fill="#f59e0b"
                name="Pendiente"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

