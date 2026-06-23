import type { TrackedField } from '../api/types'
import StatusBadge from './StatusBadge'

function formatValue(value: unknown): string | null {
  if (value === null || value === undefined) return null
  if (Array.isArray(value)) return value.length ? value.join(', ') : null
  return String(value)
}

export default function FieldRow({
  label,
  field,
}: {
  label: string
  field: TrackedField<unknown>
}) {
  const display = formatValue(field.value)

  return (
    <div className="grid grid-cols-[11rem_1fr] gap-4 border-b border-slate-100 py-3 last:border-0">
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          {display ? (
            <span className="text-slate-900">{display}</span>
          ) : (
            <span className="text-slate-400 italic">—</span>
          )}
          <StatusBadge status={field.status} />
          {field.confidence !== null && (
            <span className="text-xs text-slate-400">{Math.round(field.confidence * 100)}% conf.</span>
          )}
        </div>
        {field.source_quote && (
          <p className="text-xs text-slate-400 italic">“{field.source_quote}”</p>
        )}
      </div>
    </div>
  )
}
