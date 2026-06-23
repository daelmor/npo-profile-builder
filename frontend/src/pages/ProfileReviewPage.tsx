import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { getProfile } from '@/api/client'
import type { Completeness, ProfileDetail, TrackedField } from '@/api/types'
import FieldRow from '@/components/FieldRow'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { FIELD_LABELS, PROFILE_SECTIONS } from '@/lib/profileFields'
import { cn } from '@/lib/utils'

function CompletenessLegend({ c }: { c: Completeness }) {
  const stats = [
    { label: 'extracted', value: c.extracted, dot: 'bg-emerald-500' },
    { label: 'inferred', value: c.inferred, dot: 'bg-amber-500' },
    { label: 'you provided', value: c.user_provided, dot: 'bg-sky-500' },
    { label: 'missing', value: c.missing, dot: 'bg-muted-foreground/40' },
  ]
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground">
      {stats.map((s) => (
        <span key={s.label} className="inline-flex items-center gap-1.5">
          <span className={cn('size-2 rounded-full', s.dot)} />
          <span className="font-medium text-foreground">{s.value}</span> {s.label}
        </span>
      ))}
    </div>
  )
}

export default function ProfileReviewPage() {
  const { profileId } = useParams<{ profileId: string }>()
  const [detail, setDetail] = useState<ProfileDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!profileId) return
    getProfile(profileId)
      .then((d) => {
        setDetail(d)
        setError(null)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load profile.'))
  }, [profileId])

  if (error) return <p className="text-destructive">{error}</p>
  if (!detail) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-5 w-80" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  const { profile } = detail
  const title = profile.legal_name.value ?? 'Untitled profile'

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <CompletenessLegend c={detail.completeness} />
          <p className="text-xs text-muted-foreground">
            Source: {detail.source.filename ?? 'pasted text'} · {detail.source.char_count} chars ·{' '}
            {detail.source.chunk_count} chunk(s)
          </p>
        </div>
        <Button asChild>
          <Link to={`/chat/${detail.id}`}>
            Fill the gaps <ArrowRight />
          </Link>
        </Button>
      </div>

      <div className="space-y-4">
        {PROFILE_SECTIONS.map((section) => (
          <Card key={section.title}>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                {section.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {section.fields.map((key) => (
                <FieldRow
                  key={key}
                  label={FIELD_LABELS[key]}
                  field={profile[key] as TrackedField<unknown>}
                />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}
