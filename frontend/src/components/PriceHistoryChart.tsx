import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface HistoryPoint {
  storename: string
  day: string
  price: number
}

interface PriceHistoryChartProps {
  productId: string
}

const RANGE_OPTIONS = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1A', days: 365 },
  { label: 'Todo', days: undefined },
]

const STORE_COLORS: Record<string, string> = {
  'Cyberpuerta': '#f97316',
  'DDTech': '#3b82f6',
  'digitalife': '#22c55e',
  'PCEL': '#eab308',
  'Zegucom': '#a855f7',
  'MercadoLibre': '#ec4899',
  'Intercompras': '#ef4444', 
}

function PriceHistoryChart({ productId }: PriceHistoryChartProps) {
  const [rawData, setRawData] = useState<HistoryPoint[]>([])
  const [days, setDays] = useState<number | undefined>(undefined)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = days ? `?days=${days}` : ''
    fetch(`${import.meta.env.VITE_API_URL}/gpus/${productId}/history${params}`)
      .then(res => res.json())
      .then(json => setRawData(json))
      .finally(() => setLoading(false))
  }, [productId, days])

  // Reshape data: one row per day, one column per store
  const stores = [...new Set(rawData.map(d => d.storename))]
  const dayMap = new Map<string, any>()

  rawData.forEach(point => {
    const dayKey = point.day.split('T')[0]
    if (!dayMap.has(dayKey)) {
      dayMap.set(dayKey, { day: dayKey })
    }
    dayMap.get(dayKey)[point.storename] = point.price
  })

  const chartData = [...dayMap.values()].sort((a, b) => a.day.localeCompare(b.day))

  return (
    <div className="mt-8 w-full overflow-hidden">
    <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <h2 className="font-semibold text-gray-200">Historial de precios</h2>
        <div className="flex gap-1">
        {RANGE_OPTIONS.map(opt => (
            <button
            key={opt.label}
            onClick={() => setDays(opt.days)}
            className={`px-3 py-1 rounded-full border text-xs ${
                days === opt.days
                ? 'bg-orange-500 text-white border-orange-500'
                : 'text-gray-400 border-gray-700 hover:border-orange-500 hover:text-orange-500'
            }`}
            >
            {opt.label}
            </button>
        ))}
        </div>
    </div>

      {loading && <p className="text-gray-500 text-sm">Cargando historial...</p>}

      {!loading && chartData.length === 0 && (
        <p className="text-gray-500 text-sm">Aún no hay suficiente historial para este producto.</p>
      )}

      {!loading && chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="day" stroke="#9ca3af" tick={{ fontSize: 12 }} />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 6 }}
              labelStyle={{ color: '#f9fafb' }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {stores.map(store => (
              <Line
                key={store}
                type="monotone"
                dataKey={store}
                stroke={STORE_COLORS[store] || '#9ca3af'}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

export default PriceHistoryChart