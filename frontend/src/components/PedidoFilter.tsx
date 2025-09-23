import { FC, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Chip } from './ui/chip';
import { Search, X, Package } from 'lucide-react';
import { apiService } from '../services/api';

interface PedidoFilterProps {
  onPedidosChange: (pedidos: string[]) => void;
  onClearPedidos: () => void;
}

export const PedidoFilter: FC<PedidoFilterProps> = ({ onPedidosChange, onClearPedidos }) => {
  const [pedidosDisponibles, setPedidosDisponibles] = useState<string[]>([]);
  const [pedidosSeleccionados, setPedidosSeleccionados] = useState<string[]>([]);
  const [pedidoSeleccionado, setPedidoSeleccionado] = useState<string>('');

  // Cargar pedidos disponibles
  useEffect(() => {
    const cargarPedidos = async () => {
      try {
        const pedidos = await apiService.getPedidosFiltro();
        setPedidosDisponibles(pedidos);
        console.log('Pedidos cargados en PedidoFilter:', pedidos);
      } catch (error) {
        console.error('Error cargando pedidos:', error);
      }
    };
    cargarPedidos();
  }, []);

  // Recargar pedidos si el dropdown está vacío
  useEffect(() => {
    if (pedidosDisponibles.length === 0) {
      const recargarPedidos = async () => {
        try {
          const pedidos = await apiService.getPedidosFiltro();
          if (pedidos.length > 0) {
            setPedidosDisponibles(pedidos);
            console.log('Pedidos recargados:', pedidos);
          }
        } catch (error) {
          console.error('Error recargando pedidos:', error);
        }
      };
      recargarPedidos();
    }
  }, [pedidosDisponibles.length]);

  const handleAgregarPedido = () => {
    if (pedidoSeleccionado && !pedidosSeleccionados.includes(pedidoSeleccionado)) {
      const nuevosPedidos = [...pedidosSeleccionados, pedidoSeleccionado];
      setPedidosSeleccionados(nuevosPedidos);
      console.log('Agregando pedido:', pedidoSeleccionado, 'Lista actual:', nuevosPedidos);
      onPedidosChange(nuevosPedidos);
      setPedidoSeleccionado('');
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
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Filtro por Pedido
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Selector de pedido */}
        <div className="flex gap-2">
          <Select
            value={pedidoSeleccionado}
            onValueChange={setPedidoSeleccionado}
          >
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Seleccionar pedido" />
            </SelectTrigger>
            <SelectContent>
              {pedidosDisponibles
                .filter(pedido => !pedidosSeleccionados.includes(pedido))
                .map((pedido) => (
                  <SelectItem key={pedido} value={pedido}>
                    Pedido {pedido}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
          <Button 
            onClick={handleAgregarPedido}
            disabled={!pedidoSeleccionado}
            size="sm"
          >
            <Search className="h-4 w-4 mr-2" />
            Agregar
          </Button>
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
      </CardContent>
    </Card>
  );
};
