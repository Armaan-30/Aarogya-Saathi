import { useEffect, useState } from "react";
import { HeartHandshake, UserPlus, ShieldCheck, Copy, Check, Clock, Circle } from "lucide-react";
import { api, post } from "../services/api";
import { ErrorBox, Loading } from "../components/UI";
import { Localized, useLocale } from "../i18n";

export default function Caregivers() {
  const { language } = useLocale();
  const [relations, setRelations] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [email, setEmail] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [createdInvite, setCreatedInvite] = useState(null);
  const [canComplete, setCanComplete] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function refresh() {
    const [nextRelations, nextDashboard] = await Promise.all([api("/caregivers"), api("/caregivers/dashboard")]);
    setRelations(nextRelations); setDashboard(nextDashboard);
  }
  useEffect(() => { refresh().catch(e => setError(e.message)); }, []);

  async function invite(event) {
    event.preventDefault(); setBusy(true); setError(""); setMessage(""); setCreatedInvite(null);
    try { setCreatedInvite(await post("/caregivers/invite", { email, can_complete_tasks: canComplete })); setEmail(""); await refresh(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function revoke(id) {
    setBusy(true); setError("");
    try { await api(`/caregivers/${id}`, { method: "DELETE" }); setCreatedInvite(null); setMessage("Caregiver access revoked."); await refresh(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function accept(event) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try { await post("/caregivers/accept", { invite_code: inviteCode.trim() }); setInviteCode(""); setMessage("Caregiver access is active. The patient can revoke it at any time."); await refresh(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function toggle(planId, task) {
    setBusy(true); setError("");
    try { await api(`/care-plans/${planId}/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ completed: !task.completed }) }); await refresh(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  if (!relations || !dashboard) return <Localized language={language}><>{error ? <ErrorBox message={error} /> : <Loading text="Opening caregiver access…" />}</></Localized>;
  return <Localized language={language}>
    <>
      <div className="page-intro"><div><span className="eyebrow">TRUSTED SUPPORT · PERMISSION BASED</span><h1>Care, together.</h1><p>Only records shared by a patient appear here. Patients can revoke access at any time.</p></div><HeartHandshake size={30} /></div>
      <div className="caregiver-layout">
        <section className="caregiver-column">
          <article className="card caregiver-panel">
            <div className="caregiver-heading"><UserPlus /><div><h2>Invite a caregiver</h2><p>Invite someone you trust by their registered email. No email is sent by this prototype.</p></div></div>
            <form className="caregiver-form" onSubmit={invite}>
              <label>Caregiver email<input type="email" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} /></label>
              <label className="caregiver-check"><input type="checkbox" checked={canComplete} onChange={e => setCanComplete(e.target.checked)} />Allow them to mark checklist tasks complete</label>
              <button className="button" disabled={busy || !email.trim()}>Create invitation code</button>
            </form>
            {createdInvite && <div className="invite-code-box" role="status"><strong>Share this one-time code privately</strong><code>{createdInvite.invite_code}</code><p>It expires {new Date(createdInvite.expires_at).toLocaleString()}. The caregiver must register or sign in using {createdInvite.email} and accept this code.</p><button className="button small secondary" onClick={() => navigator.clipboard?.writeText(createdInvite.invite_code)}><Copy size={15} /> Copy invite code</button></div>}
            <h3 className="caregiver-subheading">Caregivers you invited</h3>
            {!relations.caregivers.length && <p className="fine">No caregiver access has been shared.</p>}
            {relations.caregivers.map(grant => <div className="caregiver-relation" key={grant.id}><div><b>{grant.email}</b><span className={`access-pill ${grant.status}`}>{grant.status}</span><small>{grant.can_complete_tasks ? "Can complete tasks" : "View only"}</small></div>{grant.status !== "revoked" && <button className="button small secondary" disabled={busy} onClick={() => revoke(grant.id)}>Revoke access</button>}</div>)}
          </article>
          <article className="card caregiver-panel">
            <div className="caregiver-heading"><ShieldCheck /><div><h2>Accept a patient invitation</h2><p>Enter the private code the patient shared with you. It must match your sign-in email.</p></div></div>
            <form className="caregiver-form" onSubmit={accept}><label>Invitation code<input required minLength={20} value={inviteCode} onChange={e => setInviteCode(e.target.value)} /></label><button className="button secondary" disabled={busy || !inviteCode.trim()}>Accept caregiver access</button></form>
          </article>
        </section>
        <section className="caregiver-column">
          <div className="section-heading"><div><span className="eyebrow">SHARED WITH ME</span><h2>Caregiver dashboard</h2></div></div>
          {!dashboard.patients.length && <div className="card empty"><HeartHandshake size={34} /><h3>No patient has shared a care plan yet</h3><p>Accept an invitation to see the patient's reviewed tasks and follow-ups.</p></div>}
          {dashboard.patients.map(patient => <article className="card caregiver-patient" key={patient.patient_email}><h3>{patient.patient_email}</h3><p className="fine">Shared patient account · {patient.can_complete_tasks ? "task updates allowed" : "view-only access"}</p>
            {!patient.plans.length && <p className="fine">No reviewed recovery plans are available yet.</p>}
            {patient.plans.map(plan => <div className="caregiver-plan" key={plan.id}><h4>{plan.document.filename}</h4><p className="fine">Patient Reviewed · review the original instructions before helping.</p>
              {plan.tasks.map(task => <div className="caregiver-task" key={task.id}><span>{task.completed ? <Check size={17} /> : <Circle size={17} />}</span><div><b>{task.item.title}</b><p>{task.item.wording}</p>{task.reminder?.state !== "unscheduled" && <small><Clock size={13} /> {task.reminder.state.replace("_", " ")}{task.reminder.scheduled_for ? ` · ${new Date(task.reminder.scheduled_for).toLocaleString()}` : ""}</small>}</div>{patient.can_complete_tasks && <button className="button small secondary" disabled={busy} onClick={() => toggle(plan.id, task)}>{task.completed ? "Reopen" : "Complete"}</button>}</div>)}
              {!!plan.clarifications.length && <div className="clarification-card"><b>{plan.clarifications.length} items need professional clarification</b>{plan.clarifications.map(item => <p key={item.id}>{item.title}: {item.concerns.join(" ")}</p>)}</div>}
            </div>)}
          </article>)}
        </section>
      </div>
      {message && <p className="success-note" role="status">{message}</p>}
      <ErrorBox message={error} />
      <p className="fine caregiver-disclaimer">Caregiver access is limited to the records of the patient who invited this account. Do not share invitation codes in public messages.</p>
    </>
  </Localized>;
}
