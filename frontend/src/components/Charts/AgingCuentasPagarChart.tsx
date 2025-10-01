import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Clock } from 'lucide-react';

interface AgingCuentasPagarChartProps {
  data: Array<{ name: string; value: number }>;
  titulo?: string;
}

export const AgingCuentasPagarChart: FC<AgingCuentasPagarChartProps> = ({
  data,
  titulo = "Aging de Cuentas por Pagar"
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
              <Clock className="h-12 w-12 mx-auto mb-4" />
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay datos de aging de cuentas por pagar para mostrar</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Transformar datos para Recharts
  const chartData = data.map(item => ({
    periodo: item.name,
    monto: item.value
  }));

  // Definir colores por período
  const getBarColor = (periodo: string) => {
    if (periodo.includes('0-30')) return '#10b981'; // Verde para vencido reciente
    if (periodo.includes('31-60')) return '#f59e0b'; // Amarillo para moderado
    if (periodo.includes('61-90')) return '#f97316'; // Naranja para alto
    return '#ef4444'; // Rojo para muy alto
  };

  const formatTooltipValue = (value: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatYAxisValue = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="periodo" 
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatYAxisValue}
              />
              <Tooltip 
                formatter={(value: number) => [formatTooltipValue(value), 'Monto']}
                labelFormatter={(label) => `Período: ${label}`}
              />
              <Bar 
                dataKey="monto" 
                fill={(entry: any) => getBarColor(entry.periodo)}
                name="Monto por Pagar"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>0-30 días</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>31-60 días</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-orange-500 rounded"></div>
            <span>61-90 días</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>90+ días</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
