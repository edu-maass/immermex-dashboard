import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface DataTableRow {
  id: string;
  fecha_compra: string;
  proveedor: string;
  concepto: string; // material in backend
  cantidad_kg: number;
  precio_unitario: number;
  subtotal: number;
  anticipo: number;
}

interface DataTableProps {
  data: DataTableRow[];
}

export const DataTable: FC<DataTableProps> = ({ data }) => {
  const formatCurrency = (value: number) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0';
    }
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-MX');
    } catch {
      return dateString;
    }
  };

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Datos Filtrados</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-40 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg font-medium">Sin datos disponibles</p>
              <p className="text-sm">No hay información para mostrar</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Datos Filtrados ({data.length} registros)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 font-medium text-gray-600">ID</th>
                <th className="text-left py-2 px-3 font-medium text-gray-600">Fecha Compra</th>
                <th className="text-left py-2 px-3 font-medium text-gray-600">Proveedor</th>
                <th className="text-left py-2 px-3 font-medium text-gray-600">Material</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Cantidad (kg)</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Precio Unit.</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Subtotal</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Anticipo</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={row.id || index} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-3 text-gray-900">{row.id}</td>
                  <td className="py-2 px-3 text-gray-700">{formatDate(row.fecha_compra)}</td>
                  <td className="py-2 px-3 text-gray-700 max-w-xs truncate" title={row.proveedor}>
                    {row.proveedor}
                  </td>
                  <td className="py-2 px-3 text-gray-700 max-w-xs truncate" title={row.concepto}>
                    {row.concepto}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-700">
                    {row.cantidad_kg?.toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) || '0'}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-700">
                    {formatCurrency(row.precio_unitario || 0)}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-700 font-medium">
                    {formatCurrency(row.subtotal || 0)}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-700">
                    {formatCurrency(row.anticipo || 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};
