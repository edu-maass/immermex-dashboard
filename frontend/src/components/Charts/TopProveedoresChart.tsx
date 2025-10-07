import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TopProveedoresChartProps {
  data: Array<{ proveedor: string; total_kg: number }>;
  titulo?: string;
}

export const TopProveedoresChart: FC<TopProveedoresChartProps> = ({ 
  data, 
  titulo = "Top Proveedores por KG Comprados"
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
              <p className="text-sm">No hay información de proveedores</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatKg = (value: number) => {
    if (value >= 1000000) return `${Math.round(value / 1000000)}M kg`;
    if (value >= 1000) return `${Math.round(value / 1000)}K kg`;
    return `${value.toFixed(0)} kg`;
  };

  // Format data for the chart
  const chartData = data.map(item => ({
    proveedor: item.proveedor.length > 15 ? item.proveedor.substring(0, 15) + '...' : item.proveedor,
    total_kg: item.total_kg,
    fullName: item.proveedor // Keep full name for tooltip
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
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
                dataKey="proveedor"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={formatKg}
              />
              <Tooltip
                formatter={(value: number) => [
                  formatKg(value),
                  'KG Comprados'
                ]}
                labelFormatter={(label, payload) => {
                  if (payload && payload[0] && payload[0].payload) {
                    return payload[0].payload.fullName;
                  }
                  return label;
                }}
                labelStyle={{ color: '#374151' }}
                contentStyle={{
                  backgroundColor: '#f9fafb',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Bar
                dataKey="total_kg"
                fill="#3b82f6"
                name="KG Comprados"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
