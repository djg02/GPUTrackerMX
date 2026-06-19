import { useState } from 'react'

interface SortMenuProps {
  sort: string
  onSortChange: (sort: string) => void
}

const SORT_OPTIONS = [
  { value: 'name_asc', label: 'Nombre: A-Z' },
  { value: 'name_desc', label: 'Nombre: Z-A' },
  { value: 'price_asc', label: 'Precio: menor a mayor' },
  { value: 'price_desc', label: 'Precio: mayor a menor' },
]

function SortMenu({ sort, onSortChange }: SortMenuProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative md:hidden">
      <button
        onClick={() => setIsOpen(p => !p)}
        className="border border-gray-700 rounded-full px-4 py-1 text-xs text-gray-400 hover:border-orange-500 hover:text-orange-500"
      >
        Ordenar
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 bg-gray-800 border border-gray-700 rounded shadow-md w-48">
          {SORT_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => {
                onSortChange(opt.value)
                setIsOpen(false)
              }}
              className={`block w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                sort === opt.value ? 'font-semibold text-blue-600' : ''
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default SortMenu