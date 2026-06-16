import { useState, useEffect } from 'react'
import Pagination from './components/Pagination'
import GpuTable from './components/GpuTable'
import type { Gpu, GpuResponse, ActiveFilters } from '../types'
import FilterPanel from './components/FilterPanel'



function App() {
  const [data, setData] = useState<GpuResponse | null>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [sort, setSort] = useState('name_asc')
  const [filters, setFilters] = useState<ActiveFilters>({
    brand: [], manufacturer: [], model: [], vram: [],
    memorytype: [], color: [], oc: '', inStock: false,
    fans: [], buswidth: [], interfaceversion: []
  })

  // 1. Debounce: wait 300ms after user stops typing before updating debouncedSearch
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
    }, 300)

    return () => clearTimeout(timer)
  }, [search])

  // 2. Fetch: re-runs whenever debouncedSearch or page changes
  useEffect(() => {
    const params = new URLSearchParams()
    if (debouncedSearch) params.set('search', debouncedSearch)
    params.set('page', page.toString())
    params.set('sort', sort)

    filters.brand.forEach(v => params.append('brand', v))
    filters.manufacturer.forEach(v => params.append('manufacturer', v))
    filters.model.forEach(v => params.append('model', v))
    filters.vram.forEach(v => params.append('vram', v))
    filters.memorytype.forEach(v => params.append('memorytype', v))
    filters.color.forEach(v => params.append('color', v))
    if (filters.oc) params.set('oc', filters.oc)
    if (filters.inStock) params.set('inStock', 'true')
    filters.fans.forEach(v => params.append('fans', v))
    filters.buswidth.forEach(v => params.append('buswidth', v))
    filters.interfaceversion.forEach(v => params.append('interfaceversion', v))

    setLoading(true)
    setError(null)

    fetch(`http://localhost:3000/api/gpus?${params.toString()}`)
      .then(res => {
        if (!res.ok) throw new Error(`Error del servidor: ${res.status}`)
        return res.json()
      })
      .then(json => setData(json))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [debouncedSearch, page, sort, filters])

  const toggleSort = (column: 'price' | 'name') => {
  setSort(prev => {
    if (prev === `${column}_asc`) return `${column}_desc`
    return `${column}_asc`
    })
    setPage(1)
  }

return (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-blue-600 mb-4">GPU Tracker</h1>
    
    <div className="flex gap-8">
      <FilterPanel
        filters={filters}
        onChange={newFilters => {
          setFilters(newFilters)
          setPage(1)
        }}
      />

      <div className="flex-1">
        <input
          type="text"
          placeholder="Buscar..."
          value={search}
          onChange={e => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="border rounded px-3 py-2 w-full max-w-md"
        />

        {loading && <p className="mt-4 text-gray-500">Cargando...</p>}
        {error && <p className="mt-4 text-red-500">{error}</p>}

        {data && (
          <GpuTable
            gpus={data.results}
            sort={sort}
            onSort={toggleSort}
          />
        )}

        {data && (
          <Pagination
            page={page}
            totalPages={data.totalPages}
            totalCount={data.totalCount}
            onPrev={() => setPage(p => p - 1)}
            onNext={() => setPage(p => p + 1)}
          />
        )}
      </div>
    </div>
  </div>
)
}
export default App