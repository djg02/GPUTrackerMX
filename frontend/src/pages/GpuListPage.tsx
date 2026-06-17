import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import Pagination from '../components/Pagination'
import GpuTable from '../components/GpuTable'
import type {GpuResponse, ActiveFilters } from '../types'
import FilterPanel from '../components/FilterPanel'


function filtersFromParams(params: URLSearchParams): ActiveFilters {
    return {
        brand: params.getAll('brand'),
        manufacturer: params.getAll('manufacturer'),
        model: params.getAll('model'),
        vram: params.getAll('vram'),
        memorytype: params.getAll('memorytype'),
        color: params.getAll('color'),
        oc: params.get('oc') || '',
        inStock: params.get('inStock') === 'true',
        fans: params.getAll('fans'),
        buswidth: params.getAll('buswidth'),
        interfaceversion: params.getAll('interfaceversion'),
    }
}

function GpuListPage() {
    const [data, setData] = useState<GpuResponse | null>(null)
    const [searchParams, setSearchParams] = useSearchParams()
    const search = searchParams.get('search') || ''
    const page = Number(searchParams.get('page')) || 1
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const sort = searchParams.get('sort') || 'name_asc'
    const filters = filtersFromParams(searchParams)

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
    }, [debouncedSearch, searchParams.toString()])

        const toggleSort = (column: 'price' | 'name') => {
            const newSort = sort === `${column}_asc` ? `${column}_desc` : `${column}_asc`
            setSearchParams(prev => {
                const next = new URLSearchParams(prev)
                next.set('sort', newSort)
                next.set('page', '1')
                return next
            })
        }

    return (
    <div className="p-8">
        <Link to="/">
        <h1 className="text-3xl font-bold text-blue-600 mb-4 cursor-pointer hover:text-blue-700">GPU Tracker</h1>
        </Link>
        
        <div className="flex gap-8">
        <FilterPanel
            filters={filters}
            onChange={newFilters => {
                setSearchParams(prev => {
                const next = new URLSearchParams(prev)
                // Clear all filter-related keys first
                ;['brand', 'manufacturer', 'model', 'vram', 'memorytype', 'color', 'oc', 'inStock', 'fans', 'buswidth', 'interfaceversion'].forEach(key => next.delete(key))
                
                // Re-add the new values
                newFilters.brand.forEach(v => next.append('brand', v))
                newFilters.manufacturer.forEach(v => next.append('manufacturer', v))
                newFilters.model.forEach(v => next.append('model', v))
                newFilters.vram.forEach(v => next.append('vram', v))
                newFilters.memorytype.forEach(v => next.append('memorytype', v))
                newFilters.color.forEach(v => next.append('color', v))
                if (newFilters.oc) next.set('oc', newFilters.oc)
                if (newFilters.inStock) next.set('inStock', 'true')
                newFilters.fans.forEach(v => next.append('fans', v))
                newFilters.buswidth.forEach(v => next.append('buswidth', v))
                newFilters.interfaceversion.forEach(v => next.append('interfaceversion', v))
                
                next.set('page', '1')
                return next
            })
        }}
        />

        <div className="flex-1">
            <input
                type="text"
                placeholder="Buscar..."
                value={search}
                onChange={e => {
                    setSearchParams(prev => {
                        const next = new URLSearchParams(prev)
                        if (e.target.value) {
                        next.set('search', e.target.value)
                        } else {
                        next.delete('search')
                        }
                        next.set('page', '1')
                        return next
                    })
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
                    onPrev={() => setSearchParams(prev => {
                        const next = new URLSearchParams(prev)
                        next.set('page', (page - 1).toString())
                        return next
                    })}
                    onNext={() => setSearchParams(prev => {
                        const next = new URLSearchParams(prev)
                        next.set('page', (page + 1).toString())
                        return next
                    })}
                />
            )}
        </div>
        </div>
    </div>
    )
    }
    export default GpuListPage