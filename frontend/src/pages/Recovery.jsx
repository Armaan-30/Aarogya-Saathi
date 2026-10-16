import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Check,
  Circle,
  ArrowUpRight,
  HeartHandshake,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { api } from "../services/api";
import {
  Badge,
  ErrorBox,
  Loading,
  Explanation,
  kindIcons,
} from "../components/UI";
import { Localized, useLocale } from "../i18n";

export default function Recovery({ notify }) {
  const { language } = useLocale();
  const { id } = useParams();
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  useEffect(() => {
    api(`/care-plans/${id}`)
      .then(setPlan)
      .catch((e) => setError(e.message));
  }, [id]);
  async function toggle(task) {
    setPending(task.id);
    try {
      const r = await api(`/care-plans/${id}/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({ completed: !task.completed }),
      });
      setPlan((p) => ({
        ...p,
        tasks: p.tasks.map((t) =>
          t.id === task.id ? { ...t, completed: r.completed } : t,
        ),
      }));
      notify(
        r.completed
          ? "Checklist item marked complete."
          : "Checklist item reopened.",
      );
    } catch (e) {
      notify(e.message);
    } finally {
      setPending("");
    }
  }
  if (error) return <Localized language={language}><ErrorBox message={error} /></Localized>;
  if (!plan) return <Localized language={language}><Loading text="Opening your recovery space…" /></Localized>;
  const completed = plan.tasks.filter((t) => t.completed).length;
  const reminders = plan.tasks.filter((task) => task.reminder && task.reminder.state !== "unscheduled");
  return (
    <Localized language={language}>
    <>
      <div className="page-intro">
        <div>
          <span className="eyebrow">YOUR RECOVERY · ONE STEP AT A TIME</span>
          <h1>Small steps. A clearer way forward.</h1>
          <p>Your reviewed instructions, together in one calm space.</p>
        </div>
        <Badge>Patient Reviewed</Badge>
      </div>
      <div className="recovery-banner">
        <div className="icon-box">
          <HeartHandshake size={30} />
        </div>
        <div>
          <h2>Your checklist is ready.</h2>
          <p>
            {completed} of {plan.tasks.length} items marked complete · This
            tracks tasks, not health or recovery progress.
          </p>
        </div>
        <div
          className="progress-track"
          aria-label={`${completed} of ${plan.tasks.length} tasks complete`}
        >
          <span
            style={{
              width: `${plan.tasks.length ? (completed / plan.tasks.length) * 100 : 0}%`,
            }}
          />
        </div>
      </div>
      <Badge warning={plan.document.mode === "demo"}>
        {plan.document.mode === "demo"
          ? "Demo Mode — Prerecorded AI Results"
          : "Live Gemini analysis · Patient Reviewed"}
      </Badge>
      <div className="reminder-summary" aria-label="Upcoming recovery reminders">
        {!reminders.length && <article className="card reminder-card"><h3>No dated reminders</h3><p>Tasks without an explicit date and time stay on the checklist. No schedule is inferred.</p></article>}
        {reminders.map(task => <article className={`card reminder-card ${task.reminder.state}`} key={task.id}>
          <h3>{task.item.title}</h3><p>{task.item.wording}</p>
          <span className={`reminder-state ${task.reminder.state}`}>{task.reminder.state.replace("_", " ")}</span>
          {task.reminder.scheduled_for && <p>{new Date(task.reminder.scheduled_for).toLocaleString()}</p>}
        </article>)}
      </div>
      <div className="recovery-grid">
        <section>
          <div className="section-heading">
            <h2>Your care checklist</h2>
            <span className="fine">Saved automatically</span>
          </div>
          <p className="fine">
            One-time checklist for this document. No recurring alarms or push
            notifications. Medicine timing is shown only when explicitly
            written.
          </p>
          {!plan.tasks.length && (
            <div className="card">
              <h3>Clarification comes first.</h3>
              <p>
                No instructions were cleared for your checklist. Review the open
                questions with your healthcare professional.
              </p>
            </div>
          )}
          {plan.tasks.map((task) => {
            const Icon = kindIcons[task.item.kind];
            return (
              <article
                className={`card care-task ${task.completed ? "completed" : ""}`}
                key={task.id}
              >
                <button
                  aria-label={`${task.completed ? "Reopen" : "Complete"} ${task.item.title}`}
                  aria-pressed={task.completed}
                  disabled={!!pending}
                  className="task-check"
                  onClick={() => toggle(task)}
                >
                  {task.completed ? <Check size={18} /> : <Circle size={21} />}
                </button>
                <div>
                  <div className="task-kind">
                    <Icon size={14} />
                    {(task.item.category || task.item.kind).replace("_", " ")}
                  </div>
                  <h3>{task.item.title}</h3>
                  <p>{task.item.wording}</p>
                  {task.item.timing ? (
                    <span className="time">
                      <Clock size={13} /> As written: {task.item.timing}
                    </span>
                  ) : (
                    task.item.kind === "medicine" && (
                      <span className="fine">
                        Clock time not specified. Ask your professional.
                      </span>
                    )
                  )}
                  <details>
                    <summary>Source evidence</summary>
                    <blockquote>{task.item.source}</blockquote>
                  </details>
                </div>
              </article>
            );
          })}
        </section>
        <aside>
          <div className="section-heading">
            <h2>Keep in mind</h2>
          </div>
          {plan.warnings.map((i) => (
            <div className="card warning-card" key={i.id}>
              <AlertTriangle size={21} />
              <h3>{i.title}</h3>
              <p>{i.wording}</p>
            </div>
          ))}
          <div className="card clarification-card">
            <Badge warning={plan.clarifications.length > 0}>
              {plan.clarifications.length} open questions
            </Badge>
            <h3>Bring clarity to your next visit.</h3>
            {plan.clarifications.length ? (
              plan.clarifications.map((i) => (
                <div className="clarification" key={i.id}>
                  <strong>{i.title}</strong>
                  <p>
                    {i.concerns.join(" ") ||
                      "You marked this item for professional clarification."}
                  </p>
                  <blockquote>{i.source}</blockquote>
                </div>
              ))
            ) : (
              <p>
                You have no items marked for clarification. Contact your
                professional if any instruction becomes unclear.
              </p>
            )}
          </div>
          <Link
            className="button secondary full"
            to={`/analysis/${plan.document.id}`}
          >
            View original analysis <ArrowUpRight size={17} />
          </Link>
        </aside>
      </div>
      <Explanation doc={plan.document} notify={notify} />
    </>
    </Localized>
  );
}
