import { useEffect, useRef, useState } from 'react'

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
  const ref = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen(p => !p)}
        className="border border-gray-700 rounded-full px-2 py-1 text-xs text-gray-400 hover:border-orange-500 hover:text-orange-500"
      >
        Ordenar
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-50 bg-gray-800 border border-gray-700 rounded shadow-md w-42">
          {SORT_OPTIONS.map(opt => {
            const isActive = sort === opt.value

            return (
              <button
                key={opt.value}
                onClick={() => {
                  onSortChange(opt.value)
                  setIsOpen(false)
                }}
                className={`block w-full text-left px-3 py-2 text-sm transition-colors
                  ${
                    isActive
                      ? 'text-orange-500 font-medium'
                      : 'text-gray-400 hover:text-orange-500'
                  }`}
              >
                {opt.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default SortMenu