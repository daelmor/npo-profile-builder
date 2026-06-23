import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listProfiles } from '@/api/client'
import type { ProfileSummary } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

function CompletenessBar({ filled, total }: { filled: number; total: number }) {
  const pct = total ? Math.round((filled / total) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="h-1.5 w-full rounded-full bg-muted">
        <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-muted-foreground">
        {filled}/{total} fields filled
      </p>
    </div>
  )
}

export default function ProfilesPage() {
  const [profiles, setProfiles] = useState<ProfileSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listProfiles()
      .then(setProfiles)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load profiles.'))
  }, [])

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Profiles</h1>
          <p className="mt-1 text-muted-foreground">Every nonprofit you've ingested.</p>
        </div>
        <Button asChild>
          <Link to="/">New profile</Link>
        </Button>
      </div>

      {error && <p className="text-destructive">{error}</p>}

      {!profiles ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : profiles.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No profiles yet —{' '}
            <Link to="/" className="font-medium text-foreground underline underline-offset-4">
              ingest your first document
            </Link>
            .
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {profiles.map((p) => (
            <Link key={p.id} to={`/profiles/${p.id}`} className="block">
              <Card className="h-full transition-colors hover:border-foreground/20">
                <CardHeader>
                  <CardTitle className="text-base">{p.legal_name ?? 'Untitled profile'}</CardTitle>
                  {p.country && <p className="text-xs text-muted-foreground">{p.country}</p>}
                </CardHeader>
                <CardContent className="space-y-3">
                  {p.cause_areas.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {p.cause_areas.slice(0, 4).map((c) => (
                        <Badge key={c} variant="secondary">
                          {c}
                        </Badge>
                      ))}
                    </div>
                  )}
                  <CompletenessBar
                    filled={p.completeness.total - p.completeness.missing}
                    total={p.completeness.total}
                  />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}
