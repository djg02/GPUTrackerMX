import type { Gpu } from '../types'

interface SpecsSidebarProps {
  gpu: Gpu
}

function SpecsSidebar({ gpu }: SpecsSidebarProps) {
  return (
    <div className="w-full md:w-64 md:shrink-0">
      {/* Image */}
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
                <dd>{gpu.color ?'Blanco' : 'Negro/Gris'}</dd>
            </div>
            {/* Boost clock*/}
            {gpu.boostclock && (
            <div className="flex justify-between py-1">
                <dt className="text-gray-500">Boost Clock</dt>
                <dd>{gpu.boostclock} MHz</dd>
            </div>
            )}
            {/* Base clock*/}
            {gpu.baseclock && (
            <div className="flex justify-between py-1">
                <dt className="text-gray-500">Base Clock</dt>
                <dd>{gpu.baseclock} MHz</dd>
          </div>
        )}
      </dl>
    </div>
  )
}

export default SpecsSidebar