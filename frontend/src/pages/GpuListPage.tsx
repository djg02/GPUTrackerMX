import { useState, useEffect, useRef } from 'react'
import { useSearchParams} from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import type {GpuResponse, ActiveFilters } from '../types'
import Pagination from '../components/Pagination'
import GpuTable from '../components/GpuTable'
import FilterPanel from '../components/FilterPanel'
import SortMenu from '../components/SortMenu'


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
        minPrice: params.get('minPrice') || '',
        maxPrice: params.get('maxPrice') || '',
    }
}

function GpuListPage() {
    const [data, setData] = useState<GpuResponse | null>(null)
    const [searchParams, setSearchParams] = useSearchParams()
    const search = searchParams.get('search') || ''
    const page = Number(searchParams.get('page')) || 1
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const sort = searchParams.get('sort') || 'name_asc'
    const filters = filtersFromParams(searchParams)
    const [isFilterOpen, setIsFilterOpen] = useState(false)
    const [inputValue, setInputValue] = useState(search)
    const isFirstRender = useRef(true)

    // 1. Debounce: wait 300ms after user stops typing before updating debouncedSearch
    useEffect(() => {
        if (isFirstRender.current) {
            isFirstRender.current = false
            return
        }

        const timer = setTimeout(() => {
            setSearchParams(prev => {
            const next = new URLSearchParams(prev)
            if (inputValue) {
                next.set('search', inputValue)
            } else {
                next.delete('search')
            }
            next.set('page', '1')
            return next
            })
        }, 300)

        return () => clearTimeout(timer)
    }, [inputValue])

    // 2. Fetch: re-runs whenever debouncedSearch or page changes
    useEffect(() => {
        const params = new URLSearchParams()
        if (search) params.set('search', search)
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
        if (filters.minPrice) params.set('minPrice', filters.minPrice)
        if (filters.maxPrice) params.set('maxPrice', filters.maxPrice)

        setLoading(true)
        setError(null)

        fetch(`${import.meta.env.VITE_API_URL}/gpus?${params.toString()}`)
        .then(res => {
            if (!res.ok) throw new Error(`Error del servidor: ${res.status}`)
            return res.json()
        })
        .then(json => setData(json))
        .catch(err => setError(err.message))
        .finally(() => setLoading(false))
    }, [search, searchParams.toString()])

    //prevents main page from scrolling while in filter menu
    useEffect(() => {
        if (isFilterOpen) {
            document.body.style.overflow = 'hidden'
        } else {
            document.body.style.overflow = ''
        }

        return () => {
            document.body.style.overflow = ''
        }
        }, [isFilterOpen])

        const toggleSort = (column: 'price' | 'name') => {
            const newSort = sort === `${column}_asc` ? `${column}_desc` : `${column}_asc`
            setSearchParams(prev => {
                const next = new URLSearchParams(prev)
                next.set('sort', newSort)
                next.set('page', '1')
                return next
            })
        }
        const setSortValue = (newSort: string) => {
        setSearchParams(prev => {
            const next = new URLSearchParams(prev)
            next.set('sort', newSort)
            next.set('page', '1')
            return next
        })
        }
        useEffect(() => {
            setInputValue(search)
        }, [search])


    return (
    <div>
        <Helmet>
            <title>GPUTrackerMX - Comparador de Tarjetas Gráficas en México</title>
            <meta name="description" content="Compara precios, especificaciones y disponibilidad de tarjetas gráficas en múltiples tiendas en México. Precios históricos, stock en tiempo real y costos de envío." />
            <link rel="canonical" href="https://gputracker.mx/" />
        </Helmet>
    <div className="p-8 bg-gray-900 min-h-screen">
        <div className="flex flex-col md:flex-row gap-8">
            {/* Filter panel: always visible on desktop, overlay on mobile when open */}
            <div className={`
                ${isFilterOpen ? 'fixed inset-0 z-50 bg-gray-900 p-6 overflow-y-auto' : 'hidden'}
                md:block md:static md:bg-transparent md:p-0 pt-[50px]
            `}>
            {isFilterOpen && (
            <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-800 shadow-md">
                <div className="flex items-center justify-between px-4 py-3">
                <h2 className="text-white font-medium">Filtros</h2>

                <button
                    onClick={() => setIsFilterOpen(false)}
                    className="text-orange-500 text-sm font-medium"
                >
                    ✕ Cerrar
                </button>
                </div>
            </div>
            )}

        <FilterPanel
            filters={filters}
            onChange={newFilters => {
                setSearchParams(prev => {
                const next = new URLSearchParams(prev)
                // Clear all filter-related keys first
                ;['brand', 'manufacturer', 'model', 'vram', 'memorytype', 'color', 'oc', 'inStock', 'fans', 'buswidth', 'interfaceversion', 'minPrice', 'maxPrice'].forEach(key => next.delete(key))
                
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
                if (newFilters.minPrice) next.set('minPrice', newFilters.minPrice)
                if (newFilters.maxPrice) next.set('maxPrice', newFilters.maxPrice)
                
                next.set('page', '1')
                return next
            })
        }}
        />
        </div>
        <div className="flex-1">
            <div className="flex items-center gap-2">
                <input
                    type="text"
                    placeholder="Buscar..."
                    value={inputValue}
                    onChange={e => setInputValue(e.target.value)}
                    className="border border-gray-700 rounded px-1 py-2 flex-2 min-w-0 max-w-md bg-gray-800 text-gray-50 placeholder-gray-400 focus:outline-none focus:border-orange-500"
                />
                {/* Sort button - hides once table headers appear at lg */}
                <div className="lg:hidden">
                    <SortMenu sort={sort} onSortChange={setSortValue} />
                </div>
                  {/* Mobile filter toggle button - hides once sidebar appears at md */}
                <button
                    onClick={() => setIsFilterOpen(true)}
                    className="md:hidden border border-gray-700 rounded-full px-2 py-1 text-xs text-gray-400 hover:border-orange-500 hover:text-orange-500"
                >
                    Filtros
                </button>
            </div>
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
    </div>   
    )
    }
    export default GpuListPage