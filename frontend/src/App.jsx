import { useEffect, useState } from "react";
import { NavLink, Link, Routes, Route, useLocation } from "react-router-dom";
import {
  HeartPulse,
  LayoutDashboard,
  FileUp,
  ClipboardCheck,
  HeartHandshake,
  ShieldCheck,
  MessageCircle,
  LogOut,
  ArrowUpRight,
  X,
  Moon,
  Sun,
} from "lucide-react";
import Home from "./pages/Home";
import Upload from "./pages/Upload";
import Analysis from "./pages/Analysis";
import Verify from "./pages/Verify";
import Recovery from "./pages/Recovery";
import MedicineInfo from "./pages/MedicineInfo";
import DocumentChat from "./pages/DocumentChat";
import AuthPage from "./pages/AuthPage";
import Caregivers from "./pages/Caregivers";
import { api, post } from "./services/api";
import { LocaleContext, Localized, translate } from "./i18n";

export default function App() {
  const [language, setLanguage] = useState(localStorage.getItem("aarogya-language") || "en");
  const [theme, setTheme] = useState(localStorage.getItem("aarogya-theme") || "light");
  const [health, setHealth] = useState(null);
  const [toast, setToast] = useState("");
  const location = useLocation();
  const [lastDoc, setLastDoc] = useState(
    localStorage.getItem("aarogya-document"),
  );
  const [lastPlan, setLastPlan] = useState(
    localStorage.getItem("aarogya-plan"),
  );
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [setupRequired, setSetupRequired] = useState(false);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);
  useEffect(() => {
    api("/health")
      .then(setHealth)
      .catch(() => setHealth({ status: "offline" }));
  }, []);
  useEffect(() => {
    api("/auth/me").then(setAuthUser).catch(() =>
      api("/auth/status").then(status => setSetupRequired(status.setup_required)).catch(() => setSetupRequired(false))
    ).finally(() => setAuthLoading(false));
  }, []);
  useEffect(() => {
    window.scrollTo(0, 0);
    window.speechSynthesis?.cancel();
  }, [location.pathname]);
  useEffect(() => {
    if (toast) {
      const id = setTimeout(() => setToast(""), 6000);
      return () => clearTimeout(id);
    }
  }, [toast]);
  function rememberDoc(id) {
    localStorage.setItem("aarogya-document", id);
    setLastDoc(id);
  }
  function rememberPlan(id) {
    localStorage.setItem("aarogya-plan", id);
    setLastPlan(id);
  }
  const nav = [
    ["/", LayoutDashboard, "Overview"],
    ["/upload", FileUp, "Upload document"],
    [
      lastDoc ? `/analysis/${lastDoc}` : "/analysis",
      ClipboardCheck,
      "Document review",
    ],
    ...(lastDoc ? [[`/chat/${lastDoc}`, MessageCircle, "Ask AarogyaSaathi"]] : []),
    [
      lastPlan ? `/recovery/${lastPlan}` : "/recovery",
      HeartHandshake,
      "My recovery",
    ],
    ["/caregivers", HeartHandshake, "Caregivers"],
  ];
  async function signOut() {
    try { await post("/auth/logout", {}); } catch {}
    setAuthUser(null);
  }
  function acceptSignIn(user) { setAuthUser(user); setSetupRequired(false); }
  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    localStorage.setItem("aarogya-theme", nextTheme);
    setTheme(nextTheme);
  }
  if (authLoading) return <div className="auth-loading" role="status">Opening your private care space…</div>;
  if (!authUser) return <LocaleContext.Provider value={{ language, setLanguage: changeLanguage }}><AuthPage setupRequired={setupRequired} onAuthenticated={acceptSignIn} theme={theme} toggleTheme={toggleTheme} /></LocaleContext.Provider>;
  function changeLanguage(value) {
    localStorage.setItem("aarogya-language", value);
    setLanguage(value);
  }
  return (
    <LocaleContext.Provider value={{ language, setLanguage: changeLanguage }}>
    <Localized language={language}>
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <HeartPulse />
          </span>
          <span>
            AarogyaSaathi<small>YOUR RECOVERY COMPANION</small>
          </span>
          <sup>AI</sup>
        </Link>
        <div className="nav-caption">YOUR CARE SPACE</div>
        <nav>
          {nav.map(([to, Icon, label]) => (
            <NavLink end={to === "/"} key={label} to={to}>
              <Icon size={20} />
              <span>{translate(label, language)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <ShieldCheck />
            <h4>
              A little support.
              <br />A lot more clarity.
            </h4>
            <p>Understand your care, one step at a time.</p>
          </div>
          <span className="india">Built for India. With care.</span>
          <span className="flag">
            <i />
            <i />
            <i />
          </span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span className="breadcrumb">
            Your care space <span>/</span>{" "}
            {location.pathname === "/"
              ? "Overview"
              : location.pathname.startsWith("/upload")
                ? "Document upload"
                : location.pathname.startsWith("/medicine")
                  ? "Medicine information"
                : location.pathname.startsWith("/chat")
                  ? "Ask AarogyaSaathi"
                : location.pathname.startsWith("/caregivers")
                  ? "Caregiver access"
                : location.pathname.startsWith("/recovery")
                  ? "My recovery"
                  : "Document review"}
          </span>
          <span
            className={`connection ${health?.status === "ok" ? "online" : ""}`}
          >
            <i />
            {health?.status === "ok"
              ? "Care workspace connected"
              : health
                ? "Backend offline"
                : "Connecting…"}
          </span>
          <div className="avatar">AS</div>
          <span className="signed-in-email">{authUser.email}</span>
          <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"} title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
            {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <button className="button small secondary signout" onClick={signOut} aria-label="Sign out"><LogOut size={15} /> Sign out</button>
          <label className="sr-only" htmlFor="app-language">Interface language</label>
          <select id="app-language" aria-label="Interface language" value={language} onChange={e => changeLanguage(e.target.value)}>
            <option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option>
          </select>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Home lastPlan={lastPlan} />} />
            <Route
              path="/upload"
              element={<Upload health={health} rememberDoc={rememberDoc} />}
            />
            <Route
              path="/analysis/:id"
              element={<Analysis notify={setToast} />}
            />
            <Route
              path="/verify/:id"
              element={<Verify rememberPlan={rememberPlan} />}
            />
            <Route
              path="/recovery/:id"
              element={<Recovery notify={setToast} />}
            />
            <Route path="/medicine" element={<MedicineInfo />} />
            <Route path="/chat/:id" element={<DocumentChat />} />
            <Route path="/caregivers" element={<Caregivers />} />
            <Route
              path="*"
              element={
                <section className="card empty">
                  <HeartHandshake size={38} />
                  <h1>Your care journey starts here</h1>
                  <p>
                    Upload a medical document to create your recovery space.
                  </p>
                  <Link className="button" to="/upload">
                    Get started <ArrowUpRight size={18} />
                  </Link>
                </section>
              }
            />
          </Routes>
        </main>
        <footer>
          <ShieldCheck size={16} />
          <span>
            Hackathon prototype · Synthetic data only · Supports understanding,
            never replaces your healthcare professional.
          </span>
        </footer>
      </div>
      <nav className="mobile-nav">
        {nav.map(([to, Icon, label]) => (
          <NavLink end={to === "/"} key={label} to={to}>
            <Icon size={21} />
            <span>
              {translate(label === "Upload document"
                ? "Upload"
                : label === "Document review"
                  ? "Review"
                : label === "My recovery"
                    ? "Recovery"
                    : label === "Ask AarogyaSaathi"
                      ? "Ask AI"
                : label === "Caregivers"
                  ? "Caregivers"
                : "Home", language)}
            </span>
          </NavLink>
        ))}
      </nav>
      {toast && (
        <div className="toast" role="status">
          {toast}
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast("")}
          >
            <X size={18} />
          </button>
        </div>
      )}
    </div>
    </Localized>
    </LocaleContext.Provider>
  );
}
