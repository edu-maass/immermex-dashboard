import { FC } from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export const LoadingSpinner: FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  text = 'Cargando...', 
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  return (
    <div className={`flex flex-col items-center justify-center p-4 ${className}`}>
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600`} />
      {text && (
        <p className="mt-2 text-sm text-gray-600">{text}</p>
      )}
    </div>
  );
};

// Componente para loading de páginas completas
export const PageLoader: FC<{ text?: string }> = ({ text = 'Cargando dashboard...' }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <LoadingSpinner size="lg" text={text} />
      </div>
    </div>
  );
};

// Componente para loading de gráficos
export const ChartLoader: FC = () => {
  return (
    <div className="h-80 flex items-center justify-center bg-white rounded-lg shadow">
      <LoadingSpinner text="Cargando gráfico..." />
    </div>
  );
};

// Componente para loading de datos
export const DataLoader: FC<{ message?: string }> = ({ message = 'Procesando datos...' }) => {
  return (
    <div className="flex items-center justify-center p-8">
      <LoadingSpinner text={message} />
    </div>
  );
};
