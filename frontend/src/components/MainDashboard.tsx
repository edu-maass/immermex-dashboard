import { FC, useState, useEffect } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { DualUpload } from './DualUpload';
import { OptimizedDashboard } from './OptimizedDashboard';
import { DashboardFiltrado } from './DashboardFiltrado';
import { ComprasDashboard } from './ComprasDashboard';
import { DataManagement } from './DataManagement';
import { Upload, BarChart3, Package, Database, ShoppingCart } from 'lucide-react';
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Dashboard Immermex
          </h1>
          <p className="text-gray-600">
            Sistema de análisis de datos financieros y operativos
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Carga de Archivos
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Facturación
            </TabsTrigger>
            <TabsTrigger value="pedidos" className="flex items-center gap-2">
              <Package className="h-4 w-4" />
              Análisis por Pedido
            </TabsTrigger>
            <TabsTrigger value="compras" className="flex items-center gap-2">
              <ShoppingCart className="h-4 w-4" />
              Compras
            </TabsTrigger>
            <TabsTrigger value="data" className="flex items-center gap-2">
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

          <TabsContent value="compras" className="mt-6">
            <ComprasDashboard onUploadSuccess={handleUploadSuccess} dataLoaded={dataLoaded} />
          </TabsContent>

          <TabsContent value="data" className="mt-6">
            <DataManagement />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
