import { useState, useEffect } from 'react'

interface Listing {
  storename: string
  price: number
  currency: string
  link: string
  imageurl: string
  availabilitystatus: string
}

interface Gpu {
  productid: string
  canonicalname: string
  brand: string
  manufacturer_normalized: string
  model_normalized: string
  coolervariant_normalized: string
  vramgb: string
  boostclock: number | null
  listings: Listing[]
  lowestPrice: number | null
  color: string | null
  oc: Boolean
}

interface GpuResponse {
  page: number
  limit: number
  totalCount: number
  totalPages: number
  results: Gpu[]
}

function App() {
  const [data, setData] = useState<GpuResponse | null>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    params.set('page', page.toString())

    fetch(`http://localhost:3000/api/gpus?${params.toString()}`)
      .then(res => res.json())
      .then(json => setData(json))
  }, [search, page])

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-blue-600">GPU Tracker</h1>
      <input
        type="text"
        placeholder="Buscar..."
        value={search}
        onChange={e => {
          setSearch(e.target.value)
          setPage(1)
        }}
        className="mt-4 border rounded px-3 py-2 w-full max-w-md"
      />
      {data && (
        <table className="mt-4 w-full border-collapse">
          <thead>
            <tr className="border-b text-left text-sm text-gray-500">
              <th className="p-2">Nombre</th>
              <th className="p-2 text-center">Modelo</th>
              <th className="p-2 text-center">VRAM</th>
              <th className="p-2 text-center">Boost Clock</th>
              <th className="p-2 text-center">OC</th>
              <th className="p-2 text-right">Color</th>
              <th className="p-2 text-right">Precio</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map(gpu => (
              <tr key={gpu.productid} className="border-b hover:bg-gray-50">
                <td className="p-2">
                  <div className="flex items-center gap-3">
                    {gpu.listings[0]?.imageurl && (
                      <img 
                        src={gpu.listings[0].imageurl} 
                        alt={gpu.canonicalname}
                        className="w-16 h-16 object-contain"
                      />
                    )}
                    <div>
                      <p className="font-semibold">
                        {gpu.manufacturer_normalized} {gpu.coolervariant_normalized}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="p-2 text-center text-sm text-gray-600">
                  {gpu.model_normalized}
                </td>
                <td className="p-2 text-center text-sm text-gray-600">
                  {gpu.vramgb} GB
                </td>
                <td className="p-2 text-center text-sm text-gray-600">
                  {gpu.boostclock ? `${gpu.boostclock} MHz` : '—'}
                </td>
                <td className="p-2 text-center text-sm text-gray-600">
                  {gpu.oc ? 'Sí' : 'No'}
                </td>
                <td className="p-2 text-center text-sm text-gray-600">
                  {gpu.color ? `Blanco` : 'Negro/Gris'}
                </td>
                <td className="p-2 text-right font-bold text-lg">
                  {gpu.lowestPrice ? `$${gpu.lowestPrice.toLocaleString()} MXN` : 'N/A'}
                </td>
                
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {data && (
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => setPage(p => p - 1)}
            disabled={page <= 1}
            className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Anterior
          </button>

          <span className="text-sm text-gray-600">
            Página {data.page} de {data.totalPages} ({data.totalCount} resultados)
          </span>

          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page >= data.totalPages}
            className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Siguiente
          </button>
        </div>
      )}

    </div>
  )
}
export default App