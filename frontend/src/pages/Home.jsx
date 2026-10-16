import { Link } from "react-router-dom";
import {
  ArrowRight,
  FileUp,
  Sparkles,
  Pill,
  Languages,
  Volume2,
  ShieldCheck,
  Check,
  Heart,
} from "lucide-react";
import { Localized, useLocale } from "../i18n";

export default function Home({ lastPlan }) {
  const { language } = useLocale();
  return (
    <Localized language={language}>
    <>
      <div className="page-intro">
        <div>
          <span className="eyebrow">
            A HEALTHIER TOMORROW STARTS WITH CLARITY
          </span>
          <h1>
            Welcome to your care space<span className="teal">.</span>
          </h1>
          <p>A little guidance for every step of your recovery.</p>
        </div>
        <span className="edition">
          <span /> AI for India · 2026
        </span>
      </div>
      <section className="hero">
        <div className="hero-copy">
          <span className="hero-label">
            <Heart size={14} /> CARE THAT CONTINUES AT HOME
          </span>
          <h2>
            Back home.
            <br />
            Never on your own.
          </h2>
          <p>
            Your Smart Post-Hospital Recovery Companion.
            <br />
            Turn complex medical documents into clear, everyday instructions —
            in your language.
          </p>
          <Link className="button" to="/upload">
            <FileUp size={19} /> Upload medical document{" "}
            <ArrowRight size={18} />
          </Link>
          <div className="hero-hint">
            <ShieldCheck size={15} /> Understand first. Review together. Recover
            with confidence.
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="floating-heart">
            <Heart fill="currentColor" />
          </div>
          <div className="illustration-paper">
            <div className="paper-header">
              <span className="paper-logo">✚</span>
              <span>
                YOUR RECOVERY
                <br />
                <strong>A little clearer, every day.</strong>
              </span>
              <span className="paper-dot" />
            </div>
            <div className="paper-lines">
              <i />
              <i />
            </div>
            <div className="paper-task">
              <span>
                <Check size={16} />
              </span>
              <div>
                <b>Understand your instructions</b>
                <small>Simple words. Clear next steps.</small>
              </div>
            </div>
            <div className="paper-task">
              <span>
                <Check size={16} />
              </span>
              <div>
                <b>Review what matters</b>
                <small>Keep the original in view.</small>
              </div>
            </div>
            <div className="paper-task">
              <span>
                <Heart size={16} />
              </span>
              <div>
                <b>Take recovery one step at a time</b>
                <small>A care checklist made from your document.</small>
              </div>
            </div>
            <div className="paper-footer">
              <ShieldCheck size={14} /> Thoughtfully designed around you
            </div>
          </div>
          <div className="language-float">
            <Languages size={21} />
            <div>
              In a language that feels like home
              <small>English &nbsp; हिन्दी &nbsp; मराठी</small>
            </div>
          </div>
          <span className="art-plus plus-one">+</span>
          <span className="art-plus plus-two">+</span>
        </div>
      </section>
      <section>
        <div className="section-heading">
          <div>
            <span className="eyebrow">LESS CONFUSION. MORE CONFIDENCE.</span>
            <h2>A helping hand for your recovery</h2>
          </div>
          {lastPlan && (
            <Link className="text-link" to={`/recovery/${lastPlan}`}>
              Open my recovery <ArrowRight size={16} />
            </Link>
          )}
        </div>
        <div className="feature-grid">
          {[
            [
              Sparkles,
              "Clarity from complexity",
              "Understand your document with simple, source-backed explanations.",
              "AI DOCUMENT ANALYSIS",
            ],
            [
              Pill,
              "Your instructions, organized",
              "Review medicine details before adding them to your care checklist.",
              "MEDICINE CHECKLIST",
            ],
            [
              Languages,
              "Your care. Your language.",
              "Read explanations in English, Hindi or Marathi.",
              "MULTILINGUAL SUPPORT",
            ],
            [
              Volume2,
              "A voice by your side",
              "Listen to explanations with supported voices on your device.",
              "VOICE ASSISTANCE",
            ],
          ].map(([Icon, title, body, label]) => (
            <div className="card feature" key={title}>
              <div className="icon-box">
                <Icon size={23} />
              </div>
              <h3>{title}</h3>
              <p>{body}</p>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="how">
        <div>
          <span className="eyebrow">SIMPLE BY DESIGN</span>
          <h2>
            From paperwork
            <br />
            to a clearer path.
          </h2>
          <p>Three small steps to get started.</p>
        </div>
        <div className="steps">
          {[
            [
              "01",
              "Upload your document",
              "A discharge summary, prescription or clear photo.",
            ],
            [
              "02",
              "Understand & review",
              "Read the explanation and check it against the source.",
            ],
            [
              "03",
              "Create your care checklist",
              "Keep reviewed instructions together, one step at a time.",
            ],
          ].map(([n, t, d]) => (
            <div className="step" key={n}>
              <span>{n}</span>
              <div>
                <h3>{t}</h3>
                <p>{d}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
    </Localized>
  );
}
