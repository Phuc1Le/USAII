const BASE_URL = "http://localhost:8000/api/v1"

const CLIENT_KEY_STORAGE = "zero-to-one:client-key"
const TOKEN_STORAGE = "zero-to-one:token"
const USER_STORAGE = "zero-to-one:user"

export const SIGNED_OUT_EVENT = "zero-to-one:signed-out"

export type AuthUser = {
  id: string
  email: string | null
  display_name: string
}

type TokenResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

// Who the backend thinks we are before anyone signs in. Generated here and kept
// in localStorage — not sessionStorage — so it survives closing the tab; a new
// key would look like a brand new person with no projects. This identifies, it
// does not authenticate, which is why registering makes the backend stop
// accepting it for that account.
function getClientKey(): string {
  let key = localStorage.getItem(CLIENT_KEY_STORAGE)
  if (!key) {
    key =
      typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `k-${Date.now()}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem(CLIENT_KEY_STORAGE, key)
  }
  return key
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE)
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_STORAGE)
    return raw ? (JSON.parse(raw) as AuthUser) : null
  } catch {
    return null
  }
}

function saveSession(res: TokenResponse): AuthUser {
  localStorage.setItem(TOKEN_STORAGE, res.access_token)
  localStorage.setItem(USER_STORAGE, JSON.stringify(res.user))
  return res.user
}

export function clearSession() {
  localStorage.removeItem(TOKEN_STORAGE)
  localStorage.removeItem(USER_STORAGE)
  // The client_key is deliberately left alone: signing out returns this browser
  // to the anonymous account it had before, rather than stranding it as a
  // stranger with no projects.
}

// A token can expire or be revoked mid-session, and that can happen inside any
// request from any component. Rather than teaching every caller to handle it,
// the session is cleared here and the app is told once, in one place.
function handleSignedOut() {
  if (!getToken()) return
  clearSession()
  window.dispatchEvent(new CustomEvent(SIGNED_OUT_EVENT))
}

function defaultHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const token = getToken()
  if (token) {
    // Once signed in, the header identity is refused by the backend anyway —
    // sending both would only make it ambiguous which one we meant.
    headers.Authorization = `Bearer ${token}`
  } else {
    headers["X-User-Id"] = getClientKey()
  }
  return headers
}

type StreamChatOptions = {
  content: string
  signal?: AbortSignal
  onToken: (token: string) => void
  onDecision?: () => void
}

// The server's own explanation lives in the response body (FastAPI puts it in
// `detail`). Without this the caller only ever sees the status code, which is
// how "you are out of Gemini quota" surfaced as "the backend did not answer".
async function apiError(res: Response): Promise<Error> {
  let detail = ""
  try {
    const body = await res.text()
    try {
      const parsed = JSON.parse(body)
      detail = typeof parsed?.detail === "string" ? parsed.detail : body
    } catch {
      detail = body
    }
  } catch {
    // body already consumed or unreadable — fall back to the status alone
  }
  detail = detail.trim()
  return new Error(detail ? `${res.status}: ${detail}` : `API error: ${res.status}`)
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    // headers last: spreading `options` after them let a caller-supplied `headers`
    // silently drop Content-Type (and now the identity header) instead of adding to it
    headers: { ...defaultHeaders(), ...options?.headers },
  })
  if (res.status === 401) handleSignedOut()
  if (!res.ok) throw await apiError(res)
  return res.json()
}

// ── auth ──────────────────────────────────────────────────────────

// Sent with the anonymous client key so the backend can attach the credentials
// to the account this browser has already been using — whatever was created
// before signing up stays with the person who created it.
export async function register(email: string, password: string): Promise<AuthUser> {
  const res = await apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    headers: { "X-User-Id": getClientKey() },
  })
  return saveSession(res)
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const res = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })
  return saveSession(res)
}

export async function fetchMe(): Promise<AuthUser> {
  return apiFetch<AuthUser>("/auth/me")
}

export async function streamChat(
  sessionId: string,
  { content, signal, onToken, onDecision }: StreamChatOptions,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: defaultHeaders(),
    body: JSON.stringify({ content }),
    signal,
  })

  if (res.status === 401) handleSignedOut()
  if (!res.ok) throw await apiError(res)
  if (!res.body) throw new Error("Chat stream is unavailable")

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })

    const events = buffer.split("\n\n")
    buffer = events.pop() ?? ""

    for (const event of events) {
      for (const line of event.split("\n")) {
        if (!line.startsWith("data: ")) continue
        const payload = line.slice(6)
        if (payload === "[DONE]") return

        try {
          const parsed = JSON.parse(payload) as { content?: string; decision?: boolean }
          if (parsed.content) onToken(parsed.content)
          else if (parsed.decision) onDecision?.()
        } catch {
          onToken(payload)
        }
      }
    }

    if (done) break
  }
}
