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
            <h3 className="text-lg font-semibold text-gray-900">Compras</h3>
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
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Información del Sistema:</h4>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• Los archivos se procesan de forma independiente y se integran automáticamente</li>
          <li>• Formatos soportados: .xlsx y .xls</li>
          <li>• <strong>Recomendado:</strong> Usar Compras para nuevas importaciones (sistema optimizado)</li>
          <li>• Cálculos automáticos de fechas estimadas basados en datos de proveedores</li>
          <li>• KPIs avanzados y validación robusta de datos</li>
        </ul>
      </div>
    </div>
  );
};
