import { useState } from "react"
import type { FormEvent } from "react"
import { filterOptions } from "../utils"

type ChoicePanelProps = {
  eyebrow: string
  title: string
  value: string
  options: string[]
  placeholder: string
  submitLabel: string
  onBack: () => void
  onSubmit: (value: string) => void
}

export default function ChoicePanel({
  eyebrow,
  title,
  value,
  options,
  placeholder,
  submitLabel,
  onBack,
  onSubmit,
}: ChoicePanelProps) {
  const [input, setInput] = useState(value)
  const filteredOptions = filterOptions(options, input)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit(input)
  }

  return (
    <form className="form-panel choice-panel" onSubmit={handleSubmit}>
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
      </div>
      <div className="combo-wrap">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={placeholder}
          autoFocus
        />
        <div className="dropdown-list">
          {(filteredOptions.length > 0 ? filteredOptions : [input]).filter(Boolean).map((option) => (
            <button type="button" key={option} onClick={() => setInput(option)}>
              {option}
            </button>
          ))}
        </div>
      </div>
      <div className="panel-actions">
        <button type="button" className="secondary-button" onClick={onBack}>
          Back
        </button>
        <button type="submit" className="primary-button" disabled={!input.trim()}>
          {submitLabel}
        </button>
      </div>
    </form>
  )
}
