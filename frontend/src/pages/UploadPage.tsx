import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ingestFile, ingestText } from '../api/client'
import BackendStatus from '../components/BackendStatus'

type Mode = 'text' | 'file'

export default function UploadPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>('text')
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = mode === 'text' ? text.trim().length > 0 : file !== null

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      const detail =
        mode === 'text' ? await ingestText(text) : await ingestFile(file as File)
      navigate(`/profiles/${detail.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingestion failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Build a profile</h1>
          <p className="mt-1 max-w-prose text-slate-600">
            Upload a PDF or paste text. The pipeline extracts a structured nonprofit profile and
            tracks the provenance of every field.
          </p>
        </div>
        <BackendStatus />
      </div>

      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm">
        {(['text', 'file'] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={
              mode === m
                ? 'rounded-md bg-slate-900 px-3 py-1.5 font-medium text-white'
                : 'rounded-md px-3 py-1.5 text-slate-600 hover:text-slate-900'
            }
          >
            {m === 'text' ? 'Paste text' : 'Upload PDF'}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'text' ? (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
            placeholder="Paste a nonprofit's about page, annual report text, grant narrative…"
            className="w-full rounded-lg border border-slate-300 p-3 font-mono text-sm shadow-sm focus:border-slate-900 focus:ring-0"
          />
        ) : (
          <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-300 bg-white p-10 text-slate-500 hover:border-slate-400">
            <input
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <span className="text-sm">{file ? file.name : 'Choose a PDF…'}</span>
          </label>
        )}

        {error && (
          <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-600/20">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!canSubmit || busy}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy ? 'Extracting…' : 'Extract profile'}
        </button>
      </form>
    </section>
  )
}
