import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import type { Gpu } from '../types'
import SpecsSidebar from '../components/SpecsSidebar'
import PricesTable from '../components/PricesTable'

function GpuDetailPage() {
  const { id } = useParams()
  const [gpu, setGpu] = useState<Gpu | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

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
    
    <div className="p-8 bg-gray-900 min-h-screen">
        <button 
          onClick={() => navigate(-1)}
          className="text-orange-500 hover:text-orange-400 text-sm"
        >
          &larr; Volver al listado
        </button>
     <h1 className="text-2xl font-bold mt-4 text-gray-50">{gpu.canonicalname}</h1>

    <div className="flex flex-col md:flex-row gap-8 mt-6">
        <SpecsSidebar gpu={gpu} />
        <PricesTable listings={gpu.listings} />
    </div>
    </div>
  )
}

export default GpuDetailPage