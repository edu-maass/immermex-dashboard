import { FC, ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { X } from 'lucide-react';

interface ChipProps {
  children: ReactNode;
  onRemove?: () => void;
  className?: string;
  variant?: 'default' | 'secondary' | 'destructive' | 'outline';
}

export const Chip: FC<ChipProps> = ({ 
  children, 
  onRemove, 
  className, 
  variant = 'default' 
}) => {
  const baseClasses = "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium transition-colors";
  
  const variantClasses = {
    default: "bg-blue-100 text-blue-800 hover:bg-blue-200",
    secondary: "bg-gray-100 text-gray-800 hover:bg-gray-200",
    destructive: "bg-red-100 text-red-800 hover:bg-red-200",
    outline: "border border-gray-300 text-gray-700 hover:bg-gray-50"
  };

  return (
    <span className={cn(baseClasses, variantClasses[variant], className)}>
      {children}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-1 hover:bg-black/10 rounded-full p-0.5"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
};
