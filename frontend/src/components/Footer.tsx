import githubLogo from '../assets/logos/githublogo.png'

function Footer() {
  return (
    <footer className="border-t border-gray-700 px-8 py-4 mt-8 flex items-center justify-center gap-2 bg-gray-900">
        <a
        href="https://github.com/djg02/GPUTrackerMX"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-orange-500"
        >
        <img src={githubLogo} alt="GitHub" className="h-15 w-auto" />
        GPUTrackerMX en GitHub
      </a>
    </footer>
  )
}

export default Footer