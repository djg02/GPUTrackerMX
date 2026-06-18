import type { Listing } from '../types'
import ddtechLogo from '../assets/store_logos/ddtech.png'
import cyberpuertaLogo from '../assets/store_logos/cyberpuerta.png'
import digitalifeLogo from '../assets/store_logos/digitalife.png'

const storeLogos: Record<string, string> = {
  'DDTech': ddtechLogo,
  'Cyberpuerta': cyberpuertaLogo,
  'digitalife': digitalifeLogo,
}

function timeAgo(isoDate: string): string {
  const diffMs = Date.now() - new Date(isoDate).getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMinutes < 60) return `hace ${diffMinutes} min`
  if (diffHours < 24) return `hace ${diffHours} h`
  return `hace ${diffDays} d`
}

interface PricesTableProps {
  listings: Listing[]
}

function PricesTable({ listings }: PricesTableProps) {
  return (
    <div className="flex-1">
      <h2 className="font-semibold mb-2">Precios</h2>

      {/* Desktop table */}
      <div className="overflow-x-auto">
        <table className="hidden md:table w-full border-collapse">
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
            {listings.map(listing => (
              <tr key={listing.link} className="border-b hover:bg-gray-50">
                <td className="p-2">
                  <a href={listing.link} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                    {storeLogos[listing.storename] && (
                      <img src={storeLogos[listing.storename]} alt={listing.storename} className="w-6 h-6 object-contain" />
                    )}
                    {listing.storename}
                  </a>
                </td>
                <td className="p-2 text-center">
                  {listing.availabilitystatus === 'InStock' || listing.availabilitystatus === 'Available' ? (
                    <span className="text-xs text-green-600 font-semibold">Disponible</span>
                  ) : (
                    <span className="text-xs text-red-500 font-semibold">Agotado</span>
                  )}
                </td>
                <td className="p-2 text-right">
                  <div>${listing.price.toLocaleString()}</div>
                  <div className="text-xs text-gray-400">{timeAgo(listing.currentpriceupdated)}</div>
                </td>
                <td className="p-2 text-right">
                  {listing.shipping !== null ? `$${listing.shipping.toLocaleString()} MXN` : 'Calculado en Checkout'}
                </td>
                <td className="p-2 text-right font-bold">
                  {listing.shipping !== null
                    ? `$${(listing.price + listing.shipping).toLocaleString()} MXN`
                    : `$${listing.price.toLocaleString()}+ MXN`
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-3">
        {listings.map(listing => (
          <a
            key={listing.link}
            href={listing.link}
            target="_blank"
            rel="noopener noreferrer"
            className="block border rounded-lg p-3 hover:bg-gray-50"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {storeLogos[listing.storename] && (
                  <img src={storeLogos[listing.storename]} alt={listing.storename} className="w-6 h-6 object-contain" />
                )}
                <span className="font-semibold">{listing.storename}</span>
              </div>
              {listing.availabilitystatus === 'InStock' || listing.availabilitystatus === 'Available' ? (
                <span className="text-xs text-green-600 font-semibold">Disponible</span>
              ) : (
                <span className="text-xs text-red-500 font-semibold">Agotado</span>
              )}
            </div>

            <div className="mt-2 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">Precio</span>
                <span>${listing.price.toLocaleString()} <span className="text-xs text-gray-400">({timeAgo(listing.currentpriceupdated)})</span></span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Envío</span>
                <span>{listing.shipping !== null ? `$${listing.shipping.toLocaleString()}` : 'En checkout'}</span>
              </div>
            </div>

            <div className="flex justify-between mt-2 pt-2 border-t">
              <span className="text-gray-500 text-sm">Total</span>
              <span className="font-bold">
                {listing.shipping !== null
                  ? `$${(listing.price + listing.shipping).toLocaleString()} MXN`
                  : `$${listing.price.toLocaleString()}+ MXN`
                }
              </span>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

export default PricesTable