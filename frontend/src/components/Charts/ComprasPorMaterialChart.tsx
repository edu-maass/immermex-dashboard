import { FC, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface ComprasPorMaterialChartProps {
  data: Array<{ material: string; total_compras: number; total_kg: number }>;
  titulo?: string;
}

export const ComprasPorMaterialChart: FC<ComprasPorMaterialChartProps> = ({ 
  data, 
  titulo = "Compras por Materiales"
}) => {
  const [viewMode, setViewMode] = useState<'cost' | 'kg'>('cost');

  // Safety check for data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{titulo}</CardTitle>
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => setViewMode('cost')}
              className={`px-3 py-1 text-xs rounded ${
                viewMode === 'cost' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              $
            </button>
            <button
              onClick={() => setViewMode('kg')}
              className={`px-3 py-1 text-xs rounded ${
                viewMode === 'kg' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              KG
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información de materiales</p>
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

  const formatKG = (value: number) => {
    if (value >= 1000000) return `${Math.round(value / 1000000)}M kg`;
    if (value >= 1000) return `${Math.round(value / 1000)}K kg`;
    return `${value.toFixed(0)} kg`;
  };

  // Define colors for the pie chart
  const COLORS = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', 
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
  ];

  // Format data for the chart
  const chartData = data.map((item, index) => ({
    material: item.material.length > 20 ? item.material.substring(0, 20) + '...' : item.material,
    total_compras: item.total_compras,
    total_kg: item.total_kg,
    fullName: item.material, // Keep full name for tooltip
    color: COLORS[index % COLORS.length]
  }));

  // Get the data key based on view mode
  const dataKey = viewMode === 'cost' ? 'total_compras' : 'total_kg';

  // Custom label that only shows percentage
  const renderLabel = (props: any) => {
    const { cx, cy, midAngle, innerRadius, outerRadius, percent } = props;
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    // Only show label if percentage is significant (more than 3%)
    if (percent < 0.03) return null;

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="14"
        fontWeight="600"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => setViewMode('cost')}
            className={`px-3 py-1 text-xs rounded ${
              viewMode === 'cost' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            $
          </button>
          <button
            onClick={() => setViewMode('kg')}
            className={`px-3 py-1 text-xs rounded ${
              viewMode === 'kg' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            KG
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="40%"
                labelLine={false}
                label={renderLabel}
                innerRadius={80}
                outerRadius={150}
                fill="#8884d8"
                dataKey={dataKey}
                paddingAngle={2}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, _name, props: any) => {
                  const payload = props.payload;
                  if (viewMode === 'cost') {
                    return [
                      <div key="tooltip-content" className="space-y-1">
                        <div className="font-semibold text-blue-600">
                          {formatCurrency(value)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {formatKG(payload.total_kg)}
                        </div>
                      </div>
                    ];
                  } else {
                    return [
                      <div key="tooltip-content" className="space-y-1">
                        <div className="font-semibold text-blue-600">
                          {formatKG(value)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {formatCurrency(payload.total_compras)}
                        </div>
                      </div>
                    ];
                  }
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
                  padding: '12px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* Leyenda manual debajo del gráfico */}
        <div className="mt-1 grid grid-cols-2 md:grid-cols-3 gap-1 text-xs">
          {chartData.slice(0, 6).map((item, index) => (
            <div key={index} className="flex items-center gap-1">
              <div 
                className="w-2 h-2 rounded-full flex-shrink-0" 
                style={{ backgroundColor: item.color }}
              />
              <span className="truncate" title={item.fullName}>
                {item.material}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
