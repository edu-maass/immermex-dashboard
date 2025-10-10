import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface FlujoPagosChartProps {
  data: Array<{ semana: string; pagos: number; pendiente: number }>;
}

export const FlujoPagosChart: FC<FlujoPagosChartProps> = ({ data }) => {
  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Flujo de Pagos Semanal</CardTitle>
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

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const allValues = chartData.flatMap(item => [item.pagos, item.pendiente]);
  const maxValue = Math.max(...allValues);
  const minValue = Math.min(...allValues);
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Flujo de Pagos Semanal</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[500px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 30, right: 40, left: 30, bottom: 90 }}
            >
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="#e5e7eb"
                strokeOpacity={0.7}
                verticalFill={['#f9fafb', '#ffffff']}
              />
              <XAxis
                dataKey="semana"
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
                formatter={(value: number, name: string) => [
                  formatCurrency(value),
                  name === 'pagos' ? 'Pagos Realizados' : 'Pendiente'
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
              <Bar
                dataKey="pagos"
                fill="#10b981"
                name="Pagos Realizados"
                radius={[6, 6, 0, 0]}
              />
              <Bar
                dataKey="pendiente"
                fill="#f59e0b"
                name="Pendiente"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};