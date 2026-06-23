import type { FieldStatus } from '../api/types'

const STYLES: Record<FieldStatus, string> = {
  extracted: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  inferred: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  user_provided: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  missing: 'bg-slate-100 text-slate-500 ring-slate-400/30',
}

const LABELS: Record<FieldStatus, string> = {
  extracted: 'Extracted',
  inferred: 'Inferred',
  user_provided: 'You provided',
  missing: 'Missing',
}

export default function StatusBadge({ status }: { status: FieldStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  )
}
