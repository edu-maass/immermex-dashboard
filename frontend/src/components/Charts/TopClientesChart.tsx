import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface TopClientesChartProps {
  data: Array<{ name: string; value: number }>;
}

export const TopClientesChart: FC<TopClientesChartProps> = ({ data }) => {
  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top 10 Clientes por Facturación</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información de clientes</p>
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

  // Limitar a 10 clientes y truncar nombres a 20 caracteres
  const limitedData = data.slice(0, 10).map(item => ({
    ...item,
    name: item.name.length > 20 ? item.name.substring(0, 20) + '...' : item.name
  }));

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const maxValue = Math.max(...limitedData.map(item => item.value));
  const minValue = Math.min(...limitedData.map(item => item.value));
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top 10 Clientes por Facturación</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[500px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={limitedData} 
              margin={{ top: 30, right: 40, left: 30, bottom: 90 }}
            >
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
                tickFormatter={formatCurrency}
                domain={yAxisDomain}
                stroke="#6b7280"
                tickCount={8}
              />
              <Tooltip 
                formatter={(value: number) => [formatCurrency(value), 'Facturación']}
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
                name="Facturación"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};