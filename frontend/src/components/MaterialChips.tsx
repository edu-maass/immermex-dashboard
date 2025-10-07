import { FC } from 'react';

interface MaterialChipsProps {
  materiales: string[];
  maxVisible?: number;
}

export const MaterialChips: FC<MaterialChipsProps> = ({ 
  materiales, 
  maxVisible = 3 
}) => {
  if (!materiales || materiales.length === 0) {
    return (
      <span className="text-gray-400 text-sm">Sin materiales</span>
    );
  }

  const visibleMaterials = materiales.slice(0, maxVisible);
  const remainingCount = materiales.length - maxVisible;

  return (
    <div className="flex flex-wrap gap-1">
      {visibleMaterials.map((material, index) => (
        <span
          key={index}
          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
        >
          {material}
        </span>
      ))}
      {remainingCount > 0 && (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          +{remainingCount}
        </span>
      )}
    </div>
  );
};
