import {
  AlertTriangle,
  Check,
  FileText,
  Pill,
  CalendarDays,
  ShieldCheck,
  Volume2,
  Square,
  LoaderCircle,
  ArrowUpRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { post } from "../services/api";
import { Localized, translate, useLocale } from "../i18n";

export function Badge({ children, warning = false }) {
  const { language } = useLocale();
  return (
    <Localized language={language}>
    <span className={`badge ${warning ? "warning" : ""}`}>{children}</span>
    </Localized>
  );
}
export function ErrorBox({ message }) {
  const { language } = useLocale();
  return message ? (
    <Localized language={language}>
    <div className="error" role="alert">
      <AlertTriangle size={19} />
      <span>{message}</span>
    </div>
    </Localized>
  ) : null;
}
export function Loading({ text = "Opening your document…" }) {
  const { language } = useLocale();
  return (
    <Localized language={language}>
    <div className="loading" role="status">
      <LoaderCircle className="spin" />
      <h3>{text}</h3>
      <p>Please keep this page open.</p>
      <div className="skeleton" />
      <div className="skeleton short" />
    </div>
    </Localized>
  );
}
export const kindIcons = {
  medicine: Pill,
  instruction: ShieldCheck,
  follow_up: CalendarDays,
  warning: AlertTriangle,
};
export function MedicalCard({ item, children }) {
  const { language } = useLocale();
  const Icon = kindIcons[item.kind];
  return (
    <Localized language={language}>
    <article
      className={`card medical-card ${item.uncertain ? "needs-review" : ""}`}
    >
      <div className="card-top">
        <div className="icon-box">
          <Icon size={21} />
        </div>
        <Badge warning={item.uncertain}>
          {item.professional_verification_required
            ? "Needs Professional Verification"
            : item.uncertain
              ? "Needs clarification"
              : item.kind.replace("_", " ")}
        </Badge>
      </div>
      <h3>{item.kind === "medicine" ? <Link className="medicine-link" to={`/medicine?name=${encodeURIComponent(item.title)}`} title="View medicine information">{item.title}<ArrowUpRight size={16} aria-hidden="true" /></Link> : item.title}</h3>
      <p className="wording">{item.wording}</p>
      {item.kind === "medicine" && (
        <dl className="medicine-facts">
          {[
            ["Dose", item.dosage],
            ["Frequency", item.frequency],
            ["Duration", item.duration],
            ["Timing", item.timing],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value || "Not documented"}</dd>
            </div>
          ))}
        </dl>
      )}
      {item.kind === "medicine" && !item.timing && (
        <p className="fine">
          No clock-time reminder: ask your professional to clarify timing.
        </p>
      )}
      <details>
        <summary>View source evidence</summary>
        <blockquote>{item.source}</blockquote>
      </details>
      {item.concerns?.length > 0 && (
        <ul className="concerns">
          {item.concerns.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      )}
      {children}
    </article>
    </Localized>
  );
}
export function Source({ doc }) {
  const { language } = useLocale();
  return (
    <Localized language={language}>
    <details className="card source">
      <summary>
        <FileText size={20} /> Original extracted document{" "}
        <span>{doc.extraction}</span>
      </summary>
      <p className="fine">
        Compare against the original file. OCR may misread characters.
      </p>
      <pre>{doc.extracted_text}</pre>
      <a
        className="text-link"
        href={`/api/documents/${doc.id}/file`}
        target="_blank"
        rel="noreferrer"
      >
        Open original document ↗
      </a>
    </details>
    </Localized>
  );
}
export function OriginalPreview({ doc }) {
  const { language } = useLocale();
  const url = `/api/documents/${doc.id}/file`;
  const isPDF = doc.filename.toLowerCase().endsWith(".pdf");
  return (
    <Localized language={language}>
    <aside className="original-column">
      <section className="card original-preview">
        <div className="section-heading">
          <h2>Original document</h2>
          <FileText size={20} />
        </div>
        <p className="fine">Compare the image with every extracted field.</p>
        {isPDF ? (
          <iframe src={url} title="Original document preview" />
        ) : (
          <img src={url} alt="Original prescription for comparison" />
        )}
        <a className="text-link" href={url} target="_blank" rel="noreferrer">
          Open full-size original ↗
        </a>
      </section>
      <Source doc={doc} />
    </aside>
    </Localized>
  );
}
export function ProcessingNotice({ doc, reused = false }) {
  const { language } = useLocale();
  const p = doc.processing;
  return (
    <Localized language={language}>
    <section
      className="processing-notice"
      aria-label="Document processing details"
    >
      <div className="processing-badges">
        {(p?.methods?.length ? p.methods : [doc.extraction]).map((m) => (
          <Badge key={m}>{m}</Badge>
        ))}
        {reused && (
          <Badge>Saved live result reused · no new analysis call</Badge>
        )}
      </div>
      <p>
        {p?.provenance ||
          "Compare extracted text against the original document."}
      </p>
      {!!p?.warnings?.length && (
        <div className="processing-warnings" role="alert" aria-label="Document reading warnings">
          <strong>Check these reading warnings against the original:</strong>
          <ul>{p.warnings.map((warning, i) => <li key={`${i}-${warning}`}>{warning}</li>)}</ul>
        </div>
      )}
      {p?.document_mode === "handwritten" && (
        <p className="fine">
          {doc.mode === "demo"
            ? "Prerecorded transcription. No live image-capability claim."
            : p.image_input_verified
              ? `Image input succeeded with ${p.vision_model}. This does not verify transcription accuracy.`
              : "Image support has not been verified."}
        </p>
      )}
      {!!p?.unreadable_regions?.length && (
        <ul>
          {p.unreadable_regions.map((r, i) => (
            <li key={i}>Unreadable: {r}</li>
          ))}
        </ul>
      )}
      {!!p?.preprocessing?.length && (
        <details>
          <summary>Image preparation details</summary>
          <ul>
            {p.preprocessing.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
    </Localized>
  );
}
export function Explanation({ doc, notify }) {
  const { language: appLanguage } = useLocale();
  const [language, setLanguage] = useState("en");
  const [text, setText] = useState(doc.analysis.summary);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const [speechBusy, setSpeechBusy] = useState(false);
  const audioRef = useRef(null);
  const audioContextRef = useRef(null);
  useEffect(() => () => {
    window.speechSynthesis?.cancel();
    try { audioRef.current?.stop(); } catch {}
    audioContextRef.current?.close();
  }, []);
  async function changeLanguage(next) {
    window.speechSynthesis?.cancel();
    try { audioRef.current?.stop(); } catch {}
    audioRef.current = null;
    setPlaying(false);
    setVoiceMessage("");
    setBusy(true);
    setError("");
    try {
      const res = await post(`/documents/${doc.id}/translate`, {
        language: next,
      });
      setText(res.explanation);
      setLanguage(next);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function speak() {
    if (playing) {
      window.speechSynthesis?.cancel();
      try { audioRef.current?.stop(); } catch {}
      audioRef.current = null;
      setPlaying(false);
      return;
    }
    setVoiceMessage("");
    const voices = window.speechSynthesis?.getVoices?.() || [];
    window.speechSynthesis?.cancel();
    const voice = voices.find((v) => v.lang.toLowerCase() === `${language}-in`) ||
      voices.find((v) => v.lang.toLowerCase().startsWith(`${language}-`)) ||
      voices.find((v) => v.lang.toLowerCase() === language);
    if (!voice) {
      if (!["hi", "mr"].includes(language)) {
        setVoiceMessage("No voice is installed for this language. You can read the explanation below.");
        return;
      }
      setSpeechBusy(true);
      try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) throw new Error("Audio playback is unavailable in this browser.");
        const context = audioContextRef.current || new AudioContextClass();
        audioContextRef.current = context;
        await context.resume();
        const result = await post(`/documents/${doc.id}/speech`, { language, text });
        const bytes = Uint8Array.from(atob(result.audio_base64), c => c.charCodeAt(0));
        const audioBuffer = await context.decodeAudioData(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
        const source = context.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(context.destination);
        source.onended = () => { setPlaying(false); if (audioRef.current === source) audioRef.current = null; };
        audioRef.current = source;
        source.start();
        setVoiceMessage(translate("Audio is generated from the explanation using the configured Google AI service.", appLanguage));
        setPlaying(true);
      } catch (error) {
        const fallback = language === "hi" ? "हिंदी ऑडियो अभी उपलब्ध नहीं है। नीचे दिया पाठ पढ़ें।" : "मराठी ऑडिओ सध्या उपलब्ध नाही. खालील मजकूर वाचा.";
        setVoiceMessage(`${fallback} ${error.message}`);
      } finally {
        setSpeechBusy(false);
      }
      return;
    }
    setVoiceMessage("");
    if (!window.speechSynthesis) {
      setVoiceMessage(translate("Speech is unavailable in this browser. You can read the explanation below.", appLanguage));
      return;
    }
    const u = new SpeechSynthesisUtterance(text);
    u.voice = voice;
    u.lang = language === "hi" ? "hi-IN" : language === "mr" ? "mr-IN" : voice.lang;
    u.rate = 0.9;
    u.onend = () => setPlaying(false);
    u.onerror = () => {
      setPlaying(false);
      setVoiceMessage(translate("Voice playback was interrupted.", language));
    };
    setPlaying(true);
    window.speechSynthesis.speak(u);
  }
  useEffect(() => {
    window.speechSynthesis?.getVoices();
  }, []);
  return (
    <Localized language={appLanguage}>
    <section className="card explanation">
      <div className="section-heading">
        <div>
          <span className="eyebrow">A LITTLE CLARITY</span>
          <h2>Your document, in simpler words</h2>
        </div>
        <div className="language-controls">
          <select
            aria-label="Explanation language"
            value={language}
            disabled={busy}
            onChange={(e) => changeLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="mr">मराठी</option>
          </select>
          <button
            className="button small secondary"
            disabled={busy || speechBusy}
            onClick={speak}
          >
            {speechBusy ? <LoaderCircle size={16} className="spin" /> : playing ? <Square size={16} /> : <Volume2 size={16} />} {" "}
            {speechBusy ? "Preparing audio…" : playing ? "Stop" : "Listen"}
          </button>
        </div>
      </div>
      {voiceMessage && <p className="voice-status" role="status">{voiceMessage}</p>}
      <ErrorBox message={error} />
      {["hi", "mr"].includes(language) && <p className="fine voice-disclosure">If this device has no Hindi or Marathi voice, the translated explanation is sent to the configured Google AI speech service to make the audio. Internet access and available free-tier quota are required.</p>}
      <p className={busy ? "muted" : ""} lang={language}>
        {busy ? "Translating explanation…" : text}
      </p>
      <p className="fine">
        {doc.mode === "demo"
          ? "Prerecorded sample explanation."
          : "AI explanation — review for accuracy."}{" "}
        Medicine instructions remain in the original wording. Translations have
        not been clinically verified.
      </p>
    </section>
    </Localized>
  );
}
