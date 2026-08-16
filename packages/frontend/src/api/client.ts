const BASE_URL = "http://localhost:8000/api/v1"

const CLIENT_KEY_STORAGE = "zero-to-one:client-key"

// Who the backend thinks we are. Generated here and kept in localStorage — not
// sessionStorage — so it survives closing the tab; a new key would look like a
// brand new person with no projects. This identifies, it does not authenticate:
// anyone can send someone else's key, which is why it is not protecting anything
// that actually needs protecting.
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

function defaultHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-User-Id": getClientKey(),
  }
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
    // silently drop Content-Type (and now X-User-Id) instead of adding to it
    headers: { ...defaultHeaders(), ...options?.headers },
  })
  if (!res.ok) throw await apiError(res)
  return res.json()
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