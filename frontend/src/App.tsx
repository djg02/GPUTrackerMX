import { Routes, Route } from 'react-router-dom'
import GpuListPage from './pages/GpuListPage'
import GpuDetailPage from './pages/GpuDetailPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<GpuListPage />} />
      <Route path="/gpu/:id" element={<GpuDetailPage />} />
    </Routes>
  )
}

export default App