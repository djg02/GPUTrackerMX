import { useNavigate } from 'react-router-dom'
import type { Listing, Gpu } from '../types'
import ddtechLogo from '../assets/store_logos/ddtech.png'
import cyberpuertaLogo from '../assets/store_logos/cyberpuerta.png'
import digitalifeLogo from '../assets/store_logos/digitalife.png'
import pcellogo from '../assets/store_logos/pcel.png'
import MLLogo from '../assets/store_logos/mercadolibre.png'
import zegucomLogo from '../assets/store_logos/zegucom.png'
import intercomprasLogo from '../assets/store_logos/intercompras.png'

interface GpuRowProps {
  gpu: Gpu
}

const storeLogos: Record<string, string> = {
  'DDTech': ddtechLogo,
  'Cyberpuerta': cyberpuertaLogo,
  'digitalife': digitalifeLogo,
  'PCEL' : pcellogo,
  'MercadoLibre' : MLLogo,
  'Zegucom' : zegucomLogo,
  'Intercompras' : intercomprasLogo,
}

const getInStockStores = (listings: Listing[]) => [
  ...new Map(
    listings
      .filter(l => l.availabilitystatus === 'InStock' || l.availabilitystatus === 'Available')
      .map(l => [l.storename, l])
  ).values()
]

const getBestImage = (listings: Listing[]): string => {
  // First priority: non-Digitalife, non-PCEL listings
  const preferred = listings.find(l => 
    l.storename !== 'digitalife' && 
    l.storename !== 'PCEL' && 
    l.imageurl
  )
  if (preferred) return preferred.imageurl
  
  // Second priority: PCEL (better than placeholder, worse than other stores)
  const pcelImage = listings.find(l => l.storename === 'PCEL' && l.imageurl)
  if (pcelImage) return pcelImage.imageurl

  // Last resort: placeholder
  return '/gpu-placeholder.png'
}

function GpuRow({ gpu }: GpuRowProps) {
  const navigate = useNavigate()
  const inStockStores = getInStockStores(gpu.listings)

  return (
    <>
      {/* Desktop row - only show at lg+ */}
      <tr 
        className="hidden lg:table-row border-b border-gray-700 hover:bg-gray-800 cursor-pointer"
        onClick={() => navigate(`/gpu/${gpu.productid}`)}
      >
        <td className="p-2">
          <div className="flex items-center gap-3">
            {gpu.listings[0]?.imageurl && (
              <img 
                src={getBestImage(gpu.listings)}
                alt={gpu.canonicalname}
                className="w-16 h-16 object-contain"
              />
            )}
            <div>
               <p className="font-semibold text-gray-50">
                {gpu.manufacturer_normalized} {gpu.coolervariant_normalized}
              </p>
            </div>
          </div>
        </td>
        <td className="p-2 text-center text-sm text-gray-400">
          {gpu.model_normalized}
        </td>
        <td className="p-2 text-center text-sm text-gray-400">
          {gpu.vramgb} GB
        </td>
        <td className="p-2 text-center text-sm text-gray-400">
          {gpu.boostclock ? `${gpu.boostclock} MHz` : '—'}
        </td>
        <td className="p-2 text-center text-sm text-gray-400">
          {gpu.oc ? 'Sí' : 'No'}
        </td>
        <td className="p-2">
          {inStockStores.length === 0 
            ? <span className="block text-center text-xs text-red-500 font-bold">Agotado</span>
            : (
              <div className="flex flex-wrap justify-center gap-1 max-w-[80px] mx-auto ">
                {inStockStores.map(l => storeLogos[l.storename] && (
                  <img
                    key={l.link}
                    src={storeLogos[l.storename]}
                    alt={l.storename}
                    title={l.storename}
                    className="w-6 h-6 object-contain rounded-lg"
                  />
                ))}
              </div>
            )
          }
        </td>
        <td className="p-2 text-center text-sm text-gray-400">
          {gpu.color ? 'Blanco' : 'Negro/Gris'}
        </td>
        <td className="p-2 text-right font-bold text-lg text-orange-500">
          {gpu.lowestPrice ? `$${gpu.lowestPrice.toLocaleString()} MXN` : 'N/A'}
        </td>
      </tr>

      {/* Mobile - show below lg */}
      <div
        className="lg:hidden border border-gray-700 rounded-lg p-3 mb-3 cursor-pointer bg-gray-800 hover:bg-gray-900"
        onClick={() => navigate(`/gpu/${gpu.productid}`)}
      >
        <div className="flex gap-3">
          {gpu.listings[0]?.imageurl && (
            <img 
              src={getBestImage(gpu.listings)}
              alt={gpu.canonicalname}
              className="w-20 h-20 object-contain shrink-0"
            />
          )}
          <div className="flex-1">
            <p className="font-semibold">
              {gpu.manufacturer_normalized} {gpu.coolervariant_normalized}
            </p>
            <p className="text-sm text-gray-400">{gpu.model_normalized}</p>

            <div className="mt-2 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">VRAM</span>
                <span className="text-gray-300">{gpu.vramgb} GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Overclock</span>
                <span className="text-gray-300">{gpu.oc ? 'Sí' : 'No'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Color</span>
                <span className="text-gray-300">{gpu.color ? 'Blanco' : 'Negro/Gris'}</span>
            </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-700">
          <div className="flex items-center gap-1">
          {inStockStores.length === 0
            ? <span className="text-xs text-red-500 font-bold">Agotado</span>
            : (
              <>
                <span className="text-xs text-green-500 font-bold ">Stock: </span>
                <div className="flex flex-wrap justify-center gap-1 max-w-[80px] mx-auto " >
                {inStockStores.map(l => storeLogos[l.storename] && (
                  <img
                    key={l.link}
                    src={storeLogos[l.storename]}
                    alt={l.storename}
                    title={l.storename}
                    className="w-6 h-6 object-contain rounded-lg"
                  />
                ))}</div>
              </>
            )
          }
          </div>
          <span className="font-bold text-lg text-orange-500 ">
            {gpu.lowestPrice ? `$${Math.floor(gpu.lowestPrice).toLocaleString()} MXN` : 'N/A'}
          </span>
        </div>
      </div>
    </>
  )
}

export default GpuRow