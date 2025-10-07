import { FC } from 'react';
import { FileUpload } from './FileUpload';
import { ComprasV2Upload } from './ComprasV2Upload';
import { Card, CardContent } from './ui/card';
import { FileText, ShoppingBag } from 'lucide-react';

interface DualUploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: string) => void;
  onNewUpload?: () => void;
}

export const DualUpload: FC<DualUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  onNewUpload
}) => {
  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Carga de Archivos
        </h2>
        <p className="text-gray-600">
          Sube archivos Excel para procesar datos de facturación, cobranza y compras
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sección de Facturación y Cobranza */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-4">
            <FileText className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Facturación y Cobranza</h3>
          </div>
          
          <Card className="border-blue-200">
            <CardContent className="p-0">
              <FileUpload 
                onUploadSuccess={onUploadSuccess}
                onUploadError={onUploadError}
                onNewUpload={onNewUpload}
              />
            </CardContent>
          </Card>

        </div>

        {/* Sección de Compras V2 */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-4">
            <ShoppingBag className="h-5 w-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-gray-900">Compras V2</h3>
          </div>
          
          <Card className="border-indigo-200">
            <CardContent className="p-0">
              <ComprasV2Upload 
                onUploadSuccess={onUploadSuccess}
                onUploadError={onUploadError}
                onNewUpload={onNewUpload}
              />
            </CardContent>
          </Card>

        </div>
      </div>

      {/* Información consolidada */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
        <h4 className="text-lg font-semibold text-gray-900 mb-4 text-center">Información del Sistema</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-sm text-gray-600 space-y-2">
            <p className="font-semibold text-gray-800 mb-2">Facturación y Cobranza:</p>
            <ul className="space-y-1">
              <li>• Datos de facturación</li>
              <li>• Información de cobranza</li>
              <li>• Detalles de pedidos</li>
              <li>• Materiales utilizados</li>
            </ul>
          </div>
          <div className="text-sm text-gray-600 space-y-2">
            <p className="font-semibold text-gray-800 mb-2">Características Compras V2:</p>
            <ul className="space-y-1">
              <li>• Sistema optimizado para mejor rendimiento</li>
              <li>• Cálculos automáticos de fechas estimadas</li>
              <li>• Integración con datos de proveedores</li>
              <li>• Layout descargable con instrucciones</li>
              <li>• Validación robusta de columnas</li>
              <li>• KPIs avanzados de importaciones</li>
            </ul>
          </div>
          <div className="text-sm text-gray-600 space-y-2">
            <p className="font-semibold text-gray-800 mb-2">Información General:</p>
            <ul className="space-y-1">
              <li>• Los archivos se procesan de forma independiente</li>
              <li>• Puedes subir archivos de facturación y compras V2 por separado</li>
              <li>• Los datos se integran automáticamente en el dashboard</li>
              <li>• Formatos soportados: .xlsx y .xls</li>
              <li>• <strong>Recomendado:</strong> Usar Compras V2 para nuevas importaciones</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
