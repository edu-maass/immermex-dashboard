import * as React from "react"
import { Check, ChevronDown, Search, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface SearchableSelectProps {
  value?: string
  onValueChange?: (value: string) => void
  placeholder?: string
  options: Array<{ value: string; label: string }>
  className?: string
}

export const SearchableSelect: React.FC<SearchableSelectProps> = ({
  value,
  onValueChange,
  placeholder = "Seleccionar...",
  options,
  className
}) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const [searchTerm, setSearchTerm] = React.useState("")
  const [selectedOption, setSelectedOption] = React.useState<{ value: string; label: string } | null>(null)

  // Encontrar la opción seleccionada
  React.useEffect(() => {
    const option = options.find(opt => opt.value === value)
    setSelectedOption(option || null)
  }, [value, options])

  // Filtrar opciones basado en el término de búsqueda
  const filteredOptions = React.useMemo(() => {
    if (!searchTerm) return options
    return options.filter(option =>
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [options, searchTerm])

  const handleSelect = (option: { value: string; label: string }) => {
    setSelectedOption(option)
    onValueChange?.(option.value)
    setIsOpen(false)
    setSearchTerm("")
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedOption(null)
    onValueChange?.("")
    setSearchTerm("")
  }

  return (
    <div className={cn("relative", className)}>
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-md border border-input bg-white px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          "hover:bg-gray-50"
        )}
      >
        <span className="truncate">
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <div className="flex items-center gap-1">
          {selectedOption && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-gray-200 rounded-sm"
            >
              <X className="h-3 w-3" />
            </button>
          )}
          <ChevronDown className={cn("h-4 w-4 opacity-50 transition-transform", isOpen && "rotate-180")} />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-hidden">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-100">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
              />
            </div>
          </div>

          {/* Options List */}
          <div className="max-h-48 overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500 text-center">
                No se encontraron opciones
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className={cn(
                    "w-full px-3 py-2 text-left text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none flex items-center justify-between",
                    selectedOption?.value === option.value && "bg-blue-50 text-blue-700"
                  )}
                >
                  <span>{option.label}</span>
                  {selectedOption?.value === option.value && (
                    <Check className="h-4 w-4 text-blue-600" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}

      {/* Overlay para cerrar al hacer click fuera */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setIsOpen(false)
            setSearchTerm("")
          }}
        />
      )}
    </div>
  )
}
