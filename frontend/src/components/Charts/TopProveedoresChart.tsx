import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TopProveedoresChartProps {
  data: Array<{ proveedor: string; total_kg: number; total_compras?: number; precio_unitario?: number }>;
  titulo?: string;
}

export const TopProveedoresChart: FC<TopProveedoresChartProps> = ({ 
  data, 
  titulo = "Top Proveedores"
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
    return `${tons.toLocaleString('es-MX', { maximumFractionDigits: 0 })} ton`;
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

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const maxValue = Math.max(...chartData.map(item => item.total_kg));
  const minValue = Math.min(...chartData.map(item => item.total_kg));
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
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
                dataKey="proveedor"
                tick={{ fontSize: 13 }}
                angle={-45}
                textAnchor="end"
                height={80}
                stroke="#6b7280"
              />
              <YAxis
                tick={{ fontSize: 13 }}
                tickFormatter={formatTons}
                domain={yAxisDomain}
                stroke="#6b7280"
                tickCount={8}
              />
              <Tooltip
                formatter={(_value: number, _name: string, props: any) => {
                  const payload = props.payload;
                  return [
                    <div key="tooltip-content" className="space-y-1">
                      <div className="font-semibold text-blue-600">
                        {formatTons(payload.total_kg)}
                      </div>
                      {payload.total_compras && (
                        <div className="text-sm text-gray-600">
                          Costo Total: {formatCurrency(payload.total_compras)}
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
                labelStyle={{ color: '#374151', fontWeight: 600 }}
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  padding: '12px',
                }}
              />
              <Bar
                dataKey="total_kg"
                fill="#3b82f6"
                name="KG Comprados"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
