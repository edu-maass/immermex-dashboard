import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConsumoMaterialChartProps {
  data: Array<{ name: string; value: number }>;
}

export const ConsumoMaterialChart: FC<ConsumoMaterialChartProps> = ({ data }) => {
  console.log('ConsumoMaterialChart component received data:', data);
  
  const COLORS = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
  ];

  const formatWeight = (value: number) => {
    return `${value.toLocaleString('es-MX')} kg`;
  };

  console.log('ConsumoMaterialChart data length:', data.length);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Consumo por Material</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80 bg-purple-100 border-2 border-orange-500">
          <p className="p-2">ConsumoMaterialChart Container</p>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={data.slice(0, 5)}>
              <XAxis dataKey="name" />
              <YAxis />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
