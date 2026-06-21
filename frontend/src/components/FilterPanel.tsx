import { useState, useEffect } from 'react'
import type { FilterOptions, ActiveFilters } from '../types'

interface FilterPanelProps {
  filters: ActiveFilters
  onChange: (filters: ActiveFilters) => void
}

function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/gpus/filters`)
      .then(res => res.json())
      .then(json => setOptions(json))
  }, [])

  const toggleArrayValue = (key: keyof ActiveFilters, value: string) => {
    const current = filters[key] as string[]
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value]
    onChange({ ...filters, [key]: updated })
  }

  const setOc = (value: string) => {
    onChange({ ...filters, oc: filters.oc === value ? '' : value })
  }

  const toggleInStock = () => {
    onChange({ ...filters, inStock: !filters.inStock })
  }

  const reset = () => {
    onChange({
      brand: [], manufacturer: [], model: [], vram: [],
      memorytype: [], color: [], oc: '', inStock: false,
      fans: [], buswidth: [], interfaceversion: []
    })
  }

  if (!options) return <div className="text-xs text-gray-500 hover:text-orange-500">Cargando filtros...</div>

const buttonClass = (active: boolean) =>
  `px-3 py-1 rounded-full border text-xs ${
    active 
      ? 'bg-orange-500 text-white border-orange-500' 
      : 'text-gray-400 border-gray-700 hover:border-orange-500 hover:text-orange-500'
  }`

  return (
    <div className="w-full md:w-64 md:shrink-0">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-bold text-gray-200">Filtros</h2>
        <button onClick={reset} className="px-3 py-1 text-xs font-medium text-red-400 bg-darkblue-800 border border-gray-700 rounded-md hover:border-orange-600 ">
          Reiniciar Filtros
        </button>
      </div>

      <div className="mb-4">
        <button onClick={toggleInStock} className={`w-full ${buttonClass(filters.inStock)}`}>
          En stock
        </button>
      </div>

      <div className="mb-4">
        <label className="block text-gray-400 mb-1">Marca</label>
        <div className="flex flex-wrap gap-1">
          {options.brands.map(b => (
            <button key={b} onClick={() => toggleArrayValue('brand', b)} className={buttonClass(filters.brand.includes(b))}>
              {b}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-400 mb-1">Tipo de memoria</label>
        <div className="flex flex-wrap gap-1">
          {options.memoryTypes.map(t => (
            <button key={t} onClick={() => toggleArrayValue('memorytype', t)} className={buttonClass(filters.memorytype.includes(t))}>
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-400 mb-1">Overclock</label>
        <div className="flex flex-wrap gap-1">
          {['true', 'false'].map(val => (
            <button key={val} onClick={() => setOc(val)} className={buttonClass(filters.oc === val)}>
              {val === 'true' ? 'Sí' : 'No'}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-400 mb-1">Fabricante</label>
        <div className="flex flex-wrap gap-1">
          {options.manufacturers.map(m => (
            <button key={m} onClick={() => toggleArrayValue('manufacturer', m)} className={buttonClass(filters.manufacturer.includes(m))}>
              {m}
            </button>
          ))}
        </div>
      </div>

        <div className="mb-4">
        <label className="block text-gray-400 mb-1">Modelo</label>
        <div className="border border-gray-700 rounded px-2 py-1 h-50 overflow-y-auto bg-darkblue-800 scrollbar-thin scrollbar-thumb-orange-500 scrollbar-track-gray-800">
            {options.models.map(m => (
            <label key={m} className="flex items-center gap-2 py-0.5 cursor-pointer text-gray-300 hover:text-orange-500">
              <input
                type="checkbox"
                checked={filters.model.includes(m)}
                onChange={() => toggleArrayValue('model', m)}
                className="accent-orange-500 border-orange-500 bg-orange-200"
                />
                {m}
              </label>
            ))}
        </div>
            <button
                onClick={() => onChange({ ...filters, model: [] })}
                className="text-xs text-gray-300 hover:text-orange-500  " > Limpiar
            </button>
        </div>

      <div className="mb-4">
        <label className="block text-gray-400 mb-1">VRAM</label>
        <div className="flex flex-wrap gap-1">
          {options.vramOptions.map(v => (
            <button key={v} onClick={() => toggleArrayValue('vram', v)} className={buttonClass(filters.vram.includes(v))}>
              {parseFloat(v)} GB
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-400 mb-1">Color</label>
        <div className="flex flex-wrap gap-1">
          {options.colors.map(c => (
            <button key={c} onClick={() => toggleArrayValue('color', c)} className={buttonClass(filters.color.includes(c))}>
              {c}
            </button>
          ))}
        </div>
      </div>

      <button onClick={() => setShowAdvanced(p => !p)} 
        className="text-orange-500 text-xs mb-3 hover:text-orange-400">
        {showAdvanced ? '▲ Ocultar avanzados' : '▼ Filtros avanzados'}
      </button>

      {showAdvanced && (
        <>
          <div className="mb-4">
            <label className="block text-gray-400 mb-1">Ventiladores</label>
            <div className="flex flex-wrap gap-1">
              {options.fans.map(f => (
                <button key={f} onClick={() => toggleArrayValue('fans', f.toString())} className={buttonClass(filters.fans.includes(f.toString()))}>
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-400 mb-1">Bus</label>
            <div className="flex flex-wrap gap-1">
              {options.buswidths.map(b => (
                <button key={b} onClick={() => toggleArrayValue('buswidth', b.toString())} className={buttonClass(filters.buswidth.includes(b.toString()))}>
                  {b}-bit
                </button>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-400 mb-1">PCIe</label>
            <div className="flex flex-wrap gap-1">
              {options.interfaceVersions.map(i => (
                <button key={i} onClick={() => toggleArrayValue('interfaceversion', i)} className={buttonClass(filters.interfaceversion.includes(i))}>
                  PCIe {i}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default FilterPanel