// Typed fetch client mirroring the backend API.

import type {
  ChatResponse,
  ConversationState,
  ProfileDetail,
  ProfileSummary,
  SearchResponse,
} from './types'

const BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function handle<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail ?? detail
    } catch {
      // non-JSON error body — keep statusText
    }
    throw new ApiError(resp.status, detail)
  }
  return resp.json() as Promise<T>
}

async function apiGet<T>(path: string): Promise<T> {
  return handle<T>(await fetch(`${BASE}${path}`))
}

async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  return handle<T>(
    await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}

async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  // No explicit Content-Type — the browser sets the multipart boundary.
  return handle<T>(await fetch(`${BASE}${path}`, { method: 'POST', body: form }))
}

export const getHealth = () => apiGet<{ status: string }>('/health')

export const ingestText = (text: string, title?: string) =>
  apiPostJson<ProfileDetail>('/ingest/text', { text, title: title ?? null })

export const ingestFile = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return apiUpload<ProfileDetail>('/ingest/file', form)
}

export const getProfile = (id: string) => apiGet<ProfileDetail>(`/profiles/${id}`)

export const listProfiles = () => apiGet<ProfileSummary[]>('/profiles')

export const getConversation = (id: string) => apiGet<ConversationState>(`/chat/${id}`)

export const startConversation = (id: string) =>
  apiPostJson<ChatResponse>(`/chat/${id}/start`, {})

export const sendChatMessage = (id: string, message: string) =>
  apiPostJson<ChatResponse>(`/chat/${id}/messages`, { message })

export const searchProfiles = (q: string, limit = 5) =>
  apiGet<SearchResponse>(`/search?q=${encodeURIComponent(q)}&limit=${limit}`)
