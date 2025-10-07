import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingUp } from 'lucide-react';

interface UnitEconomicsCardProps {
  precioUnitarioPromedio?: number;
  costoUnitarioPromedio?: number;
  utilidadPorKg?: number;
  margenPorKg?: number;
}

export const UnitEconomicsCard: React.FC<UnitEconomicsCardProps> = ({
  precioUnitarioPromedio = 0,
  costoUnitarioPromedio = 0,
  utilidadPorKg = 0,
  margenPorKg = 0,
}) => {
  const formatCurrency = (value: number) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0.0%';
    }
    return `${value.toFixed(1)}%`;
  };

  return (
    <Card className="backdrop-blur-sm bg-card/90">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Unit Economics
        </CardTitle>
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Precio por kg */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Precio por kg</p>
            <p className="text-xl font-bold text-green-600">
              {formatCurrency(precioUnitarioPromedio)}
            </p>
          </div>
          
          {/* Costo por kg */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Costo por kg</p>
            <p className="text-xl font-bold text-red-600">
              {formatCurrency(costoUnitarioPromedio)}
            </p>
          </div>
          
          {/* Utilidad por kg */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Utilidad por kg</p>
            <p className={`text-xl font-bold ${utilidadPorKg >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(utilidadPorKg)}
            </p>
          </div>
          
          {/* Margen por kg */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Margen por kg</p>
            <p className={`text-xl font-bold ${margenPorKg >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercentage(margenPorKg)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
