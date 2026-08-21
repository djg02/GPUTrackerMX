import { Link, useLocation } from 'react-router-dom'
import logo from '../assets/logos/logo.png'

function Header() {
  const location = useLocation()
  const isDetailPage = location.pathname.startsWith('/gpu/')

  return (
    <header className="border-b border-gray-700 px-8 py-4 bg-gray-900">
      {!isDetailPage && (
        <h1 className="sr-only">GPU Tracker MX - Compara precios, stock y envío de GPUs en las principales tiendas mexicanas.</h1>
      )}
      <div className="flex flex-col md:flex-row items-center justify-between gap-2">
        <Link
          to="/"
          className="flex flex-col items-center gap-2 sm:flex-row"
        >
          <img
            src={logo}
            alt="GPU Tracker MX"
            className="h-20 w-auto"
          />
          <span
            className="text-4xl sm:text-7xl font-bold text-orange-500 text-center sm:text-left"
            style={{ fontFamily: 'Geo', fontStyle: 'italic' }}
          >
            Tracker MX
          </span>
        </Link>

        <p className="text-sm text-orange-500 font-bold text-center md:text-right max-w-xs">
          Compara precios, stock y envío de GPUs en las principales tiendas mexicanas.
        </p>
      </div>
    </header>
  )
}

export default Header