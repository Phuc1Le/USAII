import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { FormEvent } from "react"
import ReactMarkdown from "react-markdown"
import type { ChatMessage, ChatSession, OpenSessionRequest, Step, Task } from "../../../api"
import { apiFetch, streamChat } from "../../../api/client"

type Props = {
  projectId: string
  step: Step
  tasks: Task[]
  onClose: () => void
}

const seededSessionIds = new Set<string>()

function buildSeedMessage(step: Step, tasks: Task[]): string {
  const taskLines = tasks.length > 0
    ? tasks.map((task) => `- ${task.title}${task.detail ? `: ${task.detail}` : ""}`).join("\n")
    : "- No tasks loaded yet."

  return [
    "Apply this step to chat and help me move it forward.",
    "",
    `Step: ${step.title}`,
    `Description: ${step.description}`,
    "",
    "Tasks:",
    taskLines,
  ].join("\n")
}

export default function ChatPanel({ projectId, step, tasks, onClose }: Props) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const seedMessage = useMemo(() => buildSeedMessage(step, tasks), [step, tasks])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const appendAssistantToken = useCallback((token: string) => {
    setMessages((prev) => {
      const next = [...prev]
      const last = next[next.length - 1]
      if (last?.role === "assistant") {
        next[next.length - 1] = { ...last, content: last.content + token }
      } else {
        next.push({ role: "assistant", content: token })
      }
      return next
    })
  }, [])

  const sendToChat = useCallback(async (id: string, content: string, showUserMessage = true) => {
    const trimmed = content.trim()
    if (!trimmed) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setError(null)
    setIsStreaming(true)

    if (showUserMessage) {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: trimmed },
        { role: "assistant", content: "" },
      ])
    } else {
      setMessages((prev) => [...prev, { role: "assistant", content: "" }])
    }

    try {
      await streamChat(id, {
        content: trimmed,
        signal: controller.signal,
        onToken: appendAssistantToken,
      })
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : "Chat request failed")
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsStreaming(false)
      }
    }
  }, [appendAssistantToken])

  useEffect(() => {
    let isActive = true

    async function openChat() {
      setIsLoading(true)
      setError(null)

      try {
        const body: OpenSessionRequest = {
          project_id: projectId,
          scope_type: "step",
          scope_step_id: step.id,
        }
        const session = await apiFetch<ChatSession>("/chat/sessions", {
          method: "POST",
          body: JSON.stringify(body),
        })

        if (!isActive) return

        setSessionId(session.id)
        setMessages(session.messages)

        if (session.messages.length === 0 && !seededSessionIds.has(session.id)) {
          seededSessionIds.add(session.id)
          await sendToChat(session.id, seedMessage)
        }
      } catch (err) {
        if (isActive) {
          setError(err instanceof Error ? err.message : "Unable to open chat")
        }
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void openChat()

    return () => {
      isActive = false
      abortRef.current?.abort()
    }
  }, [projectId, seedMessage, sendToChat, step.id])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!sessionId || isStreaming) return

    const content = input
    setInput("")
    await sendToChat(sessionId, content)
  }

  return (
    <section className="db-chat-panel" aria-label={`Chat for ${step.title}`}>
      <div className="db-chat-header">
        <div>
          <p className="db-chat-eyebrow">Step chat</p>
          <h3 className="db-chat-title">{step.title}</h3>
        </div>
        <button className="db-detail-btn" onClick={onClose} type="button">
          Close
        </button>
      </div>

      <div className="db-chat-messages">
        {isLoading && messages.length === 0 ? (
          <p className="db-chat-muted">Opening chat...</p>
        ) : (
          messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`db-chat-message ${message.role}`}>
              <span className="db-chat-role">{message.role === "user" ? "You" : "Agent"}</span>
              {message.role === "assistant" ? (
                message.content
                  ? <div className="db-chat-markdown"><ReactMarkdown>{message.content}</ReactMarkdown></div>
                  : isStreaming && index === messages.length - 1
                    ? <p className="db-chat-muted">Thinking...</p>
                    : null
              ) : (
                <p>{message.content}</p>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="db-chat-error">{error}</p>}

      <form className="db-chat-form" onSubmit={handleSubmit}>
        <input
          className="db-chat-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask a follow-up..."
          disabled={!sessionId || isStreaming}
        />
        <button className="primary-button" type="submit" disabled={!sessionId || isStreaming || !input.trim()}>
          {isStreaming ? "Sending..." : "Send"}
        </button>
      </form>
    </section>
  )
}
