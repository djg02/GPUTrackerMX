import type { Listing, Gpu } from '../types'

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

interface SpecsSidebarProps {
  gpu: Gpu
}

function SpecsSidebar({ gpu }: SpecsSidebarProps) {
  return (
    <div className="w-full md:w-64 md:shrink-0">
      {/* Image */}
      {gpu.listings[0]?.imageurl && (
        <img
          src={getBestImage(gpu.listings)}
          alt={gpu.canonicalname}
          className="w-full object-contain border border-gray-700 rounded bg-gray-800 p-2"
        />
      )}

      {/* Specs list */}
      <dl className="mt-4 text-sm divide-y divide-gray-700">
            {/* Manufacturer */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Fabricante</dt>
                <dd className="text-gray-200">{gpu.manufacturer_normalized}</dd>
            </div>
            {/* Model */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Modelo</dt>
                <dd className="text-gray-200">{gpu.model_normalized}</dd>
            </div>
            {/* Series */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Serie</dt>
                <dd className="text-gray-200">{gpu.series ?? '—'}</dd>
            </div>
            {/* VRAM */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">VRAM</dt>
                <dd className="text-gray-200">{parseFloat(gpu.vramgb)} GB</dd>
            </div>
            {/* Memory type */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Memoria</dt>
                <dd className="text-gray-200">{gpu.memorytype}</dd>
            </div>
            {/* Overclock */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Overclock</dt>
                <dd className="text-gray-200">{gpu.oc ? 'Sí' : 'No'}</dd>
            </div>
            {/* Bus width */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Bus</dt>
                <dd className="text-gray-200">{gpu.buswidth}-bit</dd>
            </div>
            {/* PCIe interface version */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">PCIe</dt>
                <dd className="text-gray-200">{gpu.interfaceversion}</dd>
            </div>
            {/* Fan count */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Ventiladores</dt>
                <dd className="text-gray-200">{gpu.fans ?? '—'}</dd>
            </div>
            {/* Color */}
            <div className="flex justify-between py-1">
                <dt className="text-gray-400">Color</dt>
                <dd className="text-gray-200">{gpu.color ?'Blanco' : 'Negro/Gris'}</dd>
            </div>
            {/* Boost clock*/}
            {gpu.boostclock && (
            <div className="flex justify-between py-1">
                <dt className="text-gray-200">Boost Clock</dt>
                <dd className="text-gray-400">{gpu.boostclock} MHz</dd>
            </div>
            )}
            {/* Base clock*/}
            {gpu.baseclock && (
            <div className="flex justify-between py-1">
                <dt className="text-gray-200">Base Clock</dt>
                <dd className="text-gray-400">{gpu.baseclock} MHz</dd>
          </div>
        )}
      </dl>
    </div>
  )
}

export default SpecsSidebar