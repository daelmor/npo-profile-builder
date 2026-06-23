import { useState } from 'react'
import type { FormEvent } from 'react'
import { Loader2, Search as SearchIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { searchProfiles } from '@/api/client'
import type { SearchResult } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

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
        <h1 className="text-2xl font-semibold tracking-tight">Search</h1>
        <p className="mt-1 max-w-prose text-muted-foreground">
          Natural-language search across profiles and their source documents. Each result links
          back to the supporting evidence.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. literacy programs for out-of-school children"
        />
        <Button type="submit" disabled={busy || !query.trim()}>
          {busy ? <Loader2 className="animate-spin" /> : <SearchIcon />}
          Search
        </Button>
      </form>

      {error && <p className="text-destructive">{error}</p>}

      {results && results.length === 0 && (
        <p className="text-muted-foreground">No matches — try ingesting a document first, or rephrasing.</p>
      )}

      <div className="space-y-4">
        {results?.map((r) => (
          <Link key={r.profile_id} to={`/profiles/${r.profile_id}`} className="block">
            <Card className="transition-colors hover:border-foreground/20">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-base">{r.legal_name ?? 'Untitled profile'}</CardTitle>
                    {r.country && <p className="text-xs text-muted-foreground">{r.country}</p>}
                  </div>
                  <Badge variant="outline" className="shrink-0 border-emerald-200 bg-emerald-50 text-emerald-700">
                    {Math.round(r.score * 100)}% match
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {r.mission && <p className="text-sm text-muted-foreground">{r.mission}</p>}
                {r.cause_areas.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {r.cause_areas.map((c) => (
                      <Badge key={c} variant="secondary">
                        {c}
                      </Badge>
                    ))}
                  </div>
                )}
                <blockquote className="border-l-2 pl-3 text-xs text-muted-foreground italic">
                  “{r.evidence.text.slice(0, 240).trim()}…”
                </blockquote>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  )
}
