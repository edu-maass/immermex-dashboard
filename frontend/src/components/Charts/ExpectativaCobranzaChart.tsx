import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ExpectativaCobranzaChartProps {
  data: Array<{ semana: string; cobranza_esperada: number; cobranza_real: number }>;
}

export const ExpectativaCobranzaChart: FC<ExpectativaCobranzaChartProps> = ({ data }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Función para formatear las etiquetas del eje X con información de cobranza
  const formatXAxisLabel = (semana: string, data: any) => {
    // Formato: "Semana X (DD/MM - DD/MM)" -> extraer semana del año y fecha de inicio
    const match = semana.match(/Semana (\d+) \((\d{2}\/\d{2})/);
    if (match) {
      const semanaNum = match[1];
      const fechaInicio = match[2]; // "DD/MM"
      
      // Buscar los datos de esta semana para mostrar información de cobranza
      const semanaData = data.find((item: any) => item.semana === semana);
      if (semanaData) {
        const cobranzaReal = semanaData.cobranza_real || 0;
        const cobranzaEsperada = semanaData.cobranza_esperada || 0;
        
        // Formatear montos para mostrar en el eje X
        const formatShortCurrency = (value: number) => {
          if (value >= 1000000) return `${Math.round(value / 1000000)}M`;
          if (value >= 1000) return `${Math.round(value / 1000)}K`;
          return `${Math.round(value)}`;
        };
        
        return `S${semanaNum}\n${fechaInicio}\nReal: $${formatShortCurrency(cobranzaReal)}`;
      }
      
      return `S${semanaNum}\n${fechaInicio}`;
    }
    return semana;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Expectativa de Cobranza por Semana</CardTitle>
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
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={100}
                tickFormatter={(value) => formatXAxisLabel(value, data)}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={formatCurrency}
              />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  formatCurrency(value), 
                  name === 'cobranza_esperada' ? 'Cobranza Esperada' : name === 'cobranza_real' ? 'Cobranza Real' : name
                ]}
                labelFormatter={(label: string) => {
                  const match = label.match(/Semana (\d+) \((\d{2}\/\d{2}) - (\d{2}\/\d{2})\)/);
                  if (match) {
                    return `Semana ${match[1]} (${match[2]} - ${match[3]})`;
                  }
                  return label;
                }}
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
                radius={[4, 4, 0, 0]}
              />
              <Bar 
                dataKey="cobranza_real" 
                fill="#10b981"
                name="Real"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
