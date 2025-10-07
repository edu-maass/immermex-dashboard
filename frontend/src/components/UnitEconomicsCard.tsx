import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingUp, DollarSign, Calculator, Percent } from 'lucide-react';

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
    <Card className="backdrop-blur-sm bg-card/90 hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold text-gray-900">
          Unit Economics
        </CardTitle>
        <div className="p-2 bg-indigo-100 rounded-lg">
          <TrendingUp className="h-5 w-5 text-indigo-600" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Precio por kg */}
          <div className="p-4 rounded-lg bg-gradient-to-r from-green-50 to-green-100 border border-green-200">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-500 rounded-lg">
                <DollarSign className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-700">Precio por kg</p>
                <p className="text-xl font-bold text-green-900">
                  {formatCurrency(precioUnitarioPromedio)}
                </p>
              </div>
            </div>
          </div>
          
          {/* Costo por kg */}
          <div className="p-4 rounded-lg bg-gradient-to-r from-red-50 to-red-100 border border-red-200">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-500 rounded-lg">
                <Calculator className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-700">Costo por kg</p>
                <p className="text-xl font-bold text-red-900">
                  {formatCurrency(costoUnitarioPromedio)}
                </p>
              </div>
            </div>
          </div>
          
          {/* Utilidad por kg */}
          <div className={`p-4 rounded-lg border ${
            utilidadPorKg >= 0 
              ? 'bg-gradient-to-r from-emerald-50 to-emerald-100 border-emerald-200' 
              : 'bg-gradient-to-r from-red-50 to-red-100 border-red-200'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${utilidadPorKg >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}>
                <TrendingUp className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <p className={`text-sm font-medium ${utilidadPorKg >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                  Utilidad por kg
                </p>
                <p className={`text-xl font-bold ${utilidadPorKg >= 0 ? 'text-emerald-900' : 'text-red-900'}`}>
                  {formatCurrency(utilidadPorKg)}
                </p>
              </div>
            </div>
          </div>
          
          {/* Margen por kg */}
          <div className={`p-4 rounded-lg border ${
            margenPorKg >= 0 
              ? 'bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200' 
              : 'bg-gradient-to-r from-red-50 to-red-100 border-red-200'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${margenPorKg >= 0 ? 'bg-blue-500' : 'bg-red-500'}`}>
                <Percent className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <p className={`text-sm font-medium ${margenPorKg >= 0 ? 'text-blue-700' : 'text-red-700'}`}>
                  Margen por kg
                </p>
                <p className={`text-xl font-bold ${margenPorKg >= 0 ? 'text-blue-900' : 'text-red-900'}`}>
                  {formatPercentage(margenPorKg)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
