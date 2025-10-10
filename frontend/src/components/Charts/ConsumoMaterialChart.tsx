import { FC } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConsumoMaterialChartProps {
  data: Array<{ name: string; value: number }>;
}

export const ConsumoMaterialChart: FC<ConsumoMaterialChartProps> = ({ data }) => {
  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Ventas por Material</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos de ventas disponibles</p>
              <p className="text-sm">No hay información de ventas por material</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const COLORS = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
  ];

  const formatWeight = (value: number) => {
    return `${value.toLocaleString('es-MX')} kg`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Consumo por Material</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="45%"
                innerRadius={70}
                outerRadius={140}
                labelLine={true}
                label={(props: any) => {
                  const { name, percent } = props || {};
                  const pct = typeof percent === 'number' ? percent : 0;
                  return `${name ?? ''} (${(pct * 100).toFixed(1)}%)`;
                }}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: number) => [formatWeight(value), 'Consumo']}
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
                verticalAlign="bottom" 
                height={60}
                wrapperStyle={{ paddingTop: '20px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
