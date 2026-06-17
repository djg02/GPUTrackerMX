import { useNavigate } from 'react-router-dom'
import type { Listing, Gpu } from '../types'
import ddtechLogo from '../assets/store_logos/ddtech.png'
import cyberpuertaLogo from '../assets/store_logos/cyberpuerta.png'
import digitalifeLogo from '../assets/store_logos/digitalife.png'

interface GpuRowProps {
  gpu: Gpu
}

const storeLogos: Record<string, string> = {
  'DDTech': ddtechLogo,
  'Cyberpuerta': cyberpuertaLogo,
  'digitalife': digitalifeLogo,
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
  return (
    <tr key={gpu.productid} 
        className="border-b hover:bg-gray-50 cursor-pointer"
        onClick={() => navigate(`/gpu/${gpu.productid}`)}>
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
          {getInStockStores(gpu.listings).length === 0 
            ? <span className="text-xs text-red-500 font-bold">Agotado</span>
            : getInStockStores(gpu.listings).map(l => storeLogos[l.storename] && (
                <img
                  key={l.storename}
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
  )
}

export default GpuRow