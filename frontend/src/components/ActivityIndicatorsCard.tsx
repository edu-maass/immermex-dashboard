import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Calendar, Package, TrendingUp } from 'lucide-react';

interface ActivityIndicatorsCardProps {
  diasCreditoPromedio: number;
  rotacionInventario: number;
  cicloCompras: number;
}

export const ActivityIndicatorsCard: FC<ActivityIndicatorsCardProps> = ({
  diasCreditoPromedio,
  rotacionInventario,
  cicloCompras
}) => {
  return (
    <Card className="backdrop-blur-sm bg-card/90 hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">Indicadores de Actividad</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Días Promedio Crédito */}
          <div className="flex items-center space-x-4 p-4 rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200">
            <div className="p-3 bg-blue-500 rounded-xl shadow-lg">
              <Calendar className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-700">Días Promedio Crédito</p>
              <p className="text-2xl font-bold text-blue-900">
                {diasCreditoPromedio ? diasCreditoPromedio.toFixed(0) : '0'}
              </p>
              <p className="text-xs text-blue-600 font-medium">días promedio</p>
            </div>
          </div>

          {/* Rotación Inventario */}
          <div className="flex items-center space-x-4 p-4 rounded-lg bg-gradient-to-r from-green-50 to-green-100 border border-green-200">
            <div className="p-3 bg-green-500 rounded-xl shadow-lg">
              <Package className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-green-700">Rotación Inventario</p>
              <p className="text-2xl font-bold text-green-900">
                {(rotacionInventario || 0).toFixed(1)}
              </p>
              <p className="text-xs text-green-600 font-medium">veces por año</p>
            </div>
          </div>

          {/* Ciclo de Compras */}
          <div className="flex items-center space-x-4 p-4 rounded-lg bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200">
            <div className="p-3 bg-orange-500 rounded-xl shadow-lg">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-orange-700">Ciclo de Compras</p>
              <p className="text-2xl font-bold text-orange-900">
                {(cicloCompras || 0).toFixed(0)}
              </p>
              <p className="text-xs text-orange-600 font-medium">días promedio</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
