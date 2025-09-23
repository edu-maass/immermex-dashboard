import { FC, useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { FileUpload } from './FileUpload';
import { Dashboard } from './Dashboard';
import { DashboardFiltrado } from './DashboardFiltrado';
import { Upload, BarChart3, Package } from 'lucide-react';

export const MainDashboard: FC = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(() => {
    // Verificar si hay datos cargados en localStorage
    if (typeof window !== 'undefined') {
      return localStorage.getItem('immermex_data_loaded') === 'true';
    }
    return false;
  });

  const handleUploadSuccess = () => {
    setUploadSuccess(true);
    setDataLoaded(true);
    // Persistir en localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('immermex_data_loaded', 'true');
    }
    // Cambiar automáticamente a la pestaña de dashboard general
    setActiveTab('dashboard');
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
    if (typeof window !== 'undefined') {
      localStorage.removeItem('immermex_data_loaded');
    }
  };

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
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Carga de Archivos
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard General
            </TabsTrigger>
            <TabsTrigger value="pedidos" className="flex items-center gap-2">
              <Package className="h-4 w-4" />
              Análisis por Pedido
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <div className="max-w-2xl mx-auto">
              <FileUpload onUploadSuccess={handleUploadSuccess} onNewUpload={handleNewUpload} />
            </div>
          </TabsContent>

          <TabsContent value="dashboard" className="mt-6">
            <Dashboard onUploadSuccess={handleUploadSuccess} />
          </TabsContent>

          <TabsContent value="pedidos" className="mt-6">
            <DashboardFiltrado onUploadSuccess={handleUploadSuccess} dataLoaded={dataLoaded} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
