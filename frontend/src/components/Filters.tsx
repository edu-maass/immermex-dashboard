import { useState, FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { FiltrosDashboard } from '../types';
import { Search, X } from 'lucide-react';

interface FiltersProps {
  onFiltersChange: (filtros: FiltrosDashboard) => void;
  onClearFilters: () => void;
}

export const Filters: FC<FiltersProps> = ({ onFiltersChange, onClearFilters }) => {
  const [filtros, setFiltros] = useState<FiltrosDashboard>({});

  const handleInputChange = (field: keyof FiltrosDashboard, value: string | number) => {
    const newFiltros = { ...filtros, [field]: value || undefined };
    setFiltros(newFiltros);
  };

  const handleApplyFilters = () => {
    onFiltersChange(filtros);
  };

  const handleClearFilters = () => {
    setFiltros({});
    onClearFilters();
  };

  const meses = [
    { value: 1, label: 'Enero' },
    { value: 2, label: 'Febrero' },
    { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Mayo' },
    { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' },
    { value: 11, label: 'Noviembre' },
    { value: 12, label: 'Diciembre' },
  ];

  const años = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Filtros
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Fecha inicio */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Fecha Inicio</label>
            <Input
              type="date"
              value={filtros.fecha_inicio || ''}
              onChange={(e) => handleInputChange('fecha_inicio', e.target.value)}
            />
          </div>

          {/* Fecha fin */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Fecha Fin</label>
            <Input
              type="date"
              value={filtros.fecha_fin || ''}
              onChange={(e) => handleInputChange('fecha_fin', e.target.value)}
            />
          </div>

          {/* Cliente */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Cliente</label>
            <Input
              placeholder="Buscar cliente..."
              value={filtros.cliente || ''}
              onChange={(e) => handleInputChange('cliente', e.target.value)}
            />
          </div>

          {/* Agente */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Agente</label>
            <Input
              placeholder="Buscar agente..."
              value={filtros.agente || ''}
              onChange={(e) => handleInputChange('agente', e.target.value)}
            />
          </div>

          {/* Número de pedido */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Número de Pedido</label>
            <Input
              placeholder="Buscar pedido..."
              value={filtros.numero_pedido || ''}
              onChange={(e) => handleInputChange('numero_pedido', e.target.value)}
            />
          </div>

          {/* Material */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Material</label>
            <Input
              placeholder="Buscar material..."
              value={filtros.material || ''}
              onChange={(e) => handleInputChange('material', e.target.value)}
            />
          </div>

          {/* Mes */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Mes</label>
            <Select
              value={filtros.mes?.toString() || ''}
              onValueChange={(value) => handleInputChange('mes', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar mes" />
              </SelectTrigger>
              <SelectContent>
                {meses.map((mes) => (
                  <SelectItem key={mes.value} value={mes.value.toString()}>
                    {mes.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Año */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Año</label>
            <Select
              value={filtros.año?.toString() || ''}
              onValueChange={(value) => handleInputChange('año', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar año" />
              </SelectTrigger>
              <SelectContent>
                {años.map((año) => (
                  <SelectItem key={año} value={año.toString()}>
                    {año}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Botones de acción */}
        <div className="flex gap-2 pt-4">
          <Button onClick={handleApplyFilters} className="flex-1">
            <Search className="h-4 w-4 mr-2" />
            Aplicar Filtros
          </Button>
          <Button variant="outline" onClick={handleClearFilters}>
            <X className="h-4 w-4 mr-2" />
            Limpiar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
