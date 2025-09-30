import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface CobranzaPedidosChartProps {
  data: Array<{ semana: string; cobranza_esperada: number; cobranza_real: number }>;
}

export const CobranzaPedidosChart: FC<CobranzaPedidosChartProps> = ({ data }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Función para formatear las etiquetas del eje X
  const formatXAxisLabel = (semana: string) => {
    // Formato: "Semana X (DD/MM - DD/MM)" -> extraer semana del año y fecha de inicio
    const match = semana.match(/Semana (\d+) \((\d{2}\/\d{2})/);
    if (match) {
      const semanaNum = match[1];
      const fechaInicio = match[2]; // "DD/MM"
      return `S${semanaNum} (${fechaInicio})`;
    }
    return semana;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cobranza</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={data} 
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="semana"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
                tickFormatter={formatXAxisLabel}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
              />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  formatCurrency(value), 
                  name === 'cobranza_esperada' ? 'Esperada' : name === 'cobranza_real' ? 'Cobrado' : name
                ]}
                labelStyle={{ color: '#374151' }}
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px'
                }}
              />
              <Bar 
                dataKey="cobranza_esperada" 
                fill="#3b82f6"
                name="Esperada"
                stackId="cobranza"
                radius={[0, 0, 0, 0]}
              />
              <Bar 
                dataKey="cobranza_real" 
                fill="#10b981"
                name="Cobrado"
                stackId="cobranza"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
