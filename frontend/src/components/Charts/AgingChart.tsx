import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface AgingChartProps {
  data: Array<{ name: string; value: number; color?: string }>;
}

export const AgingChart: FC<AgingChartProps> = ({ data }) => {
  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Aging de Cartera</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información de aging de cartera</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const colors = {
    '0-30 dias': '#10b981',
    '31-60 dias': '#f59e0b',
    '61-90 dias': '#f97316',
    '90+ dias': '#ef4444'
  };

  const chartData = data.map(item => ({
    ...item,
    color: colors[item.name as keyof typeof colors] || '#6b7280'
  }));

  // Si todos los valores son 0, mostrar mensaje
  const allZero = data.every(item => item.value === 0);

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const maxValue = Math.max(...data.map(item => item.value));
  const minValue = Math.min(...data.map(item => item.value));
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aging de Cartera</CardTitle>
      </CardHeader>
      <CardContent>
        {allZero ? (
          <div className="h-[500px] flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin saldos pendientes</p>
              <p className="text-sm">Todas las facturas están completamente cobradas</p>
            </div>
          </div>
        ) : (
          <div className="h-[500px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 30, right: 40, left: 30, bottom: 80 }}>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="#e5e7eb"
                  strokeOpacity={0.7}
                  verticalFill={['#f9fafb', '#ffffff']}
                />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 13 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  stroke="#6b7280"
                />
                <YAxis 
                  tick={{ fontSize: 13 }}
                  tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                  domain={yAxisDomain}
                  stroke="#6b7280"
                  tickCount={8}
                />
                <Tooltip 
                  formatter={(value: number) => [`$${value.toLocaleString('es-MX', { maximumFractionDigits: 0 })}`, 'Monto']}
                  labelStyle={{ color: '#374151', fontWeight: 600 }}
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    padding: '12px'
                  }}
                />
                <Bar 
                  dataKey="value" 
                  fill="#3b82f6"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
