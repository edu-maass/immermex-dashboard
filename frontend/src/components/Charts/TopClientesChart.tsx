import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface TopClientesChartProps {
  data: Array<{ name: string; value: number }>;
}

export const TopClientesChart: FC<TopClientesChartProps> = ({ data }) => {
  console.log('TopClientesChart component received data:', data);
  
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

  console.log('TopClientesChart limitedData:', limitedData);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top 10 Clientes por Facturación</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={limitedData} 
              layout="horizontal"
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                type="number"
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
              />
              <YAxis 
                type="category"
                dataKey="name"
                tick={{ fontSize: 12 }}
                width={150}
              />
              <Tooltip 
                formatter={(value: number) => [formatCurrency(value), 'Facturación']}
                labelStyle={{ color: '#374151' }}
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px'
                }}
              />
              <Bar 
                dataKey="value" 
                fill="#3b82f6"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};