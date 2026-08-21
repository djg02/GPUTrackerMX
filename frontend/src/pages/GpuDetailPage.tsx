import { useState, useEffect } from 'react'
import { useParams, useNavigate} from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import type { Gpu } from '../types'
import SpecsSidebar from '../components/SpecsSidebar'
import PricesTable from '../components/PricesTable'
import PriceHistoryChart from '../components/PriceHistoryChart'

function GpuDetailPage() {
  const { id } = useParams()
  const [gpu, setGpu] = useState<Gpu | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    setLoading(true)
    setError(null)

    fetch(`${import.meta.env.VITE_API_URL}/gpus/${id}`)
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

  const pageTitle = `${gpu.canonicalname} Precios en México | GPU Tracker MX`
  const seoHeading = `Compara precios, stock y envío de la ${gpu.canonicalname} en México. Consulta precios en DDTech, Cyberpuerta, Mercado Libre y más.`
  
  return (
    <div>
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={seoHeading} />
        <link rel="canonical" href={`https://gputracker.mx/gpu/${gpu.productid}`} />
      </Helmet>
    <div className="p-8 bg-gray-900 min-h-screen overflow-x-hidden">
        <button 
          onClick={() => navigate(-1)}
          className="text-orange-500 hover:text-orange-400 text-sm"
        >
          &larr; Volver al listado
        </button>
      <h1 className="text-2xl font-bold mt-4 text-gray-50">{gpu.canonicalname}</h1>
      <h2 className="sr-only">{seoHeading}</h2>

    <div className="flex flex-col md:flex-row gap-8 mt-6">
        <SpecsSidebar gpu={gpu} />
        <PricesTable listings={gpu.listings} />
    </div>
        <PriceHistoryChart productId={gpu.productid} />
    </div>
    </div>
  )
}

export default GpuDetailPage