import type { FieldStatus } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const STYLES: Record<FieldStatus, string> = {
  extracted: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  inferred: 'border-amber-200 bg-amber-50 text-amber-700',
  user_provided: 'border-sky-200 bg-sky-50 text-sky-700',
  missing: 'border-transparent bg-muted text-muted-foreground',
}

const LABELS: Record<FieldStatus, string> = {
  extracted: 'Extracted',
  inferred: 'Inferred',
  user_provided: 'You provided',
  missing: 'Missing',
}

export default function StatusBadge({ status }: { status: FieldStatus }) {
  return (
    <Badge variant="outline" className={cn('font-medium', STYLES[status])}>
      {LABELS[status]}
    </Badge>
  )
}
