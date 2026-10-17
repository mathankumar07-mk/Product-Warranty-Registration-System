export default function AdminPagination({ page, onPrev, onNext, hasNext = true, label }) {
  return (
    <div className="admin-pagination">
      <button
        type="button"
        className="btn btn-outline btn-small"
        disabled={page <= 1}
        onClick={onPrev}
      >
        Prev
      </button>
      <span>
        Page {page}
        {label ? ` · ${label}` : ''}
      </span>
      <button
        type="button"
        className="btn btn-outline btn-small"
        disabled={!hasNext}
        onClick={onNext}
      >
        Next
      </button>
    </div>
  );
}
