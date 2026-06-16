interface PaginationProps {
  page: number
  totalPages: number
  totalCount: number
  onPrev: () => void
  onNext: () => void
}

function Pagination({ page, totalPages, totalCount, onPrev, onNext }: PaginationProps) {
  return (
    <div className="mt-4 flex items-center justify-between">
      <button
        onClick={onPrev}
        disabled={page <= 1}
        className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Anterior
      </button>

      <span className="text-sm text-gray-600">
        Página {page} de {totalPages} ({totalCount} resultados)
      </span>

      <button
        onClick={onNext}
        disabled={page >= totalPages}
        className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Siguiente
      </button>
    </div>
  )
}

export default Pagination