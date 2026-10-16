import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  UploadCloud,
  Camera,
  FileText,
  ArrowRight,
  ShieldCheck,
  X,
  Sparkles,
  LoaderCircle,
} from "lucide-react";
import { api, post } from "../services/api";
import { Badge, ErrorBox } from "../components/UI";
import { Localized, useLocale } from "../i18n";

export default function Upload({ health, rememberDoc }) {
  const { language } = useLocale();
  const [params] = useSearchParams();
  const [sample, setSample] = useState(params.get("sample") || "");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [mode, setMode] = useState("demo");
  const [documentMode, setDocumentMode] = useState("printed");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const input = useRef();
  const camera = useRef();
  const navigate = useNavigate();
  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  function choose(f) {
    setError("");
    if (!f) return;
    if (!["application/pdf", "image/png", "image/jpeg"].includes(f.type)) {
      setError("Please choose a PDF, PNG or JPEG file.");
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      setError("This file is too large. The maximum size is 5 MB.");
      return;
    }
    setFile(f);
    setSample("");
    setMode("live");
    if (f.type === "application/pdf") setDocumentMode("printed");
  }
  async function analyze() {
    setBusy(true);
    setError("");
    try {
      let doc;
      if (sample) {
        doc = await post(`/demo/cases/${sample}/analyze`, { mode });
      } else {
        const form = new FormData();
        form.append("file", file);
        form.append("document_mode", documentMode);
        doc = await api("/documents/analyze", { method: "POST", body: form });
      }
      rememberDoc(doc.id);
      navigate(`/analysis/${doc.id}`, { state: { reused: doc.reused } });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Localized language={language}>
    <>
      <div className="page-intro">
        <div>
          <span className="eyebrow">STEP 01 · UPLOAD</span>
          <h1>Let’s make your instructions easier to understand.</h1>
          <p>
            Upload a prescription, discharge summary, or care instruction sheet.
          </p>
        </div>
        <Badge>Up to 5 MB</Badge>
      </div>
      <div className="upload-layout upload-layout-single">
        <section className="card upload-panel">
          <div className="section-heading">
            <h2>Your medical document</h2>
            <FileText size={22} />
          </div>
          <p>PDFs and clear photos are supported. Handwritten prescriptions need extra professional review.</p>
          <div className="document-mode">
            <label htmlFor="document-mode">Document type</label>
            <select
              id="document-mode"
              value={
                sample
                  ? ["handwritten", "blurry"].includes(sample) ? "handwritten" : "printed"
                  : documentMode
              }
              disabled={busy || !!sample}
              onChange={(e) => setDocumentMode(e.target.value)}
            >
              <option value="printed">Printed document · PDF or image</option>
              <option
                value="handwritten"
                disabled={file?.type === "application/pdf"}
              >
                Handwritten prescription · Image
              </option>
            </select>
            <p className="fine">
              {(sample
                ? ["handwritten", "blurry"].includes(sample) ? "handwritten" : "printed"
                : documentMode) === "handwritten"
                ? "Vision reads only visible text. Handwritten medicine details require professional verification."
                : "Readable PDFs use embedded text. Scans and printed images use Tesseract OCR. Select handwriting mode yourself when needed."}
            </p>
          </div>
          <input
            ref={input}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            hidden
            onChange={(e) => choose(e.target.files[0])}
          />
          <input
            ref={camera}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => choose(e.target.files[0])}
          />
          <div
            className={`dropzone ${drag ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              if (!busy) choose(e.dataTransfer.files[0]);
            }}
          >
            <div className="upload-icon">
              <UploadCloud size={32} />
            </div>
            <h3>Drop your document here</h3>
            <p>PDF, PNG or JPG · Maximum 5 MB</p>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => input.current.click()}
            >
              Browse files <ArrowRight size={17} />
            </button>
            <button
              className="camera-button"
              disabled={busy}
              onClick={() => camera.current.click()}
            >
              <Camera size={16} /> Use your camera
            </button>
          </div>
          {file && (
            <div className="file-preview">
              <div>
                <FileText size={20} />
                <strong>{file.name}</strong>
                <small>{(file.size / 1024).toFixed(0)} KB</small>
                <button
                  aria-label="Remove file"
                  onClick={() => setFile(null)}
                  disabled={busy}
                >
                  <X size={18} />
                </button>
              </div>
              {file.type === "application/pdf" ? (
                <iframe title="Selected PDF preview" src={preview} />
              ) : (
                <img src={preview} alt="Selected medical document preview" />
              )}
            </div>
          )}
          <div className="privacy-note">
            <ShieldCheck size={20} />
            <p>
              <b>Made for demonstration.</b> Use fictional documents only. Live
              mode sends extracted text, and the original image in handwritten
              mode, to Google Gemini. This local prototype has no patient
              authentication.
            </p>
          </div>
        </section>
      </div>
      <ErrorBox message={error} />
      {mode === "live" && health?.demo_mode && (
        <ErrorBox message="Live analysis is disabled. Set DEMO_MODE=false and configure your confirmed free-tier Gemini key to analyze uploaded files." />
      )}
      <div className="action-bar">
        <div>
          <ShieldCheck size={20} />
          <span>
            Every instruction is reviewed before it becomes part of your care
            plan.
          </span>
        </div>
        <button
          className="button"
          disabled={busy || (!sample && !file)}
          onClick={analyze}
        >
          {busy ? (
            <LoaderCircle className="spin" size={18} />
          ) : (
            <Sparkles size={18} />
          )}{" "}
          {busy ? "Processing document…" : "Analyze document"}
          {!busy && <ArrowRight size={18} />}
        </button>
      </div>
      {busy && (
        <div className="processing" role="status">
          <span className="pulse" /> Reading the document and{" "}
          {mode === "demo"
            ? "loading the prerecorded analysis"
            : "requesting a grounded AI explanation"}
          …
          <span className="fine">
            {(sample
              ? ["handwritten", "blurry"].includes(sample) ? "handwritten" : "printed"
              : documentMode) === "handwritten"
              ? "Image validation → visible-text transcription → structured analysis → safety checks. Handwriting is not guaranteed to be readable."
              : "File validation → PDF text or printed OCR → structured analysis → safety checks."}
          </span>
        </div>
      )}
    </>
    </Localized>
  );
}
