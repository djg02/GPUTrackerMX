interface PaginationProps {
  page: number
  totalPages: number
  totalCount: number
  onPrev: () => void
  onNext: () => void
}

function Pagination({ page, totalPages, totalCount, onPrev, onNext }: PaginationProps) {
  return (
    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <button
        onClick={onPrev}
        disabled={page <= 1}
        className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed text-gray-400 border-gray-700 enabled:hover:border-orange-500 enabled:hover:text-orange-500"
      >
        Anterior
      </button>

      <span className="text-sm text-gray-600 text-center">
        Página {page} de {totalPages} ({totalCount} resultados)
      </span>

      <button
        onClick={onNext}
        disabled={page >= totalPages}
        className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed text-gray-400 border-gray-700 enabled:hover:border-orange-500 enabled:hover:text-orange-500"
      >
        Siguiente
      </button>
    </div>
  )
}

export default Pagination