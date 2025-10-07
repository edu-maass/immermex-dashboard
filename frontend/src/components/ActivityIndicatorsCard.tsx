import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Calendar, Truck, MapPin, Calculator } from 'lucide-react';

interface ActivityIndicatorsCardProps {
  diasCreditoPromedio: number;
  diasTransportePromedio: number;
  diasPuertoPlantaPromedio: number;
  diasCreditoNeto: number;
}

export const ActivityIndicatorsCard: FC<ActivityIndicatorsCardProps> = ({
  diasCreditoPromedio,
  diasTransportePromedio,
  diasPuertoPlantaPromedio,
  diasCreditoNeto
}) => {
  return (
    <Card className="backdrop-blur-sm bg-card/90 hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">Indicadores de Actividad</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Días Promedio Crédito */}
          <div className="flex items-center space-x-3 p-3 rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Calendar className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-700">Días Crédito</p>
              <p className="text-xl font-bold text-blue-900">
                {diasCreditoPromedio ? diasCreditoPromedio.toFixed(0) : '0'}
              </p>
              <p className="text-xs text-blue-600 font-medium">días promedio</p>
            </div>
          </div>

          {/* Días Transporte */}
          <div className="flex items-center space-x-3 p-3 rounded-lg bg-gradient-to-r from-green-50 to-green-100 border border-green-200">
            <div className="p-2 bg-green-500 rounded-lg">
              <Truck className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-green-700">Días Transporte</p>
              <p className="text-xl font-bold text-green-900">
                {(diasTransportePromedio || 0).toFixed(0)}
              </p>
              <p className="text-xs text-green-600 font-medium">días promedio</p>
            </div>
          </div>

          {/* Días Puerto-Planta */}
          <div className="flex items-center space-x-3 p-3 rounded-lg bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200">
            <div className="p-2 bg-orange-500 rounded-lg">
              <MapPin className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-orange-700">Días Puerto-Planta</p>
              <p className="text-xl font-bold text-orange-900">
                {(diasPuertoPlantaPromedio || 0).toFixed(0)}
              </p>
              <p className="text-xs text-orange-600 font-medium">días promedio</p>
            </div>
          </div>

          {/* Días Crédito Neto */}
          <div className={`flex items-center space-x-3 p-3 rounded-lg border ${
            diasCreditoNeto >= 0 
              ? 'bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200' 
              : 'bg-gradient-to-r from-red-50 to-red-100 border-red-200'
          }`}>
            <div className={`p-2 rounded-lg ${diasCreditoNeto >= 0 ? 'bg-purple-500' : 'bg-red-500'}`}>
              <Calculator className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <p className={`text-sm font-medium ${diasCreditoNeto >= 0 ? 'text-purple-700' : 'text-red-700'}`}>
                Días Crédito Neto
              </p>
              <p className={`text-xl font-bold ${diasCreditoNeto >= 0 ? 'text-purple-900' : 'text-red-900'}`}>
                {(diasCreditoNeto || 0).toFixed(0)}
              </p>
              <p className={`text-xs font-medium ${diasCreditoNeto >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                días promedio
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
