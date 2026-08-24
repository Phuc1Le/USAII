import { useState } from "react"
import { useMutation } from "@tanstack/react-query"

import { login, register, type AuthUser } from "../../api/client"
import Starfield from "../intake/components/Starfield"
import "../intake/IntakeFlow.css"
import "./AuthPanel.css"

type AuthPanelProps = {
  onSignedIn: (user: AuthUser) => void
  onCancel: () => void
}

type Mode = "login" | "register"

// The backend deliberately answers "Incorrect email or password" for both a
// wrong password and an unknown email, so it cannot be used to discover which
// addresses have accounts. Pass those through untouched; only translate the
// ones the user can actually act on.
function errorText(error: unknown): string {
  const message = error instanceof Error && error.message ? error.message : ""
  if (!message) return "Something went wrong. Please try again."
  if (message.startsWith("409")) return "That email is already registered. Try signing in instead."
  if (message.startsWith("422")) return "Check the email format, and use at least 8 characters for the password."
  // strip the status code prefix apiError adds; the sentence after it is the real message
  return message.replace(/^\d{3}:\s*/, "")
}

export default function AuthPanel({ onSignedIn, onCancel }: AuthPanelProps) {
  const [mode, setMode] = useState<Mode>("register")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const authMutation = useMutation({
    mutationFn: async () => {
      const trimmed = email.trim()
      return mode === "register" ? register(trimmed, password) : login(trimmed, password)
    },
    onSuccess: onSignedIn,
  })

  function switchMode(next: Mode) {
    setMode(next)
    // a failure from the other mode describes a request the user is no longer
    // making — leaving it up would explain the wrong thing
    authMutation.reset()
  }

  const isRegister = mode === "register"
  const canSubmit = email.trim().length > 0 && password.length > 0 && !authMutation.isPending

  return (
    <main className="idea-shell">
      <Starfield />
      <section className="hero-stage">
        <form
          className="form-panel auth-panel"
          onSubmit={(event) => {
            event.preventDefault()
            if (canSubmit) authMutation.mutate()
          }}
        >
          <div>
            <span className="eyebrow">{isRegister ? "Create an account" : "Welcome back"}</span>
            <h1>{isRegister ? "Save your work" : "Sign in"}</h1>
          </div>

          {isRegister && (
            <p className="auth-note">
              The projects you have already made stay with you — signing up keeps this
              browser's work under your new account.
            </p>
          )}

          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              placeholder={isRegister ? "At least 8 characters" : ""}
            />
          </label>

          {authMutation.isError && <p className="error-text">{errorText(authMutation.error)}</p>}

          <div className="panel-actions">
            <button type="button" className="secondary-button" onClick={onCancel}>
              Back
            </button>
            <button type="submit" className="primary-button" disabled={!canSubmit}>
              {authMutation.isPending
                ? isRegister
                  ? "Creating..."
                  : "Signing in..."
                : isRegister
                  ? "Create account"
                  : "Sign in"}
            </button>
          </div>

          <button
            type="button"
            className="auth-switch"
            onClick={() => switchMode(isRegister ? "login" : "register")}
          >
            {isRegister ? "Already have an account? Sign in" : "No account yet? Create one"}
          </button>
        </form>
      </section>
    </main>
  )
}
