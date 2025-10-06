import { FC } from 'react';
import { FileUpload } from './FileUpload';
import { ComprasUpload } from './ComprasUpload';
import { ComprasV2Upload } from './ComprasV2Upload';
import { Card, CardContent } from './ui/card';
import { FileText, ShoppingCart, ShoppingBag } from 'lucide-react';

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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

          <div className="p-3 bg-blue-50 rounded-md">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Incluye:</h4>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>• Datos de facturación</li>
              <li>• Información de cobranza</li>
              <li>• Detalles de pedidos</li>
              <li>• Materiales utilizados</li>
            </ul>
          </div>
        </div>

        {/* Sección de Compras Legacy */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-4">
            <ShoppingCart className="h-5 w-5 text-orange-600" />
            <h3 className="text-lg font-semibold text-gray-900">Compras (Legacy)</h3>
          </div>
          
          <Card className="border-orange-200">
            <CardContent className="p-0">
              <ComprasUpload 
                onUploadSuccess={onUploadSuccess}
                onUploadError={onUploadError}
                onNewUpload={onNewUpload}
              />
            </CardContent>
          </Card>

          <div className="p-3 bg-orange-50 rounded-md">
            <h4 className="text-sm font-medium text-orange-900 mb-2">Incluye:</h4>
            <ul className="text-xs text-orange-800 space-y-1">
              <li>• Datos de compras</li>
              <li>• Información de importaciones</li>
              <li>• Gastos aduanales</li>
              <li>• Estados de pago</li>
            </ul>
          </div>
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

          <div className="p-3 bg-indigo-50 rounded-md">
            <h4 className="text-sm font-medium text-indigo-900 mb-2">Características:</h4>
            <ul className="text-xs text-indigo-800 space-y-1">
              <li>• Sistema optimizado</li>
              <li>• Cálculos automáticos</li>
              <li>• Integración proveedores</li>
              <li>• Layout descargable</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Información adicional */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Información importante:</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <p>• Los archivos se procesan de forma independiente</p>
          <p>• Puedes subir archivos de facturación, compras legacy y compras V2 por separado</p>
          <p>• Los datos se integran automáticamente en el dashboard</p>
          <p>• Formatos soportados: .xlsx y .xls</p>
          <p>• <strong>Recomendado:</strong> Usar Compras V2 para nuevas importaciones (sistema optimizado)</p>
        </div>
      </div>
    </div>
  );
};
