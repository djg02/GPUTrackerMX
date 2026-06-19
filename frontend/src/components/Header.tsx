import { Link } from 'react-router-dom'
import logo from '../assets/logos/logo.png'

function Header() {
  return (
    <header className="border-b px-8 py-4 flex items-center gap-3">
      <Link to="/" className="flex items-center gap-3 hover:opacity-80">
        <img src={logo} alt="GPU Tracker MX" className="h-20 w-auto" />
        <span 
        className="text-7xl font-bold text-blue-600"
        style={{ fontFamily: 'Geo', fontStyle: 'italic' }}
        >
            Tracker MX
        </span>
      </Link>
    </header>
  )
}

export default Header