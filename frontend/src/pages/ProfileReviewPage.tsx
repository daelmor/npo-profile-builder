import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getProfile } from '../api/client'
import type { Completeness, ProfileDetail, TrackedField } from '../api/types'
import FieldRow from '../components/FieldRow'
import { FIELD_LABELS, PROFILE_SECTIONS } from '../lib/profileFields'

function CompletenessBar({ c }: { c: Completeness }) {
  const stats: { label: string; value: number; dot: string }[] = [
    { label: 'extracted', value: c.extracted, dot: 'bg-emerald-500' },
    { label: 'inferred', value: c.inferred, dot: 'bg-amber-500' },
    { label: 'you provided', value: c.user_provided, dot: 'bg-sky-500' },
    { label: 'missing', value: c.missing, dot: 'bg-slate-300' },
  ]
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-600">
      {stats.map((s) => (
        <span key={s.label} className="inline-flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${s.dot}`} />
          <span className="font-medium text-slate-900">{s.value}</span> {s.label}
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
    setError(null)
    getProfile(profileId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load profile.'))
  }, [profileId])

  if (error) return <p className="text-rose-600">{error}</p>
  if (!detail) return <p className="text-slate-500">Loading…</p>

  const { profile } = detail
  const title = profile.legal_name.value ?? 'Untitled profile'

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <CompletenessBar c={detail.completeness} />
          <p className="text-xs text-slate-400">
            Source: {detail.source.filename ?? 'pasted text'} · {detail.source.char_count} chars ·{' '}
            {detail.source.chunk_count} chunk(s)
          </p>
        </div>
        <Link
          to={`/chat/${detail.id}`}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Fill the gaps →
        </Link>
      </div>

      <div className="space-y-6">
        {PROFILE_SECTIONS.map((section) => (
          <div key={section.title} className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-1 text-sm font-semibold tracking-wide text-slate-400 uppercase">
              {section.title}
            </h2>
            {section.fields.map((key) => (
              <FieldRow
                key={key}
                label={FIELD_LABELS[key]}
                field={profile[key] as TrackedField<unknown>}
              />
            ))}
          </div>
        ))}
      </div>
    </section>
  )
}
