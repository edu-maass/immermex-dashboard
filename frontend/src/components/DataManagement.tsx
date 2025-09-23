import { FC, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { 
  Database, 
  Upload, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  Calendar,
  FileText,
  HardDrive
} from 'lucide-react';
import { apiService } from '../services/api';

interface ArchivoProcesado {
  id: number;
  nombre_archivo: string;
  fecha_procesamiento: string;
  registros_procesados: number;
  estado: string;
  tamaño_archivo: number;
  algoritmo_usado: string;
}

interface DataSummary {
  has_data: boolean;
  archivo?: {
    id: number;
    nombre: string;
    fecha_procesamiento: string;
    registros_procesados: number;
  };
  conteos?: {
    facturas: number;
    cobranzas: number;
    pedidos: number;
  };
  message?: string;
}

export const DataManagement: FC = () => {
  const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
  const [archivos, setArchivos] = useState<ArchivoProcesado[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<number | null>(null);

  const loadDataSummary = async () => {
    try {
      const summary = await apiService.getDataSummary();
      setDataSummary(summary);
    } catch (error) {
      console.error('Error cargando resumen de datos:', error);
    }
  };

  const loadArchivos = async () => {
    try {
      const archivosData = await apiService.getArchivosProcesados();
      setArchivos(archivosData);
    } catch (error) {
      console.error('Error cargando archivos:', error);
    }
  };

  const handleDeleteArchivo = async (archivoId: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este archivo y todos sus datos asociados?')) {
      return;
    }

    try {
      setDeleting(archivoId);
      await apiService.eliminarArchivo(archivoId);
      
      // Recargar datos
      await Promise.all([loadDataSummary(), loadArchivos()]);
      
      alert('Archivo eliminado exitosamente');
    } catch (error) {
      console.error('Error eliminando archivo:', error);
      alert('Error eliminando archivo');
    } finally {
      setDeleting(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-MX');
  };

  useEffect(() => {
    const loadAllData = async () => {
      setLoading(true);
      await Promise.all([loadDataSummary(), loadArchivos()]);
      setLoading(false);
    };

    loadAllData();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Gestión de Datos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span className="ml-2">Cargando información...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Estado de Datos */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Estado de la Base de Datos
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dataSummary?.has_data ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Datos disponibles</span>
              </div>
              
              {dataSummary.archivo && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium">Archivo:</span>
                    </div>
                    <p className="text-sm text-gray-600">{dataSummary.archivo.nombre}</p>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium">Procesado:</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {formatDate(dataSummary.archivo.fecha_procesamiento)}
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium">Registros:</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {dataSummary.archivo.registros_procesados.toLocaleString()}
                    </p>
                  </div>
                  
                  {dataSummary.conteos && (
                    <div className="space-y-2">
                      <span className="text-sm font-medium">Desglose:</span>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>• Facturas: {dataSummary.conteos.facturas}</p>
                        <p>• Cobranzas: {dataSummary.conteos.cobranzas}</p>
                        <p>• Pedidos: {dataSummary.conteos.pedidos}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-orange-600">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">
                {dataSummary?.message || 'No hay datos disponibles'}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Archivos Procesados */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Archivos Procesados
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => Promise.all([loadDataSummary(), loadArchivos()])}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Actualizar
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {archivos.length > 0 ? (
            <div className="space-y-4">
              {archivos.map((archivo) => (
                <div 
                  key={archivo.id} 
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-4 w-4 text-blue-500" />
                        <span className="font-medium">{archivo.nombre_archivo}</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          archivo.estado === 'procesado' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {archivo.estado}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">Fecha:</span>
                          <p>{formatDate(archivo.fecha_procesamiento)}</p>
                        </div>
                        <div>
                          <span className="font-medium">Registros:</span>
                          <p>{archivo.registros_procesados.toLocaleString()}</p>
                        </div>
                        <div>
                          <span className="font-medium">Tamaño:</span>
                          <p>{formatFileSize(archivo.tamaño_archivo)}</p>
                        </div>
                        <div>
                          <span className="font-medium">Algoritmo:</span>
                          <p className="text-xs">{archivo.algoritmo_usado}</p>
                        </div>
                      </div>
                    </div>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteArchivo(archivo.id)}
                      disabled={deleting === archivo.id}
                      className="ml-4 text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      {deleting === archivo.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Upload className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No hay archivos procesados</p>
              <p className="text-sm">Sube un archivo Excel para comenzar</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
