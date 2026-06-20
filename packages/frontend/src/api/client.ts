const BASE_URL = "http://localhost:8000/api/v1"

type StreamChatOptions = {
  content: string
  signal?: AbortSignal
  onToken: (token: string) => void
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function streamChat(
  sessionId: string,
  { content, signal, onToken }: StreamChatOptions,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  })

  if (!res.ok) throw new Error(`API error: ${res.status}`)
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
          const parsed = JSON.parse(payload) as { content?: string }
          if (parsed.content) onToken(parsed.content)
        } catch {
          onToken(payload)
        }
      }
    }

    if (done) break
  }
}