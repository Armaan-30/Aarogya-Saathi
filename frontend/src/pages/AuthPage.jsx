import { useState } from "react";
import { HeartPulse, LockKeyhole, Moon, Sun } from "lucide-react";
import { post } from "../services/api";

export default function AuthPage({ setupRequired, onAuthenticated, theme, toggleTheme }) {
  const [mode, setMode] = useState(setupRequired ? "register" : "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const user = mode === "register"
        ? await post("/auth/register", { email, password, ...(inviteCode.trim() ? { invite_code: inviteCode.trim() } : {}) })
        : await post("/auth/login", { email, password });
      onAuthenticated(user);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <main className="auth-shell">
    <section className="auth-card card">
      <div className="auth-brand"><span className="brand-mark"><HeartPulse /></span><div><b>AarogyaSaathi</b><small>YOUR RECOVERY COMPANION</small></div><button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"} title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}>{theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}</button></div>
      <span className="eyebrow">PRIVATE CARE SPACE</span>
      <h1>{mode === "register" ? "Create your account" : "Welcome back"}</h1>
      <p>Sign in to access your medical documents and recovery checklist. Records are private to your account unless you invite a caregiver.</p>
      <form onSubmit={submit} className="auth-form">
        <label>Email address<input type="email" autoComplete="email" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} required minLength={mode === "register" ? 12 : 1} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} />{mode === "register" && <small>Use at least 12 characters.</small>}</label>
        {mode === "register" && <label>Caregiver invitation code <span className="fine">(optional)</span><input autoComplete="off" value={inviteCode} onChange={e => setInviteCode(e.target.value)} /><small>Enter a code if a patient invited you. The invitation must match this email.</small></label>}
        {error && <div className="auth-error" role="alert">{error}</div>}
        <button className="button full" disabled={busy}>{busy ? "Please wait…" : mode === "register" ? "Create private account" : "Sign in securely"}</button>
      </form>
      {!setupRequired && <button className="text-link auth-switch" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>{mode === "login" ? "Create an account" : "Already have an account? Sign in"}</button>}
      <p className="fine auth-notice"><LockKeyhole size={14} /> Local prototype: keep it on a trusted network, use a unique password, and test only with synthetic or non-identifiable documents.</p>
    </section>
  </main>;
}
