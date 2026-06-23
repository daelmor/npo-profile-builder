import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getConversation, sendChatMessage, startConversation } from '../api/client'
import type { ChatMessage, Completeness, NonprofitProfile, TrackedField } from '../api/types'
import FieldRow from '../components/FieldRow'
import { FIELD_LABELS, PROFILE_SECTIONS } from '../lib/profileFields'

function CompletenessMeter({ c }: { c: Completeness }) {
  const filled = c.total - c.missing
  const pct = c.total ? Math.round((filled / c.total) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-500">
        <span>
          {filled}/{c.total} fields filled
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-slate-100">
        <div className="h-1.5 rounded-full bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { profileId } = useParams<{ profileId: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [profile, setProfile] = useState<NonprofitProfile | null>(null)
  const [completeness, setCompleteness] = useState<Completeness | null>(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const initialized = useRef(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!profileId || initialized.current) return
    initialized.current = true
    ;(async () => {
      setBusy(true)
      try {
        const state = await getConversation(profileId)
        setProfile(state.profile)
        setCompleteness(state.completeness)
        if (state.started) {
          setMessages(state.transcript)
        } else {
          const res = await startConversation(profileId)
          setMessages(res.transcript)
          setProfile(res.profile)
          setCompleteness(res.completeness)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load the conversation.')
      } finally {
        setBusy(false)
      }
    })()
  }, [profileId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages, busy])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = input.trim()
    if (!profileId || !text || busy) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text }])
    setBusy(true)
    setError(null)
    try {
      const res = await sendChatMessage(profileId, text)
      setMessages(res.transcript)
      setProfile(res.profile)
      setCompleteness(res.completeness)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Message failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Fill the gaps</h1>
        {profileId && (
          <Link to={`/profiles/${profileId}`} className="text-sm text-slate-500 hover:text-slate-900">
            ← Back to profile
          </Link>
        )}
      </div>

      {error && (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-600/20">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Conversation */}
        <div className="flex h-[34rem] flex-col rounded-xl border border-slate-200 bg-white">
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div
                  className={
                    m.role === 'user'
                      ? 'max-w-[80%] rounded-2xl bg-slate-900 px-3 py-2 text-sm text-white'
                      : 'max-w-[80%] rounded-2xl bg-slate-100 px-3 py-2 text-sm text-slate-800'
                  }
                >
                  {m.text}
                </div>
              </div>
            ))}
            {busy && <div className="text-xs text-slate-400">…</div>}
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your answer…"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:ring-0"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
            >
              Send
            </button>
          </form>
        </div>

        {/* Live profile */}
        <div className="flex h-[34rem] flex-col rounded-xl border border-slate-200 bg-white">
          <div className="border-b border-slate-100 p-4">
            <h2 className="mb-2 text-sm font-semibold text-slate-500">Live profile</h2>
            {completeness && <CompletenessMeter c={completeness} />}
          </div>
          <div className="flex-1 overflow-y-auto px-4">
            {profile &&
              PROFILE_SECTIONS.map((section) => (
                <div key={section.title} className="py-3">
                  <h3 className="mb-1 text-xs font-semibold tracking-wide text-slate-400 uppercase">
                    {section.title}
                  </h3>
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
        </div>
      </div>
    </section>
  )
}
