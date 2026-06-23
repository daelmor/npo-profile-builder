import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, Loader2, Send } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { getConversation, sendChatMessage, startConversation } from '@/api/client'
import type { ChatMessage, Completeness, NonprofitProfile, TrackedField } from '@/api/types'
import FieldRow from '@/components/FieldRow'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { FIELD_LABELS, PROFILE_SECTIONS } from '@/lib/profileFields'
import { cn } from '@/lib/utils'

function CompletenessMeter({ c }: { c: Completeness }) {
  const filled = c.total - c.missing
  const pct = c.total ? Math.round((filled / c.total) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>
          {filled}/{c.total} fields filled
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted">
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
          <Button variant="ghost" size="sm" asChild>
            <Link to={`/profiles/${profileId}`}>
              <ArrowLeft /> Back to profile
            </Link>
          </Button>
        )}
      </div>

      {error && <p className="text-destructive">{error}</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Conversation */}
        <Card className="flex h-[34rem] flex-col overflow-hidden">
          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div
                  className={cn(
                    'max-w-[80%] rounded-2xl px-3 py-2 text-sm',
                    m.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground',
                  )}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {busy && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="size-3 animate-spin" /> thinking…
              </div>
            )}
          </div>
          <form onSubmit={handleSubmit} className="flex gap-2 border-t p-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your answer…"
            />
            <Button type="submit" size="icon" disabled={busy || !input.trim()}>
              <Send />
            </Button>
          </form>
        </Card>

        {/* Live profile */}
        <Card className="flex h-[34rem] flex-col overflow-hidden">
          <div className="border-b p-4">
            <h2 className="mb-2 text-sm font-semibold text-muted-foreground">Live profile</h2>
            {completeness && <CompletenessMeter c={completeness} />}
          </div>
          <div className="flex-1 overflow-y-auto px-4">
            {profile &&
              PROFILE_SECTIONS.map((section) => (
                <div key={section.title} className="py-3">
                  <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
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
        </Card>
      </div>
    </section>
  )
}
