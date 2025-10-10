import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ComprasV2FlujoPagosChartProps {
  data: Array<{ semana: string; liquidaciones: number; gastos_importacion: number; anticipo: number }>;
  moneda: 'USD' | 'MXN';
  onMonedaChange: (moneda: 'USD' | 'MXN') => void;
  titulo?: string;
}

export const ComprasV2FlujoPagosChart: FC<ComprasV2FlujoPagosChartProps> = ({ 
  data, 
  moneda, 
  onMonedaChange, 
  titulo = "Flujo de Pagos Semanal" 
}) => {
  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{titulo}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información de flujo de pagos</p>
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

  const formatCurrencyWithSymbol = (value: number) => {
    const formatted = formatCurrency(value);
    return `${formatted} ${moneda}`;
  };

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const allValues = data.flatMap(item => [item.liquidaciones, item.gastos_importacion, item.anticipo]);
  const maxValue = Math.max(...allValues);
  const minValue = Math.min(...allValues);
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{titulo}</CardTitle>
          <div className="flex space-x-2">
            <button
              onClick={() => onMonedaChange('USD')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                moneda === 'USD' 
                  ? 'bg-blue-100 text-blue-800 border border-blue-300' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              USD
            </button>
            <button
              onClick={() => onMonedaChange('MXN')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                moneda === 'MXN' 
                  ? 'bg-blue-100 text-blue-800 border border-blue-300' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              MXN
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[500px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 30, right: 40, left: 30, bottom: 100 }}
            >
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="#e5e7eb"
                strokeOpacity={0.7}
                verticalFill={['#f9fafb', '#ffffff']}
              />
              <XAxis
                dataKey="semana"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={90}
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
                  formatCurrencyWithSymbol(value),
                  name
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
                wrapperStyle={{ paddingTop: '20px' }}
              />
              <Bar
                dataKey="liquidaciones"
                stackId="a"
                fill="#10b981"
                name="Liquidaciones"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="gastos_importacion"
                stackId="a"
                fill="#f59e0b"
                name="Gastos de Importación"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="anticipo"
                stackId="a"
                fill="#3b82f6"
                name="Anticipo"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};