import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface AgingChartProps {
  data: Array<{ name: string; value: number; color?: string }>;
}

export const AgingChart: FC<AgingChartProps> = ({ data }) => {
  const colors = {
    '0-30 días': '#10b981',
    '31-60 días': '#f59e0b',
    '61-90 días': '#f97316',
    '90+ días': '#ef4444'
  };

  const chartData = data.map(item => ({
    ...item,
    color: colors[item.name as keyof typeof colors] || '#6b7280'
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aging de Cartera</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
              />
              <Tooltip 
                formatter={(value: number) => [`$${value.toLocaleString('es-MX', { maximumFractionDigits: 0 })}`, 'Monto']}
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
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
