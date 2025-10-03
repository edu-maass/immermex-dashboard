import { useState, FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { SearchableSelect } from './ui/searchable-select';
import { FiltrosDashboard } from '../types';
import { Search, X } from 'lucide-react';
import { apiService } from '../services/api';

interface FiltersProps {
  onFiltersChange: (filtros: FiltrosDashboard) => void;
  onClearFilters: () => void;
}

export const Filters: FC<FiltersProps> = ({ onFiltersChange, onClearFilters }) => {
  const [filtros, setFiltros] = useState<FiltrosDashboard>({});

  const handleInputChange = (field: keyof FiltrosDashboard, value: string | number) => {
    const newFiltros = { ...filtros, [field]: value || undefined };
    
    // Si se deselecciona el año, limpiar también el mes
    if (field === 'año' && !value) {
      newFiltros.mes = undefined;
    }
    
    setFiltros(newFiltros);
  };

  const handleApplyFilters = async () => {
    try {
      // Aplicar filtros en el backend
      const response = await apiService.aplicarFiltros(filtros);
      console.log('Filtros aplicados:', response);
      
      // Notificar al componente padre
      onFiltersChange(filtros);
    } catch (error) {
      console.error('Error aplicando filtros:', error);
      // Aún así notificar al componente padre para que recargue
      onFiltersChange(filtros);
    }
  };

  const handleClearFilters = () => {
    setFiltros({});
    onClearFilters();
  };

  const meses = [
    { value: '1', label: 'Enero' },
    { value: '2', label: 'Febrero' },
    { value: '3', label: 'Marzo' },
    { value: '4', label: 'Abril' },
    { value: '5', label: 'Mayo' },
    { value: '6', label: 'Junio' },
    { value: '7', label: 'Julio' },
    { value: '8', label: 'Agosto' },
    { value: '9', label: 'Septiembre' },
    { value: '10', label: 'Octubre' },
    { value: '11', label: 'Noviembre' },
    { value: '12', label: 'Diciembre' },
  ];

  const años = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(año => ({
    value: año.toString(),
    label: año.toString()
  }));


  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="grid grid-cols-2 gap-3">
          {/* Mes */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Mes {!filtros.año && <span className="text-gray-400">(Selecciona año)</span>}
            </label>
            <SearchableSelect
              value={filtros.mes?.toString() || ''}
              onValueChange={(value) => handleInputChange('mes', parseInt(value))}
              placeholder="Seleccionar mes"
              options={meses}
              disabled={!filtros.año}
            />
          </div>

          {/* Año */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Año</label>
            <SearchableSelect
              value={filtros.año?.toString() || ''}
              onValueChange={(value) => handleInputChange('año', parseInt(value))}
              placeholder="Seleccionar año"
              options={años}
            />
          </div>
        </div>
      </div>
  );
};
