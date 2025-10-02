import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { FileText, DollarSign } from 'lucide-react';

interface FlujoPagosChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      color: string;
    }>;
    totales?: number[];
    moneda?: string;
  };
  titulo?: string;
  moneda?: string;
  onMonedaChange?: (moneda: string) => void;
}

export const FlujoPagosChart: FC<FlujoPagosChartProps> = ({
  data,
  titulo = "Flujo de Pagos Semanal",
  moneda = 'USD',
  onMonedaChange
}) => {
  if (!data || !data.datasets || data.datasets.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{titulo}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <FileText className="h-12 w-12 mx-auto mb-4" />
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay datos de flujo de pagos para mostrar</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Transformar datos para Recharts (columnas apiladas)
  const chartData = data.labels.map((label, index) => {
    const dataPoint: any = { semana: label };
    data.datasets.forEach(dataset => {
      dataPoint[dataset.label] = dataset.data[index] || 0;
    });
    // Agregar total si está disponible
    if (data.totales && data.totales[index]) {
      dataPoint['Total'] = data.totales[index];
    }
    return dataPoint;
  });

  const formatTooltipValue = (value: number) => {
    const currency = moneda || data.moneda || 'USD';
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatYAxisValue = (value: number) => {
    const currency = moneda || data.moneda || 'USD';
    const symbol = currency === 'USD' ? '$' : '$';
    
    if (value >= 1000000) {
      return `${symbol}${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${symbol}${(value / 1000).toFixed(1)}K`;
    }
    return `${symbol}${value}`;
  };

  const handleMonedaChange = () => {
    if (onMonedaChange) {
      const newMoneda = moneda === 'USD' ? 'MXN' : 'USD';
      onMonedaChange(newMoneda);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{titulo}</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleMonedaChange}
            className="flex items-center gap-2"
          >
            <DollarSign className="h-4 w-4" />
            {moneda || data.moneda || 'USD'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="semana" 
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
                formatter={(value: number, name: string) => [formatTooltipValue(value), name]}
                labelFormatter={(label) => `Semana: ${label}`}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              {data.datasets.map((dataset, index) => (
                <Bar 
                  key={index}
                  dataKey={dataset.label} 
                  fill={dataset.color}
                  name={dataset.label}
                  stackId="pagos"
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
