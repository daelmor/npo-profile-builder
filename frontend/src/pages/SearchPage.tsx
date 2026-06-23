import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { searchProfiles } from '../api/client'
import type { SearchResult } from '../api/types'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const q = query.trim()
    if (!q || busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await searchProfiles(q, 8)
      setResults(res.results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Search nonprofits</h1>
        <p className="mt-1 max-w-prose text-slate-600">
          Natural-language search across profiles and their source documents. Each result links
          back to the supporting evidence.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. literacy programs for out-of-school children"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
        />
        <button
          type="submit"
          disabled={busy || !query.trim()}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
        >
          {busy ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-600/20">
          {error}
        </p>
      )}

      {results && results.length === 0 && (
        <p className="text-slate-500">No matches — try ingesting a document first, or rephrasing.</p>
      )}

      <div className="space-y-4">
        {results?.map((r) => (
          <Link
            key={r.profile_id}
            to={`/profiles/${r.profile_id}`}
            className="block rounded-xl border border-slate-200 bg-white p-5 hover:border-slate-300"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-slate-900">{r.legal_name ?? 'Untitled profile'}</h2>
                {r.country && <p className="text-xs text-slate-400">{r.country}</p>}
              </div>
              <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
                {Math.round(r.score * 100)}% match
              </span>
            </div>
            {r.mission && <p className="mt-2 text-sm text-slate-600">{r.mission}</p>}
            {r.cause_areas.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {r.cause_areas.map((c) => (
                  <span key={c} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {c}
                  </span>
                ))}
              </div>
            )}
            <blockquote className="mt-3 border-l-2 border-slate-200 pl-3 text-xs text-slate-400 italic">
              “{r.evidence.text.slice(0, 240).trim()}…”
            </blockquote>
          </Link>
        ))}
      </div>
    </section>
  )
}
