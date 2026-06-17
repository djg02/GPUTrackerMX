import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import type { Gpu } from '../types'
import ddtechLogo from '../assets/store_logos/ddtech.png'
import cyberpuertaLogo from '../assets/store_logos/cyberpuerta.png'
import digitalifeLogo from '../assets/store_logos/digitalife.png'

function timeAgo(isoDate: string): string {
  const diffMs = Date.now() - new Date(isoDate).getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMinutes < 60) return `hace ${diffMinutes} min`
  if (diffHours < 24) return `hace ${diffHours} h`
  return `hace ${diffDays} d`
}

const storeLogos: Record<string, string> = {
  'DDTech': ddtechLogo,
  'Cyberpuerta': cyberpuertaLogo,
  'digitalife': digitalifeLogo,
}

function GpuDetailPage() {
  const { id } = useParams()
  const [gpu, setGpu] = useState<Gpu | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)

    fetch(`http://localhost:3000/api/gpus/${id}`)
      .then(res => {
        if (!res.ok) throw new Error(res.status === 404 ? 'Producto no encontrado' : `Error del servidor: ${res.status}`)
        return res.json()
      })
      .then(json => setGpu(json))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p className="p-8 text-gray-500">Cargando...</p>
  if (error) return <p className="p-8 text-red-500">{error}</p>
  if (!gpu) return null

  return (
    <div className="p-8">
    <Link to="/">
    <h1 className="text-3xl font-bold text-blue-600 mb-4 cursor-pointer hover:text-blue-700">GPU Tracker</h1>
    </Link>
      <Link to="/" className="text-blue-600 hover:underline">&larr; Volver al listado</Link>

      <h1 className="text-2xl font-bold mt-4">{gpu.canonicalname}</h1>

    <div className="flex gap-8 mt-6">
        {/* Sidebar */}
        {/* Image */}
        <div className="w-64 shrink-0">
          {gpu.listings[0]?.imageurl && (
            <img
              src={gpu.listings[0].imageurl}
              alt={gpu.canonicalname}
              className="w-full object-contain border rounded"
            />
          )}
        {/* Specs list */}
          <dl className="mt-4 text-sm divide-y">
        {/* Manufacturer */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Fabricante</dt>
              <dd>{gpu.manufacturer_normalized}</dd>
            </div>
        {/* Model */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Modelo</dt>
              <dd>{gpu.model_normalized}</dd>
            </div>
        {/* Series */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Serie</dt>
              <dd>{gpu.series ?? '—'}</dd>
            </div>
        {/* VRAM */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">VRAM</dt>
              <dd>{parseFloat(gpu.vramgb)} GB</dd>
            </div>
        {/* Memory type */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Memoria</dt>
              <dd>{gpu.memorytype}</dd>
            </div>
        {/* Overclock */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Overclock</dt>
              <dd>{gpu.oc ? 'Sí' : 'No'}</dd>
            </div>
        {/* Bus width */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Bus</dt>
              <dd>{gpu.buswidth}-bit</dd>
            </div>
        {/* PCIe interface version */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">PCIe</dt>
              <dd>{gpu.interfaceversion}</dd>
            </div>
        {/* Fan count */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Ventiladores</dt>
              <dd>{gpu.fans ?? '—'}</dd>
            </div>
        {/* Color */}
            <div className="flex justify-between py-1">
              <dt className="text-gray-500">Color</dt>
              <dd>{gpu.color ?? '—'}</dd>
            </div>
        {/* Boost clock (only shown if known) */}
            {gpu.boostclock && (
              <div className="flex justify-between py-1">
                <dt className="text-gray-500">Boost Clock</dt>
                <dd>{gpu.boostclock} MHz</dd>
              </div>
            )}
        {/* Base clock (only shown if known) */}
            {gpu.baseclock && (
              <div className="flex justify-between py-1">
                <dt className="text-gray-500">Base Clock</dt>
                <dd>{gpu.baseclock} MHz</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Prices table */}
        <div className="flex-1">
          <h2 className="font-semibold mb-2">Precios</h2>
          <table className="w-full border-collapse">
            {/* Column headers */}
            <thead>
              <tr className="border-b text-left text-sm text-gray-500">
                <th className="p-2">Tienda</th>
                <th className="p-2 text-center">Estado</th>
                <th className="p-2 text-right">Precio</th>
                <th className="p-2 text-right">Envío</th>
                <th className="p-2 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {/* One row per store listing */}
              {gpu.listings.map(listing => {
                const shipping = listing.shipping ?? 0
                const total = listing.price + shipping
                return (
                  <tr key={listing.link} className="border-b hover:bg-gray-50">
                {/* Store name + logo, links out to the retailer */}
                    <td className="p-2">
                      <a href={listing.link} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                        {storeLogos[listing.storename] && (
                          <img src={storeLogos[listing.storename]} alt={listing.storename} className="w-6 h-6 object-contain" />
                        )}
                        {listing.storename}
                      </a>
                    </td>
                {/* Stock status */}
                    <td className="p-2 text-center">
                        {listing.availabilitystatus === 'InStock' || listing.availabilitystatus === 'Available' ? (
                            <span className="text-xs text-green-600 font-semibold">Disponible</span>
                        ) : (
                            <span className="text-xs text-red-500 font-semibold">Agotado</span>
                        )}
                    </td>
                {/* Price, with relative "last updated" time underneath */}
                    <td className="p-2 text-right">
                        <div>${listing.price.toLocaleString()}</div>
                        <div className="text-xs text-gray-400">{timeAgo(listing.currentpriceupdated)}</div>
                    </td>
                {/* Shipping cost, or note if it's only known at checkout */}
                    <td className="p-2 text-right">
                        {listing.shipping !== null ? `$${listing.shipping.toLocaleString()} MXN` : 'Calculado en Checkout'}
                    </td>
                {/* Total (price + shipping), with "+" if shipping is unknown */}
                    <td className="p-2 text-right font-bold">
                        {listing.shipping !== null 
                            ? `$${(listing.price + listing.shipping).toLocaleString()} MXN`
                            : `$${listing.price.toLocaleString()}+ MXN`
                        }
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default GpuDetailPage