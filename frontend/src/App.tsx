import { Routes, Route } from 'react-router-dom'
import GpuListPage from './pages/GpuListPage'
import GpuDetailPage from './pages/GpuDetailPage'
import Header from './components/Header'
import Footer from './components/Footer'

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-900 text-gray-50">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<GpuListPage />} />
          <Route path="/gpu/:id" element={<GpuDetailPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App