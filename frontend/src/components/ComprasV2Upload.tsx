import React, { useState, useCallback } from 'react';
import { Button } from './ui/button';
import { LoadingSpinner } from './LoadingSpinner';
import { Tooltip } from './ui/tooltip';
import { apiService } from '../services/api';
import { 
  Download,
  AlertCircle,
  CheckCircle,
  Upload
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';

interface ComprasV2UploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: string) => void;
  onNewUpload?: () => void;
}

export const ComprasV2Upload: React.FC<ComprasV2UploadProps> = ({
  onUploadSuccess,
  onUploadError
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleDownloadLayout = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const blob = await apiService.downloadComprasV2Layout();
      
      // Crear URL para descarga
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'Layout_Compras_V2.xlsx';
      
      // Trigger descarga
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setSuccess('Layout descargado exitosamente');
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error descargando layout';
      setError(errorMessage);
      console.error('Error downloading layout:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = useCallback(async (file: File) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      console.log('🚀 COMPRAS_V2: Enviando archivo a endpoint /upload/compras-v2');
      console.log('📁 Archivo:', file.name, 'Tamaño:', file.size);

      const response = await apiService.uploadComprasV2File(file);
      
      setSuccess(`Archivo procesado exitosamente: ${response.compras_guardadas || 0} compras, ${response.materiales_guardados || 0} materiales`);
      
      if (onUploadSuccess) {
        onUploadSuccess(response);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error procesando archivo';
      setError(errorMessage);
      console.error('Error uploading file:', err);
      
      if (onUploadError) {
        onUploadError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [onUploadSuccess, onUploadError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        handleFileUpload(acceptedFiles[0]);
      }
    },
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false,
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  const excelInstructions = `Instrucciones para el archivo Excel:

• Use el botón "Descargar Layout Excel" para obtener la plantilla correcta
• El archivo debe tener 3 hojas: "Compras Generales", "Materiales Detalle" e "Instrucciones"
• Complete los datos en las hojas correspondientes siguiendo el formato de ejemplo
• Los campos obligatorios están marcados en la hoja "Instrucciones"
• Las fechas deben estar en formato YYYY-MM-DD
• Los proveedores deben existir en la base de datos para cálculos automáticos`;

  return (
    <div className="space-y-6">
      {/* Botón de descarga de layout */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-center items-center mb-4">
          <Tooltip content={excelInstructions} position="bottom">
            <Button 
              onClick={handleDownloadLayout}
              variant="outline"
              className="flex items-center gap-2"
              disabled={loading}
            >
              <Download className="h-4 w-4" />
              Descargar Layout Excel
            </Button>
          </Tooltip>
        </div>
      </div>

      {/* Upload de archivos */}
      <div className="bg-white rounded-lg shadow-md p-6">
        
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : error
              ? 'border-red-500 bg-red-50'
              : success
              ? 'border-green-500 bg-green-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          
          <div className="flex flex-col items-center">
            {error ? (
              <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
            ) : success ? (
              <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
            ) : (
              <Upload className="h-12 w-12 text-gray-400 mb-4" />
            )}
            
            <p className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive
                ? 'Suelta el archivo aquí...'
                : 'Arrastra tu archivo Excel de compras aquí o haz clic para seleccionar'}
            </p>
            
            <p className="text-sm text-gray-500 mb-4">
              Solo archivos .xlsx y .xls son aceptados
            </p>
            
            <Button
              type="button"
              variant="outline"
              className="mt-2"
              disabled={loading}
            >
              Seleccionar archivo
            </Button>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center p-4">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">Procesando...</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            <span className="text-green-800">{success}</span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

    </div>
  );
};
