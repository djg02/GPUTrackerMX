import { useNavigate } from 'react-router-dom'
import type { Listing, Gpu } from '../types'
import ddtechLogo from '../assets/store_logos/ddtech.png'
import cyberpuertaLogo from '../assets/store_logos/cyberpuerta.png'
import digitalifeLogo from '../assets/store_logos/digitalife.png'
import pcellogo from '../assets/store_logos/pcel.png'

interface GpuRowProps {
  gpu: Gpu
}

const storeLogos: Record<string, string> = {
  'DDTech': ddtechLogo,
  'Cyberpuerta': cyberpuertaLogo,
  'digitalife': digitalifeLogo,
  'PCEL' : pcellogo,
}

const getInStockStores = (listings: Listing[]) => [
  ...new Map(
    listings
      .filter(l => l.availabilitystatus === 'InStock' || l.availabilitystatus === 'Available')
      .map(l => [l.storename, l])
  ).values()
]

function GpuRow({ gpu }: GpuRowProps) {
  const navigate = useNavigate()
  const inStockStores = getInStockStores(gpu.listings)

  return (
    <>
      {/* Desktop row */}
      <tr 
        className="hidden md:table-row border-b hover:bg-gray-50 cursor-pointer"
        onClick={() => navigate(`/gpu/${gpu.productid}`)}
      >
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
        <td className="p-2">
          <div className="flex items-center justify-center gap-1">
            {inStockStores.length === 0 
              ? <span className="text-xs text-red-500 font-bold">Sin stock</span>
              : inStockStores.map(l => storeLogos[l.storename] && (
                  <img
                    key={l.link}
                    src={storeLogos[l.storename]}
                    alt={l.storename}
                    title={l.storename}
                    className="w-6 h-6 object-contain"
                  />
                ))
            }
          </div>
        </td>
        <td className="p-2 text-center text-sm text-gray-600">
          {gpu.color ? 'Blanco' : 'Negro/Gris'}
        </td>
        <td className="p-2 text-right font-bold text-lg">
          {gpu.lowestPrice ? `$${gpu.lowestPrice.toLocaleString()} MXN` : 'N/A'}
        </td>
      </tr>

      {/* Mobile card */}
      <div
        className="md:hidden border rounded-lg p-3 mb-3 cursor-pointer hover:bg-gray-50"
        onClick={() => navigate(`/gpu/${gpu.productid}`)}
      >
        <div className="flex gap-3">
          {gpu.listings[0]?.imageurl && (
            <img 
              src={gpu.listings[0].imageurl} 
              alt={gpu.canonicalname}
              className="w-20 h-20 object-contain shrink-0"
            />
          )}
          <div className="flex-1">
            <p className="font-semibold">
              {gpu.manufacturer_normalized} {gpu.coolervariant_normalized}
            </p>
            <p className="text-sm text-gray-500">{gpu.model_normalized}</p>

            <div className="mt-2 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">VRAM</span>
                <span>{gpu.vramgb} GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Overclock</span>
                <span>{gpu.oc ? 'Sí' : 'No'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Color</span>
                <span>{gpu.color ? 'Blanco' : 'Negro/Gris'}</span>
            </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 pt-3 border-t">
          <div className="flex items-center gap-1">
          {inStockStores.length === 0
            ? <span className="text-xs text-red-500 font-bold">Sin stock</span>
            : (
              <>
                <span className="text-xs text-green-500 font-bold">Stock: </span>
                {inStockStores.map(l => storeLogos[l.storename] && (
                  <img
                    key={l.link}
                    src={storeLogos[l.storename]}
                    alt={l.storename}
                    title={l.storename}
                    className="w-6 h-6 object-contain"
                  />
                ))}
              </>
            )
          }
          </div>
          <span className="font-bold text-lg">
            {gpu.lowestPrice ? `$${gpu.lowestPrice.toLocaleString()} MXN` : 'N/A'}
          </span>
        </div>
      </div>
    </>
  )
}

export default GpuRow