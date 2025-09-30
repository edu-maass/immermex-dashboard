import { useCallback, useState, FC } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Upload, File, CheckCircle, AlertCircle, ShoppingCart } from 'lucide-react';
import { apiService } from '../services/api';

interface ComprasUploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: string) => void;
  onNewUpload?: () => void;
}

export const ComprasUpload: FC<ComprasUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  onNewUpload
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Notificar que se está iniciando un nuevo upload
    if (onNewUpload) {
      onNewUpload();
    }

    setUploading(true);
    setUploadStatus('idle');
    setUploadMessage('');

    try {
      // Usar endpoint específico para compras
      const result = await apiService.uploadComprasFile(file);
      setUploadStatus('success');
      const processed = typeof result.registros_procesados === 'number' ? result.registros_procesados : 0;
      setUploadMessage(`Archivo de compras procesado exitosamente. ${processed} registros importados.`);
      onUploadSuccess?.(result);
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage(error instanceof Error ? error.message : 'Error desconocido');
      onUploadError?.(error instanceof Error ? error.message : 'Error desconocido');
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess, onUploadError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  const getStatusIcon = () => {
    switch (uploadStatus) {
      case 'success':
        return <CheckCircle className="h-8 w-8 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-8 w-8 text-red-500" />;
      default:
        return <ShoppingCart className="h-8 w-8 text-orange-500" />;
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-dashed border-orange-300';
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div className="mb-4">
          <div className="flex items-center space-x-2 mb-2">
            <ShoppingCart className="h-5 w-5 text-orange-600" />
            <h3 className="text-lg font-semibold text-gray-900">Carga de Compras</h3>
          </div>
          <p className="text-sm text-gray-600">
            Sube archivos Excel con datos de compras e importaciones
          </p>
        </div>

        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-orange-400 bg-orange-50' : getStatusColor()}
            ${uploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-orange-400'}
          `}
        >
          <input {...getInputProps()} disabled={uploading} />
          
          <div className="flex flex-col items-center space-y-4">
            {getStatusIcon()}
            
            <div className="space-y-2">
              <p className="text-base font-medium">
                {uploading 
                  ? 'Procesando archivo de compras...' 
                  : isDragActive 
                    ? 'Suelta el archivo aquí' 
                    : 'Arrastra un archivo Excel de compras aquí'
                }
              </p>
              <p className="text-sm text-muted-foreground">
                Solo archivos .xlsx y .xls son aceptados
              </p>
            </div>

            {!uploading && (
              <Button variant="outline" size="sm" className="border-orange-300 text-orange-700 hover:bg-orange-50">
                <File className="h-4 w-4 mr-2" />
                Seleccionar archivo de compras
              </Button>
            )}

            {uploadMessage && (
              <div className={`text-sm p-3 rounded-md ${
                uploadStatus === 'success' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {uploadMessage}
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-md">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Formato esperado:</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• Archivo Excel con pestaña "Resumen Compras"</li>
            <li>• Columnas: IMI, Proveedor, Material, Kilogramos, Precio, etc.</li>
            <li>• Datos de importaciones con información aduanal</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
