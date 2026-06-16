import GpuRow from './GpuRow'
import type { Listing, Gpu } from '../types'

interface GpuTableProps {
  gpus: Gpu[]
  sort: string
  onSort: (column: 'price' | 'name') => void
}

function GpuTable({ gpus, sort, onSort }: GpuTableProps) {
  return (
    <table className="mt-4 w-full border-collapse">
      <thead>
        <tr className="border-b text-left text-sm text-gray-500">
          <th
            className="p-2 text-left cursor-pointer select-none hover:text-gray-800"
            onClick={() => onSort('name')}
          >
            Nombre {sort === 'name_asc' ? '▲' : sort === 'name_desc' ? '▼' : ''}
          </th>
          <th className="p-2 text-center">Modelo</th>
          <th className="p-2 text-center">VRAM</th>
          <th className="p-2 text-center">Boost Clock</th>
          <th className="p-2 text-center">OC</th>
          <th className="p-2 text-center">En Stock</th>
          <th className="p-2 text-center">Color</th>
          <th
            className="p-2 text-right cursor-pointer select-none hover:text-gray-800"
            onClick={() => onSort('price')}
          >
            Precio {sort === 'price_asc' ? '▲' : sort === 'price_desc' ? '▼' : ''}
          </th>
        </tr>
      </thead>
      <tbody>
        {gpus.map(gpu => (
          <GpuRow key={gpu.productid} gpu={gpu} />
        ))}
      </tbody>
    </table>
  )
}

export default GpuTable