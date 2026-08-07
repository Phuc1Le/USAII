const BASE_URL = "http://localhost:8000/api/v1"

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
    headers: { "Content-Type": "application/json" },
    ...options,
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
    headers: { "Content-Type": "application/json" },
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