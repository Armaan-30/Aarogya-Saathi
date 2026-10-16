import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Bot, FileText, MessageCircle, Send, ShieldCheck, Sparkles } from "lucide-react";
import { api, post } from "../services/api";
import { ErrorBox, Loading } from "../components/UI";
import { Localized, useLocale } from "../i18n";

const suggested = [
  "What follow-up instructions are written?",
  "Which precautions does my document mention?",
  "What information is unclear?",
];

export default function DocumentChat() {
  const { id } = useParams();
  const { language } = useLocale();
  const [conversation, setConversation] = useState(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    setConversation(null);
    setError("");
    api(`/chat/history/${id}`).then(setConversation).catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [conversation?.messages?.length, loading]);

  async function send(value = question) {
    const clean = value.trim();
    if (!clean || loading) return;
    setQuestion("");
    setError("");
    setLoading(true);
    try {
      setConversation(await post("/chat/document", { document_id: id, question: clean, language }));
    } catch (e) {
      setQuestion(clean);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (error && !conversation) return <Localized language={language}><ErrorBox message={error} /></Localized>;
  if (!conversation) return <Localized language={language}><Loading text="Opening document chat…" /></Localized>;

  return (
    <Localized language={language}>
      <div className="page-intro chat-intro">
        <div>
          <span className="eyebrow">ASK AAROGYASAATHI · DOCUMENT GROUNDED</span>
          <h1>Ask about your document.</h1>
          <p>Answers use only this uploaded document and include matching source wording.</p>
        </div>
        <Link className="button secondary" to={`/analysis/${id}`}><ArrowLeft size={17} /> Document review</Link>
      </div>

      <section className="chat-panel card" aria-label="Document question and answer">
        <div className="chat-document"><FileText size={18} /><span>Discussing: <strong>{conversation.document_name}</strong></span><span className="chat-language">Replies: {language === "hi" ? "हिन्दी" : language === "mr" ? "मराठी" : "English"}</span></div>
        <div className="chat-safety"><ShieldCheck size={18} /><span>This assistant explains existing instructions. It cannot diagnose or recommend treatment. Patient review is not clinical verification.</span></div>
        <div className="chat-messages" role="log" aria-live="polite" aria-label="Conversation">
          {!conversation.messages.length && <div className="chat-empty"><span className="chat-empty-icon"><MessageCircle /></span><h2>What would you like clarified?</h2><p>Ask about instructions in {conversation.document_name}. If the document does not contain an answer, the assistant will say so.</p><div className="chat-suggestions">{suggested.map((prompt) => <button className="chat-suggestion" key={prompt} disabled={loading} onClick={() => send(prompt)}><Sparkles size={15} />{prompt}</button>)}</div></div>}
          {conversation.messages.map((message, index) => <article className={`chat-message ${message.role}`} key={`${index}-${message.created_at}`}>
            <span className="chat-avatar" aria-hidden="true">{message.role === "assistant" ? <Bot size={18} /> : "You"}</span>
            <div className="chat-bubble"><p>{message.content}</p>{message.citations?.length > 0 && <details className="chat-citations"><summary>Source wording</summary>{message.citations.map((quote, quoteIndex) => <blockquote key={`${quoteIndex}-${quote}`}>{quote}</blockquote>)}</details>}</div>
          </article>)}
          {loading && <div className="chat-message assistant" role="status"><span className="chat-avatar"><Bot size={18} /></span><div className="chat-bubble chat-typing"><i /><i /><i /><span>Checking your document…</span></div></div>}
          <div ref={endRef} />
        </div>
        {error && <div className="chat-error" role="alert"><p>{error}</p><button className="button small secondary" onClick={() => send(question)} disabled={!question.trim() || loading}>Retry</button></div>}
        <form className="chat-composer" onSubmit={(event) => { event.preventDefault(); send(); }}>
          <label className="sr-only" htmlFor="document-question">Ask a question about this document</label>
          <textarea id="document-question" value={question} maxLength={1200} rows={2} placeholder="Ask about your instructions…" disabled={loading} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} />
          <button className="button chat-send" type="submit" disabled={!question.trim() || loading} aria-label="Send question"><Send size={18} /> Send</button>
          <span className="chat-hint">Enter to send · Shift + Enter for a new line</span>
        </form>
      </section>
      <p className="fine chat-provider-note">Your question and the selected document’s extracted text are sent to the configured Gemini service. Internet and available Free-tier quota are required; no paid fallback is used.</p>
    </Localized>
  );
}
