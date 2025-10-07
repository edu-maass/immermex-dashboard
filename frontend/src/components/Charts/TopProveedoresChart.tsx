import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TopProveedoresChartProps {
  data: Array<{ proveedor: string; total_kg: number; total_compras?: number; precio_unitario?: number }>;
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

  const formatTons = (value: number) => {
    const tons = value / 1000;
    if (tons >= 1000) return `${Math.round(tons / 1000)}K ton`;
    return `${tons.toFixed(1)} ton`;
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${Math.round(value / 1000000)}M`;
    if (value >= 1000) return `$${Math.round(value / 1000)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatPricePerKg = (value: number) => {
    return `$${value.toFixed(2)}`;
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
                tickFormatter={formatTons}
              />
              <Tooltip
                formatter={(value: number, name: string, props: any) => {
                  const payload = props.payload;
                  return [
                    <div key="tooltip-content" className="space-y-1">
                      <div className="font-semibold text-blue-600">
                        {formatTons(payload.total_kg)}
                      </div>
                      {payload.total_compras && (
                        <div className="text-sm text-gray-600">
                          Monto: {formatCurrency(payload.total_compras)}
                        </div>
                      )}
                      {payload.precio_unitario && (
                        <div className="text-sm text-gray-600">
                          Precio unitario: {formatPricePerKg(payload.precio_unitario)} MXN/kg
                        </div>
                      )}
                    </div>
                  ];
                }}
                labelFormatter={(label, payload) => {
                  if (payload && payload[0] && payload[0].payload) {
                    return payload[0].payload.fullName;
                  }
                  return label;
                }}
                labelStyle={{ color: '#374151', fontWeight: 'bold' }}
                contentStyle={{
                  backgroundColor: '#f9fafb',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '12px',
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
