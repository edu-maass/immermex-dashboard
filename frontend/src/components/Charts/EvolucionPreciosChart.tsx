import { FC } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { DollarSign } from 'lucide-react';

interface EvolucionPreciosChartProps {
  data: Array<{ name: string; value: number }>;
  moneda: 'USD' | 'MXN';
  onMonedaChange: (moneda: 'USD' | 'MXN') => void;
  titulo?: string;
}

export const EvolucionPreciosChart: FC<EvolucionPreciosChartProps> = ({
  data,
  moneda,
  onMonedaChange,
  titulo = "Evolución de Precios por kg"
}) => {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{titulo}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <DollarSign className="h-12 w-12 mx-auto mb-4" />
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay datos de evolución de precios para mostrar</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Transformar datos para Recharts
  const chartData = data.map(item => ({
    mes: item.name,
    precio: item.value
  }));

  const formatTooltipValue = (value: number) => {
    return `${moneda} ${value.toFixed(2)}`;
  };

  const formatYAxisValue = (value: number) => {
    return `${moneda} ${value.toFixed(1)}`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{titulo}</CardTitle>
          <div className="flex gap-2">
            <Button
              variant={moneda === 'USD' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onMonedaChange('USD')}
            >
              USD
            </Button>
            <Button
              variant={moneda === 'MXN' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onMonedaChange('MXN')}
            >
              MXN
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="mes" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatYAxisValue}
              />
              <Tooltip 
                formatter={(value: number) => [formatTooltipValue(value), 'Precio por kg']}
                labelFormatter={(label) => `Mes: ${label}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="precio" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                name="Precio por kg"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
