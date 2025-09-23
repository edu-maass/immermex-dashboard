import { useCallback, useState, FC } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Upload, File, CheckCircle, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

interface FileUploadProps {
  onUploadSuccess?: (data: any) => void;
  onUploadError?: (error: string) => void;
  onNewUpload?: () => void;
}

export const FileUpload: FC<FileUploadProps> = ({
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
      const result = await apiService.uploadFile(file);
      setUploadStatus('success');
      const processed = typeof result.registros_procesados === 'number' ? result.registros_procesados : 0;
      setUploadMessage(`Archivo procesado exitosamente. ${processed} registros importados.`);
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
        return <Upload className="h-8 w-8 text-muted-foreground" />;
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-dashed border-gray-300';
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-primary bg-primary/5' : getStatusColor()}
            ${uploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary/50'}
          `}
        >
          <input {...getInputProps()} disabled={uploading} />
          
          <div className="flex flex-col items-center space-y-4">
            {getStatusIcon()}
            
            <div className="space-y-2">
              <p className="text-lg font-medium">
                {uploading 
                  ? 'Procesando archivo...' 
                  : isDragActive 
                    ? 'Suelta el archivo aquí' 
                    : 'Arrastra un archivo Excel aquí o haz clic para seleccionar'
                }
              </p>
              <p className="text-sm text-muted-foreground">
                Solo archivos .xlsx y .xls son aceptados
              </p>
            </div>

            {!uploading && (
              <Button variant="outline" size="sm">
                <File className="h-4 w-4 mr-2" />
                Seleccionar archivo
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
      </CardContent>
    </Card>
  );
};
