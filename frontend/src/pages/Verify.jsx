import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Check, ArrowRight, ShieldCheck } from "lucide-react";
import { api, post } from "../services/api";
import {
  Badge,
  ErrorBox,
  Loading,
  MedicalCard,
  Source,
  OriginalPreview,
  ProcessingNotice,
} from "../components/UI";
import { Localized, useLocale } from "../i18n";

export default function Verify({ rememberPlan }) {
  const { language } = useLocale();
  const { id } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [decisions, setDecisions] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api(`/documents/${id}`)
      .then(setDoc)
      .catch((e) => setError(e.message));
  }, [id]);
  function chooseDecision(itemId, decision) {
    setDecisions(current => ({ ...current, [itemId]: decision }));
    setError("");
  }
  async function save() {
    const remaining = doc.analysis.items.length - Object.keys(decisions).length;
    if (remaining > 0) {
      setError(`Review each item first. ${remaining} ${remaining === 1 ? "decision is" : "decisions are"} still needed.`);
      return;
    }
    setBusy(true);
    setError("");
    try {
      const r = await post(`/documents/${id}/verify`, { decisions });
      rememberPlan(r.plan_id);
      navigate(`/recovery/${r.plan_id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  if (!doc) return <Localized language={language}>{error ? <ErrorBox message={error} /> : <Loading />}</Localized>;
  return (
    <Localized language={language}>
    <>
      <div className="page-intro">
        <div>
          <span className="eyebrow">STEP 03 · REVIEW TOGETHER</span>
          <h1>Your care deserves a second look.</h1>
          <p>
            Compare each item with the original. Ask your healthcare
            professional about anything unclear.
          </p>
        </div>
        <Badge>
          {Object.keys(decisions).length} / {doc.analysis.items.length} reviewed
        </Badge>
      </div>
      <div className="review-notice">
        <ShieldCheck />
        <p>
          <b>Patient Reviewed, never Clinically Verified.</b> Your confirmation
          records that you checked the text. Incomplete or uncertain
          instructions cannot become actionable reminders.
        </p>
      </div>
      <ProcessingNotice doc={doc} />
      <div className="comparison-layout">
        <OriginalPreview doc={doc} />
        <div className="medical-grid">
          {doc.analysis.items.map((item) => (
            <MedicalCard item={item} key={item.id}>
              <div className="review-actions">
                <button
                  disabled={
                    item.uncertain ||
                    item.professional_verification_required ||
                    busy
                  }
                  aria-pressed={decisions[item.id] === "reviewed"}
                  className={`button small ${decisions[item.id] === "reviewed" ? "" : "secondary"}`}
                  onClick={() => chooseDecision(item.id, "reviewed")}
                >
                  <Check size={16} /> Patient Reviewed
                </button>
                <button
                  disabled={busy}
                  aria-pressed={decisions[item.id] === "clarify"}
                  className={`button small ${decisions[item.id] === "clarify" ? "amber" : "secondary"}`}
                  onClick={() => chooseDecision(item.id, "clarify")}
                >
                  Needs clarification
                </button>
              </div>
              {item.uncertain && (
                <p className="fine">
                  This item must be clarified by a healthcare professional.
                </p>
              )}
            </MedicalCard>
          ))}
        </div>
      </div>
      <ErrorBox message={error} />
      <div className="action-bar">
        <Link className="text-link" to={`/analysis/${id}`}>
          ← Back to explanation
        </Link>
        <button
          className="button"
          disabled={busy}
          onClick={save}
        >
          {busy ? "Saving your review…" : "Create my recovery plan"}
          <ArrowRight size={18} />
        </button>
      </div>
      {Object.keys(decisions).length < doc.analysis.items.length && (
        <p className="review-progress-help" role="status">
          Choose <b>Patient Reviewed</b> or <b>Needs clarification</b> for every item before continuing.
          {doc.analysis.items.length - Object.keys(decisions).length} {doc.analysis.items.length - Object.keys(decisions).length === 1 ? "item remains" : "items remain"}.
        </p>
      )}
    </>
    </Localized>
  );
}
