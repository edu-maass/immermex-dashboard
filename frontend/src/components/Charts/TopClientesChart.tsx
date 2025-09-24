import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
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
        <div className="h-80 w-full bg-yellow-100 border-2 border-green-500">
          <p className="p-2">TopClientesChart Container</p>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={limitedData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};