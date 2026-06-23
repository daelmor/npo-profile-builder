import { useEffect, useState } from 'react'
import { getHealth } from '@/api/client'
import { cn } from '@/lib/utils'

type State = 'checking' | 'ok' | 'down'

const LABEL: Record<State, string> = {
  checking: 'Checking backend…',
  ok: 'Backend connected',
  down: 'Backend unreachable',
}

const DOT: Record<State, string> = {
  checking: 'bg-amber-400',
  ok: 'bg-emerald-500',
  down: 'bg-rose-500',
}

export default function BackendStatus() {
  const [state, setState] = useState<State>('checking')

  useEffect(() => {
    let active = true
    getHealth()
      .then(() => active && setState('ok'))
      .catch(() => active && setState('down'))
    return () => {
      active = false
    }
  }, [])

  return (
    <span className="inline-flex items-center gap-2 text-xs text-muted-foreground">
      <span className={cn('size-2 rounded-full', DOT[state])} />
      {LABEL[state]}
    </span>
  )
}
