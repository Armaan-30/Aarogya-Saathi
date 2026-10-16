import { useEffect, useState } from "react";
import { Link, useParams, useLocation } from "react-router-dom";
import { ArrowRight, MessageCircle, ShieldCheck } from "lucide-react";
import { api } from "../services/api";
import {
  Badge,
  ErrorBox,
  Loading,
  MedicalCard,
  Source,
  Explanation,
  OriginalPreview,
  ProcessingNotice,
} from "../components/UI";
import { Localized, useLocale } from "../i18n";

export default function Analysis({ notify }) {
  const { language } = useLocale();
  const { id } = useParams();
  const location = useLocation();
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setDoc(null);
    api(`/documents/${id}`)
      .then(setDoc)
      .catch((e) => setError(e.message));
  }, [id]);
  if (error) return <Localized language={language}><ErrorBox message={error} /></Localized>;
  if (!doc) return <Localized language={language}><Loading /></Localized>;
  return (
    <Localized language={language}>
    <>
      <div className="page-intro">
        <div>
          <span className="eyebrow">STEP 02 · UNDERSTAND</span>
          <h1>Let’s make sense of your document.</h1>
          <p>
            {doc.filename} · {doc.analysis.document_type}
          </p>
        </div>
        <Badge warning={doc.mode === "demo"}>
          {doc.mode === "demo"
            ? "Demo Mode — Prerecorded AI Results"
            : "Live Gemini AI · Unreviewed"}
        </Badge>
      </div>
      <ProcessingNotice doc={doc} reused={location.state?.reused} />
      <div className="comparison-layout">
        <OriginalPreview doc={doc} />
        <div className="interpretation-column">
          <Explanation doc={doc} notify={notify} />
          <div className="review-notice">
            <ShieldCheck />
            <p>
              <b>Clarity starts with a careful review.</b> These are extracted
              instructions, not new medical advice. Check every item against
              your original document.
            </p>
          </div>
          {doc.analysis.uncertainties.map((w, i) => (
            <ErrorBox message={w} key={i} />
          ))}
          <div className="section-heading">
            <h2>What your document says</h2>
            <span className="fine">
              {doc.analysis.items.length} items to review
            </span>
          </div>
          <div className="medical-grid">
            {doc.analysis.items.map((item) => (
              <MedicalCard item={item} key={item.id} />
            ))}
          </div>
          {!doc.analysis.items.length && (
            <div className="card">
              <h3>No actionable instructions extracted</h3>
              <p>
                Use a clearer document or ask the prescribing professional to
                clarify the unreadable information.
              </p>
            </div>
          )}
        </div>
      </div>
      <div className="action-bar">
        <p>Next: check the details and mark anything unclear.</p>
        <Link className="button secondary" to={`/chat/${id}`}>
          Ask about this document <MessageCircle size={17} />
        </Link>
        <Link className="button" to={`/verify/${id}`}>
          Review my information <ArrowRight size={18} />
        </Link>
      </div>
    </>
    </Localized>
  );
}
