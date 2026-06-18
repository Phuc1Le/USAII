type ThinkingPanelProps = {
  eyebrow?: string
  title?: string
  message?: string
}

export default function ThinkingPanel({
  eyebrow = "Assessing clarity",
  title = "Thinking...",
  message = "Checking the problem, audience, scope, core feature, and definition of done.",
}: ThinkingPanelProps) {
  return (
    <div className="thinking-panel" role="status" aria-live="polite">
      <div className="thinking-orbit">
        <span />
        <span />
        <span />
      </div>
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{message}</p>
      </div>
    </div>
  )
}
