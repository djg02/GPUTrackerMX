import { Link } from 'react-router-dom'
import logo from '../assets/logos/logo.png'

function Header() {
  return (
    <header className="border-b border-gray-700 px-8 py-4 bg-gray-900">
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
    </header>
  )
}

export default Header