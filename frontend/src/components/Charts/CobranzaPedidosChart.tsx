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

  // Calcular el dominio del eje Y para mostrar un rango relevante
  const allValues = data.flatMap(item => [item.cobranza_esperada, item.cobranza_real]);
  const maxValue = Math.max(...allValues);
  const minValue = Math.min(...allValues);
  const yAxisDomain = [
    Math.max(0, minValue - (maxValue - minValue) * 0.1), // 10% padding inferior
    maxValue + (maxValue - minValue) * 0.15 // 15% padding superior
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cobranza</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={data} 
              margin={{ top: 30, right: 40, left: 50, bottom: 90 }}
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
                tickFormatter={formatXAxisLabel}
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
                  name === 'cobranza_esperada' ? 'Esperada' : name === 'cobranza_real' ? 'Cobrado' : name
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
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
