import { FC, useState, useEffect } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { DualUpload } from './DualUpload';
import { OptimizedDashboard } from './OptimizedDashboard';
import { DashboardFiltrado } from './DashboardFiltrado';
import { ComprasV2Dashboard } from './ComprasV2Dashboard';
import { DataManagement } from './DataManagement';
import { Upload, BarChart3, Package, Database, ShoppingBag } from 'lucide-react';
import { apiService } from '../services/api';

export const MainDashboard: FC = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [dataSummary, setDataSummary] = useState<any>(null);
  const [isCheckingData, setIsCheckingData] = useState(true);

  // Verificar datos persistentes al cargar la aplicación
  useEffect(() => {
    const checkPersistentData = async () => {
      try {
        setIsCheckingData(true);
        const summary = await apiService.getDataSummary();
        setDataSummary(summary);
        
        if (summary.has_data) {
          setDataLoaded(true);
          // Si hay datos persistentes, ir directamente al dashboard
          setActiveTab('dashboard');
          console.log('Datos persistentes encontrados:', summary);
        } else {
          setDataLoaded(false);
          console.log('No hay datos persistentes disponibles');
        }
      } catch (error) {
        console.error('Error verificando datos persistentes:', error);
        setDataLoaded(false);
      } finally {
        setIsCheckingData(false);
      }
    };

    checkPersistentData();
  }, []);

  const handleUploadSuccess = async () => {
    setUploadSuccess(true);
    
    // Verificar datos después del upload
    try {
      const summary = await apiService.getDataSummary();
      setDataSummary(summary);
      setDataLoaded(summary.has_data);
      
      if (summary.has_data) {
        // Cambiar automáticamente a la pestaña de dashboard general
        setActiveTab('dashboard');
      }
    } catch (error) {
      console.error('Error verificando datos después del upload:', error);
    }
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    // Si hay datos cargados y se cambia a pedidos, no necesitamos recargar
    if (tab === 'pedidos' && dataLoaded) {
      console.log('Cambiando a pestaña de pedidos con datos ya cargados');
    }
  };

  const handleNewUpload = () => {
    // Limpiar estado anterior cuando se sube un nuevo archivo
    setUploadSuccess(false);
    setDataLoaded(false);
    setDataSummary(null);
  };

  // Mostrar loading mientras se verifican los datos
  if (isCheckingData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando datos disponibles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">

        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="grid w-full grid-cols-5 bg-white shadow-lg border border-gray-200">
            <TabsTrigger 
              value="upload" 
              data-tab="upload"
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-blue-700 data-[state=inactive]:hover:bg-blue-50 data-[state=inactive]:text-gray-600 transition-all duration-200"
            >
              <Upload className="h-4 w-4" />
              Carga de Archivos
            </TabsTrigger>
            <TabsTrigger 
              value="dashboard" 
              className="flex items-center gap-2 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-green-700 data-[state=inactive]:hover:bg-green-50 data-[state=inactive]:text-gray-600 transition-all duration-200"
            >
              <BarChart3 className="h-4 w-4" />
              Facturación
            </TabsTrigger>
            <TabsTrigger 
              value="pedidos" 
              className="flex items-center gap-2 data-[state=active]:bg-purple-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-purple-700 data-[state=inactive]:hover:bg-purple-50 data-[state=inactive]:text-gray-600 transition-all duration-200"
            >
              <Package className="h-4 w-4" />
              Análisis por Pedido
            </TabsTrigger>
            <TabsTrigger 
              value="compras-v2" 
              className="flex items-center gap-2 data-[state=active]:bg-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-indigo-700 data-[state=inactive]:hover:bg-indigo-50 data-[state=inactive]:text-gray-600 transition-all duration-200"
            >
              <ShoppingBag className="h-4 w-4" />
              Compras
            </TabsTrigger>
            <TabsTrigger 
              value="data" 
              className="flex items-center gap-2 data-[state=active]:bg-gray-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-gray-700 data-[state=inactive]:hover:bg-gray-50 data-[state=inactive]:text-gray-600 transition-all duration-200"
            >
              <Database className="h-4 w-4" />
              Gestión de Datos
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <div className="max-w-6xl mx-auto">
              <DualUpload onUploadSuccess={handleUploadSuccess} onNewUpload={handleNewUpload} />
            </div>
          </TabsContent>

          <TabsContent value="dashboard" className="mt-6">
            <OptimizedDashboard onUploadSuccess={handleUploadSuccess} />
          </TabsContent>

          <TabsContent value="pedidos" className="mt-6">
            <DashboardFiltrado onUploadSuccess={handleUploadSuccess} dataLoaded={dataLoaded} />
          </TabsContent>

          <TabsContent value="compras-v2" className="mt-6">
            <ComprasV2Dashboard onUploadSuccess={handleUploadSuccess} />
          </TabsContent>

          <TabsContent value="data" className="mt-6">
            <DataManagement />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
