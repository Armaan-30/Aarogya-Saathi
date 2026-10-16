import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, BadgeInfo, ExternalLink, ShieldCheck } from "lucide-react";
import { Localized, useLocale } from "../i18n";
import { api } from "../services/api";

const sources = [
  {
    title: "CDSCO approved drugs search",
    description: "Search the Indian regulator’s approved drug records and indications.",
    href: "https://cdscoonline.gov.in/CDSCO/soam/drug_data.jsp",
  },
  {
    title: "CDSCO patient prescribing information",
    description: "Official patient information documents published for selected medicines.",
    href: "https://www.cdscoonline.gov.in/CDSCO/Patients",
  },
  {
    title: "Indian Pharmacopoeia Commission · National Formulary of India",
    description: "India’s national formulary and official medicine standards resources.",
    href: "https://ipc.gov.in/mandates/nfi/salient-features-of-nfi-2016.html",
  },
  {
    title: "NPPA Pharma Sahi Daam · price checker",
    description: "Check current brand MRP and government ceiling-price information in rupees. Select the exact brand/formulation and strength.",
    href: "https://nppaipdms.gov.in/NPPA/PharmaSahiDaam/searchMedicine",
  },
];

export default function MedicineInfo() {
  const { language } = useLocale();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const name = params.get("name")?.trim() || "Medicine name not provided";
  const [searchName, setSearchName] = useState(name === "Medicine name not provided" ? "" : name);
  const [strength, setStrength] = useState(params.get("strength") || "");
  const [lookup, setLookup] = useState({ loading: false, error: "", results: [], fetchedAt: "" });
  async function findApprovedUses(medicineName = searchName, exactStrength = strength) {
    if (!medicineName.trim()) return;
    setLookup(current => ({ ...current, loading: true, error: "" }));
    const query = new URLSearchParams({ name: medicineName.trim(), strength: exactStrength.trim() });
    try {
      setLookup({ loading: false, error: "", ...(await api(`/medicines/approved-use?${query}`)) });
    } catch (error) {
      setLookup({ loading: false, error: error.message, results: [], fetchedAt: "" });
    }
  }
  useEffect(() => {
    if (name !== "Medicine name not provided") findApprovedUses(name, params.get("strength") || "");
  }, []);
  return (
    <Localized language={language}>
      <div className="page-intro">
        <div>
          <span className="eyebrow">MEDICINE INFORMATION · INDIA</span>
          <h1>{name}</h1>
          <p>Official Indian government medicine resources and safe ways to verify this prescription entry.</p>
        </div>
        <BadgeInfo size={28} />
      </div>

      <section className="card medicine-info-card">
        <div className="medicine-info-heading"><ShieldCheck size={22} /><h2>What we can confirm</h2></div>
        <p>This is the medicine name read from your document. AarogyaSaathi has not independently verified its ingredient, strength, or brand. OCR can misread medicine names, so compare the spelling and strength with the original prescription or ask a pharmacist.</p>
        <div className="medicine-info-callout" role="note">
          <strong>About its use</strong>
          <p>Below we look up approved indications from CDSCO, the Indian drug regulator. An approved indication describes a regulator-approved use; it does not prove why your clinician prescribed this medicine to you. Match the active ingredient and strength on the original prescription before relying on a result.</p>
        </div>
        <div className="medicine-info-callout caution" role="note">
          <strong>Dose and timing</strong>
          <p>Follow only the directions written by your prescriber. If timing, dose, or duration is missing or unclear, ask your prescriber or pharmacist. This app will not guess a schedule.</p>
        </div>
      </section>

      <section className="medicine-source-section">
        <div className="section-heading"><div><span className="eyebrow">VERIFIED INDIAN DRUG RECORDS</span><h2>What is this medicine approved for?</h2></div></div>
        <form className="medicine-lookup card" onSubmit={event => { event.preventDefault(); findApprovedUses(); }}>
          <label>Medicine name or active ingredient<input value={searchName} onChange={event => setSearchName(event.target.value)} maxLength={100} placeholder="For example, the generic name printed on the strip" /></label>
          <label>Strength, if known<input value={strength} onChange={event => setStrength(event.target.value)} maxLength={50} placeholder="For example, 500 mg" /></label>
          <button className="button" disabled={lookup.loading || !searchName.trim()}>{lookup.loading ? "Searching CDSCO…" : "Check approved uses"}</button>
        </form>
        {lookup.loading && <p className="fine" role="status">Checking the official CDSCO database…</p>}
        {lookup.error && <div className="medicine-info-callout caution" role="alert"><strong>Official search unavailable</strong><p>{lookup.error}</p></div>}
        {!lookup.loading && !lookup.error && lookup.results.length > 0 && <div className="medicine-indication-list">
          {lookup.results.map((result, index) => <article className="card medicine-indication" key={`${result.drug_name}-${index}`}>
            <h3>{result.drug_name}</h3>
            <p><b>Approved use:</b> {result.approved_indication}</p>
            {result.strength && <p className="fine"><b>CDSCO strength/formulation:</b> {result.strength}</p>}
            {result.approval_date && <p className="fine"><b>Approval record:</b> {result.approval_date}</p>}
          </article>)}
          <p className="fine">Live CDSCO lookup; checked {lookup.fetched_at ? new Date(lookup.fetched_at).toLocaleString() : "just now"}. <a className="text-link" href={lookup.source_url} target="_blank" rel="noreferrer">Open matching CDSCO records <ExternalLink size={14} /></a></p>
        </div>}
        {!lookup.loading && !lookup.error && lookup.results.length === 0 && <div className="medicine-info-callout caution"><strong>No exact official match</strong><p>CDSCO did not return a matching approved-use entry for this name and strength. Try the active ingredient shown on the pack, then confirm the formulation with a pharmacist. We do not guess a use from a similar name.</p></div>}
      </section>

      <section className="card medicine-price-card">
        <div><span className="eyebrow">OFFICIAL PRICE INDIAN RUPEES</span><h2>Check the current medicine price</h2></div>
        <p className="medicine-price-status"><strong>₹ price for this OCR name:</strong> Not verified for an exact brand, pack and strength.</p>
        <p>AI-generated prices can be outdated or for a different brand, pack, or strength. We show pricing only from NPPA’s official price checker; select the exact brand/formulation and strength there to see its listed MRP and ceiling-price details.</p>
        <a className="button" href="https://nppaipdms.gov.in/NPPA/PharmaSahiDaam/searchMedicine" target="_blank" rel="noreferrer">Open NPPA price checker <ExternalLink size={16} /></a>
      </section>

      <section className="medicine-source-section">
        <div className="section-heading"><div><span className="eyebrow">GOVERNMENT OF INDIA SOURCES</span><h2>Check official medicine information</h2></div></div>
        <div className="medicine-source-grid">
          {sources.map((source) => <article className="card medicine-source" key={source.href}>
            <h3>{source.title}</h3>
            <p>{source.description}</p>
            <a className="text-link" href={source.href} target="_blank" rel="noreferrer">Open official source <ExternalLink size={15} /></a>
          </article>)}
        </div>
        <p className="fine medicine-source-note">These links open official Indian government resources. Availability and coverage vary; a search result is not confirmation that a medicine is right for you.</p>
      </section>

      <div className="action-bar medicine-back"><button className="button secondary" onClick={() => navigate(-1)}> <ArrowLeft size={17} /> Back to document review</button><span>For questions about your own treatment, contact your healthcare professional.</span></div>
    </Localized>
  );
}
