import githubLogo from '../assets/logos/githublogo.png'

function Footer() {
  return (
  <footer className="border-t border-gray-700 px-8 py-4 mt-8 bg-gray-900">
    <div className="flex flex-col md:flex-row items-center justify-center gap-4">
      <a
        href="https://github.com/djg02/GPUTrackerMX"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-orange-500"
      >
        <img src={githubLogo} alt="GitHub" className="h-15 w-auto" />
        GPU Tracker MX en GitHub
      </a>

      <span className="hidden md:inline text-gray-600">|</span>

      <div className="flex flex-col items-center text-center">
        <p className="text-xs text-gray-500">
          ¿Dudas, sugerencias o comentarios? ¡Escríbenos!
        </p>
        <a
          href="mailto:contacto@gputracker.mx"
          className="text-sm font-bold text-gray-400 hover:text-orange-500 break-all"
        >
          contacto@gputracker.mx
        </a>
      </div>
    </div>
  </footer>
    )
}

export default Footer