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
    fetch('http://localhost:3000/api/gpus/filters')
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

  if (!options) return <div className="w-48 text-sm text-gray-400">Cargando filtros...</div>

  const buttonClass = (active: boolean) =>
    `px-3 py-1 rounded-full border text-xs ${
      active ? 'bg-blue-600 text-white border-blue-600' : 'text-gray-600 hover:bg-gray-50'
    }`

  return (
    <div className="w-48 shrink-0 text-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-bold text-gray-700">Filtros</h2>
        <button onClick={reset} className="px-3 py-1 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 hover:border-red-300 transition-colors">
          Reiniciar Filtros
        </button>
      </div>

      <div className="mb-4">
        <button onClick={toggleInStock} className={`w-full ${buttonClass(filters.inStock)}`}>
          En stock
        </button>
      </div>

      <div className="mb-4">
        <label className="block text-gray-500 mb-1">Marca</label>
        <div className="flex flex-wrap gap-1">
          {options.brands.map(b => (
            <button key={b} onClick={() => toggleArrayValue('brand', b)} className={buttonClass(filters.brand.includes(b))}>
              {b}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-500 mb-1">Tipo de memoria</label>
        <div className="flex flex-wrap gap-1">
          {options.memoryTypes.map(t => (
            <button key={t} onClick={() => toggleArrayValue('memorytype', t)} className={buttonClass(filters.memorytype.includes(t))}>
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-500 mb-1">Overclock</label>
        <div className="flex flex-wrap gap-1">
          {['true', 'false'].map(val => (
            <button key={val} onClick={() => setOc(val)} className={buttonClass(filters.oc === val)}>
              {val === 'true' ? 'Sí' : 'No'}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-500 mb-1">Fabricante</label>
        <div className="flex flex-wrap gap-1">
          {options.manufacturers.map(m => (
            <button key={m} onClick={() => toggleArrayValue('manufacturer', m)} className={buttonClass(filters.manufacturer.includes(m))}>
              {m}
            </button>
          ))}
        </div>
      </div>

        <div className="mb-4">
        <label className="block text-gray-500 mb-1">Modelo</label>
        <div className="h-52 overflow-y-auto rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-500">
            {options.models.map(m => (
            <label key={m} className="flex items-center gap-2 py-0.5 cursor-pointer">
                <input
                type="checkbox"
                checked={filters.model.includes(m)}
                onChange={() => toggleArrayValue('model', m)}
                />
                {m}
            </label>
            ))}
        </div>
            <button
                onClick={() => onChange({ ...filters, model: [] })}
                className="text-xs text-gray-400 hover:text-gray-600  " > Limpiar
            </button>
        </div>

      <div className="mb-4">
        <label className="block text-gray-500 mb-1">VRAM</label>
        <div className="flex flex-wrap gap-1">
          {options.vramOptions.map(v => (
            <button key={v} onClick={() => toggleArrayValue('vram', v)} className={buttonClass(filters.vram.includes(v))}>
              {parseFloat(v)} GB
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-gray-500 mb-1">Color</label>
        <div className="flex flex-wrap gap-1">
          {options.colors.map(c => (
            <button key={c} onClick={() => toggleArrayValue('color', c)} className={buttonClass(filters.color.includes(c))}>
              {c}
            </button>
          ))}
        </div>
      </div>

      <button onClick={() => setShowAdvanced(p => !p)} className="text-blue-500 text-xs mb-3">
        {showAdvanced ? '▲ Ocultar avanzados' : '▼ Filtros avanzados'}
      </button>

      {showAdvanced && (
        <>
          <div className="mb-4">
            <label className="block text-gray-500 mb-1">Ventiladores</label>
            <div className="flex flex-wrap gap-1">
              {options.fans.map(f => (
                <button key={f} onClick={() => toggleArrayValue('fans', f.toString())} className={buttonClass(filters.fans.includes(f.toString()))}>
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-500 mb-1">Bus</label>
            <div className="flex flex-wrap gap-1">
              {options.buswidths.map(b => (
                <button key={b} onClick={() => toggleArrayValue('buswidth', b.toString())} className={buttonClass(filters.buswidth.includes(b.toString()))}>
                  {b}-bit
                </button>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-500 mb-1">PCIe</label>
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