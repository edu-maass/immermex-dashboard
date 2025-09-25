import { FC } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface CobranzaFuturaChartProps {
  data: Array<{ 
    semana: string; 
    cobranza_esperada: number; 
    cobranza_real: number;
    pedidos_pendientes: number;
  }>;
}

export const CobranzaFuturaChart: FC<CobranzaFuturaChartProps> = ({ data }) => {
  console.log('CobranzaFuturaChart received data:', data);
  
  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${Math.round(value / 1000000)}M`;
    if (value >= 1000) return `$${Math.round(value / 1000)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatNumber = (value: number) => {
    return value.toLocaleString('es-MX');
  };

  // Extraer solo la fecha de inicio de la semana
  const extractStartDate = (semana: string) => {
    // Formato: "Semana X (DD/MM - DD/MM)" -> extraer "DD/MM"
    const match = semana.match(/\((\d{2}\/\d{2})/);
    return match ? match[1] : semana;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cobranza Futura Esperada</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
              data={data} 
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="semana"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
                tickFormatter={extractStartDate}
              />
              <YAxis 
                yAxisId="cobranza"
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
              />
              <YAxis 
                yAxisId="pedidos"
                orientation="right"
                tick={{ fontSize: 12 }}
                tickFormatter={formatNumber}
              />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  if (name === 'cobranza_esperada' || name === 'cobranza_real') {
                    return [formatCurrency(value), name === 'cobranza_esperada' ? 'Cobranza Esperada' : 'Cobranza Real'];
                  }
                  return [formatNumber(value), 'Pedidos Pendientes'];
                }}
                labelFormatter={(label) => `Semana: ${label}`}
                labelStyle={{ color: '#374151' }}
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px'
                }}
              />
              <Legend />
              <Line 
                yAxisId="cobranza"
                type="monotone" 
                dataKey="cobranza_esperada" 
                stroke="#3b82f6" 
                strokeWidth={3}
                name="Cobranza Esperada"
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
              <Line 
                yAxisId="cobranza"
                type="monotone" 
                dataKey="cobranza_real" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Cobranza Real"
                dot={{ fill: '#10b981', strokeWidth: 2, r: 3 }}
                strokeDasharray="5 5"
              />
              <Line 
                yAxisId="pedidos"
                type="monotone" 
                dataKey="pedidos_pendientes" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Pedidos Pendientes"
                dot={{ fill: '#f59e0b', strokeWidth: 2, r: 3 }}
                strokeDasharray="2 2"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
