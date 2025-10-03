import { FC, useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Chip } from './ui/chip';
import { Search, X, Package, ChevronDown } from 'lucide-react';
import { apiService } from '../services/api';

interface PedidoFilterProps {
  onPedidosChange: (pedidos: string[]) => void;
  onClearPedidos: () => void;
  onUploadSuccess?: boolean;
  dataLoaded?: boolean;
}

export const PedidoFilter: FC<PedidoFilterProps> = ({ onPedidosChange, onClearPedidos, onUploadSuccess, dataLoaded }) => {
  const [pedidosDisponibles, setPedidosDisponibles] = useState<string[]>([]);
  const [pedidosSeleccionados, setPedidosSeleccionados] = useState<string[]>([]);
  const [pedidoSeleccionado, setPedidoSeleccionado] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Cerrar dropdown cuando se hace clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Filtrar pedidos por término de búsqueda
  const pedidosFiltrados = pedidosDisponibles.filter(pedido => 
    !pedidosSeleccionados.includes(pedido) && 
    pedido.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Cargar pedidos disponibles
  useEffect(() => {
    const cargarPedidos = async () => {
      try {
        // Si ya sabemos que hay datos cargados, cargar directamente
        if (dataLoaded) {
          console.log('Datos ya cargados, cargando pedidos directamente');
        }
        
        const pedidos = await apiService.getPedidosFiltro();
        setPedidosDisponibles(pedidos);
        console.log('Pedidos cargados en PedidoFilter:', pedidos);
      } catch (error) {
        console.error('Error cargando pedidos:', error);
      }
    };
    cargarPedidos();
  }, [dataLoaded]);

  // Recargar pedidos si el dropdown está vacío (con retry)
  useEffect(() => {
    if (pedidosDisponibles.length === 0) {
      const recargarPedidos = async () => {
        try {
          const pedidos = await apiService.getPedidosFiltro();
          if (pedidos.length > 0) {
            setPedidosDisponibles(pedidos);
            console.log('Pedidos recargados:', pedidos);
          } else {
            // Si aún no hay pedidos, intentar de nuevo después de un delay
            setTimeout(async () => {
              try {
                const pedidosRetry = await apiService.getPedidosFiltro();
                if (pedidosRetry.length > 0) {
                  setPedidosDisponibles(pedidosRetry);
                  console.log('Pedidos recargados en retry:', pedidosRetry);
                }
              } catch (error) {
                console.error('Error en retry de pedidos:', error);
              }
            }, 2000);
          }
        } catch (error) {
          console.error('Error recargando pedidos:', error);
        }
      };
      recargarPedidos();
    }
  }, [pedidosDisponibles.length]);

  // Recargar pedidos cuando hay un upload exitoso
  useEffect(() => {
    if (onUploadSuccess) {
      const recargarPedidosPostUpload = async () => {
        try {
          const pedidos = await apiService.getPedidosFiltro();
          setPedidosDisponibles(pedidos);
          console.log('Pedidos recargados después de upload:', pedidos);
        } catch (error) {
          console.error('Error recargando pedidos después de upload:', error);
        }
      };
      recargarPedidosPostUpload();
    }
  }, [onUploadSuccess]);

  const handleAgregarPedido = (pedido?: string) => {
    const pedidoToAdd = pedido || pedidoSeleccionado;
    if (pedidoToAdd && !pedidosSeleccionados.includes(pedidoToAdd)) {
      const nuevosPedidos = [...pedidosSeleccionados, pedidoToAdd];
      setPedidosSeleccionados(nuevosPedidos);
      console.log('Agregando pedido:', pedidoToAdd, 'Lista actual:', nuevosPedidos);
      onPedidosChange(nuevosPedidos);
      setPedidoSeleccionado('');
      setSearchTerm('');
      setIsDropdownOpen(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setIsDropdownOpen(true);
  };

  const handleInputFocus = () => {
    setIsDropdownOpen(true);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && pedidosFiltrados.length > 0) {
      handleAgregarPedido(pedidosFiltrados[0]);
    } else if (e.key === 'Escape') {
      setIsDropdownOpen(false);
    }
  };

  const handleRemoverPedido = (pedido: string) => {
    const nuevosPedidos = pedidosSeleccionados.filter(p => p !== pedido);
    setPedidosSeleccionados(nuevosPedidos);
    console.log('Removiendo pedido:', pedido, 'Lista actual:', nuevosPedidos);
    onPedidosChange(nuevosPedidos);
  };

  const handleLimpiarPedidos = () => {
    setPedidosSeleccionados([]);
    console.log('Limpiando pedidos, lista vacía:', []);
    onClearPedidos();
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="space-y-3">
        {/* Selector de pedido con búsqueda */}
        <div className="relative" ref={dropdownRef}>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                ref={inputRef}
                type="text"
                placeholder="Buscar pedido..."
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={handleInputFocus}
                onKeyDown={handleInputKeyDown}
                className="pr-8 h-8 text-sm"
              />
              <ChevronDown 
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 cursor-pointer"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              />
            </div>
            <Button 
              onClick={() => handleAgregarPedido()}
              disabled={!pedidoSeleccionado && pedidosFiltrados.length === 0}
              size="sm"
            >
              <Search className="h-4 w-4 mr-2" />
              Agregar
            </Button>
          </div>
          
          {/* Dropdown personalizado */}
          {isDropdownOpen && pedidosFiltrados.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
              {pedidosFiltrados.map((pedido) => (
                <div
                  key={pedido}
                  className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm border-b border-gray-100 last:border-b-0"
                  onClick={() => handleAgregarPedido(pedido)}
                >
                  Pedido {pedido}
                </div>
              ))}
            </div>
          )}
          
          {/* Mensaje cuando no hay resultados */}
          {isDropdownOpen && searchTerm && pedidosFiltrados.length === 0 && (
            <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg">
              <div className="px-3 py-2 text-sm text-gray-500">
                No se encontraron pedidos con "{searchTerm}"
              </div>
            </div>
          )}
        </div>

        {/* Pedidos seleccionados */}
        {pedidosSeleccionados.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                Pedidos seleccionados ({pedidosSeleccionados.length}):
              </span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleLimpiarPedidos}
              >
                <X className="h-4 w-4 mr-2" />
                Limpiar
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {pedidosSeleccionados.map((pedido) => (
                <Chip
                  key={pedido}
                  onRemove={() => handleRemoverPedido(pedido)}
                  variant="default"
                >
                  Pedido {pedido}
                </Chip>
              ))}
            </div>
          </div>
        )}

        {/* Indicador de estado */}
        {pedidosSeleccionados.length > 0 && (
          <div className="text-sm text-blue-600 bg-blue-50 p-2 rounded-md">
            📊 Mostrando datos filtrados por {pedidosSeleccionados.length} pedido(s) seleccionado(s)
          </div>
        )}
        
        {/* Mensaje cuando no hay pedidos disponibles */}
        {pedidosDisponibles.length === 0 && (
          <div className="text-sm text-orange-600 bg-orange-50 p-2 rounded-md">
            ⚠️ No hay pedidos disponibles. Sube un archivo Excel en la pestaña "Carga de Archivos" para comenzar.
          </div>
        )}
      </div>
    </div>
  );
};
