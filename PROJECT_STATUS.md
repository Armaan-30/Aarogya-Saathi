# AarogyaSaathi AI — prioritized completion status

Updated: 16 October 2026 (Asia/Calcutta).

## Overall status

**The local hackathon prototype, including hybrid OCR + Gemini Vision, is implemented and running.** This is a synthetic-data demonstration, not an application ready for real patient records or clinical use.

Status labels: `[x]` implemented and checked; `[~]` partly complete or requires a device check; `[ ]` not implemented.

## P0 — Core printed-document journey: complete

- [x] React/Vite, FastAPI, SQLAlchemy and SQLite architecture.
- [x] Responsive overview, upload, analysis, patient review and recovery pages.
- [x] PDF, PNG and JPEG upload with camera input, drag-and-drop, file preview and validation.
- [x] Content validation, 5 MB limit, 10-page/40,000-character PDF bounds and image pixel limits.
- [x] PyMuPDF extraction for readable PDF pages.
- [x] Page rendering and Tesseract fallback for scanned or sparse PDF pages.
- [x] Tesseract OCR for printed PNG/JPEG, OCR timeout and quality warnings.
- [x] Mixed PDF pages routed independently through embedded-text or OCR processing.
- [x] Gemini structured analysis, Pydantic validation, source excerpts, explanation, medication fields, follow-up and warning extraction.
- [x] Source-evidence checking, uncertainty flags and professional clarification requirements.
- [x] Required patient decisions before creating a recovery plan.
- [x] Uncertain or incomplete medicine details blocked from actionable tasks; no guessed clock-time reminders.
- [x] Local persistence of original files, extracted text, analysis, review decisions, plans and checklist completion.
- [x] Offline prerecorded samples for clear, incomplete, scanned, handwriting and blurry cases.
- [x] Removed sample prescriptions and the analysis-mode chooser from the visible product journey; synthetic fixtures remain available to automated checks.
- [x] Added a medicine detail page from each extracted medicine name, with OCR verification guidance and official Indian government references.
- [x] Added live CDSCO approved-indication lookup with medicine-name token checks, optional strength filter, and a clear warning that approved use does not establish an individual prescriber's reason.
- [x] Added NPPA Pharma Sahi Daam price-checker link in rupees. The app does not invent an amount when brand, pack and strength cannot be verified.

## P1 — Hybrid OCR + Gemini Vision: complete for prototype scope

- [x] Printed and handwritten document modes, independent of demo/live analysis mode.
- [x] Bounded printed-image orientation, resizing and contrast processing; original image remains unchanged.
- [x] Text-quality checks detect sparse/corrupt PDF text and route affected pages to OCR.
- [x] Handwritten mode sends the original PNG/JPEG bytes to Gemini Vision for constrained visible-text transcription.
- [x] Live image input was confirmed with the configured Gemini 3.5 Flash-Lite model. This verifies image request processing, not handwriting accuracy.
- [x] Transcription schema returns readable text, warnings and unreadable regions. Empty transcription skips text analysis; unreadable markers remain uncertain.
- [x] Vision output flows into structured text analysis and source matching.
- [x] Every handwritten medicine requires **Needs Professional Verification**. Patient review alone cannot release it into a recovery task.
- [x] Original image/PDF and extracted text appear with the interpretation in desktop columns and a mobile stacked view.
- [x] Processing labels identify PyMuPDF, Tesseract OCR, Gemini Vision and prerecorded Vision fixtures.
- [x] Saved live analysis reuse is keyed by content, document mode, MIME type, model and pipeline version; concurrent identical requests coalesce in the local single-worker app.
- [x] Hindi/Marathi translation responses are cached per saved document and language.
- [x] Simulated-handwriting and blurry samples show uncertainty without claiming handwriting benchmark accuracy; three additional font-rendered lookalike images exercise the same pipeline and are explicitly not human-handwriting benchmarks.
- [x] Live and prerecorded Vision results are clearly distinguished.

## P1 — Accessibility and presentation

- [x] English, Hindi and Marathi explanations; original medication wording remains available.
- [x] Browser speech play/stop with server-side Gemini TTS fallback for Hindi and Marathi when the device has no matching voice; free-tier quota and Internet required, with no paid fallback.
- [x] Added subtle page/card/drop-zone motion and hover feedback, with reduced-motion support.
- [x] Added a persistent light/dark theme toggle across the main app and sign-in screen.
- [x] Layout checks at 320, 390, 768 and 1440 pixels, including review and recovery screens.
- [x] Printed and handwritten demo steps, offline procedure, startup instructions and troubleshooting.
- [~] Physical speaker playback depends on the presentation device; browser flow is tested with a simulated Hindi/Marathi audio response and Gemini TTS was verified separately.
- [~] Added a persistent Hindi/Marathi interface selector and translated key navigation, workflow and medicine-information copy. Some technical/provenance text remains English; source medical text is deliberately unchanged.
- [x] Low-confidence/OCR warnings are now shown prominently beside the source comparison.
- [x] Added a four-condition synthetic printed OCR smoke evaluation (clear, small, faint and slightly blurred/rotated).
- [x] Added a phased security, privacy, clinical review and mobile release plan in `docs/PRODUCTION_READINESS.md`.

## P2 — Future work

- [ ] Improve CDSCO matching for brand-to-generic ingredient equivalence only with a reliable official mapping source; current lookup deliberately avoids similar-name guesses.
- [ ] Add automatic current price display only if NPPA provides a supported public integration and the exact brand, pack and strength can be verified.
- [x] Local account authentication, per-patient record ownership and isolation.
- [~] Access auditing and patient-controlled caregiver access/revocation are implemented; encrypted production storage, retention/deletion controls and deployment hardening remain.
- [ ] Clinical evaluation; model explanations and transcriptions are not clinically validated.
- [ ] OCR quality calibration on a larger synthetic set and multilingual printed samples.
- [ ] Evaluation across more synthetic handwriting styles. Do not use real patient prescriptions for demo testing.
- [ ] Recurring medicine alarms and push notifications.
- [ ] React Native/Expo app, hospital links and any ABHA/ABDM integration under their official requirements.

## Deferred feature-expansion scope (now implemented for the local prototype)

- [x] Reused the existing source-grounded review and ambiguity gate; uncertain medication details still cannot become checklist tasks.
- [x] Reused the existing reviewed, persistent recovery checklist and task completion state.
- [x] Added document-grounded Gemini chat with the selected document's OCR and structured extraction, exact quotation checks against OCR text, unsupported-answer refusal, recent conversation context and persisted per-document history.
- [x] Chat supports the current English/Hindi/Marathi selector, responsive layout, suggested questions, typing/error states and visible source quotations.
- [x] Patient-initiated caregiver invitations with one-time code, invited-email match, 48-hour expiry, revocation, plan viewing/task completion permissions and audit events.
- [x] Expanded recovery task categories and explicit date/time states (overdue, today, upcoming, date-only, unscheduled); absent clock times are never invented.
- [~] Reminders remain an on-screen checklist without recurring schedules, alarms or push notifications.
- [~] Wider language/voice validation beyond the current English/Hindi/Marathi explanation flow remains.

This pass implements local account sessions, patient-scoped records, patient-created caregiver invitations with expiry/revocation, access/task audit events, task categories, and explicit-date reminder states. It remains a local synthetic-data prototype without production identity assurance, encryption-at-rest, formal privacy compliance or clinical validation.

## Gemini configuration and key

The earlier `gemini-2.5-flash-lite` request was rejected for this account as unavailable to new users. The configured `gemini-3.5-flash-lite` passed live text, translation and Vision image requests on 15 October 2026. Model selection remains configurable; the application does not silently switch models. Free-tier confirmation is an environment setting, not an independent billing inspection.

Keep API keys in the ignored `backend/.env`; never commit them or place them in frontend code. Rotate any credential that may have been exposed before presenting or sharing the project.

## Latest validation

Recorded 16 October 2026:

- **61 backend tests passed**, including actual OCR, mixed PDFs, account isolation, caregiver consent/revocation and access auditing, explicit reminder states, source-validated chat citations, CDSCO safeguards, TTS response validation, persistence and saved-result reuse/concurrency.
- Latest full UI regression run: **13 Playwright tests passed; 2 live-provider tests were conditionally skipped**. Patient invitation/revocation, dark-mode persistence, review decisions and recovery-plan creation, medicine navigation, document chat evidence, Hindi/Marathi voice fallback, OCR and responsive widths passed. The focused review-flow rerun also passed after the review-button feedback fix.
- Earlier live Gemini text/translation and Vision integration checks passed on 15 October 2026. Live requests were not repeated during this UI-only run.
- Local frontend and API responded successfully (`200` and `/api/health: ok`; live mode configured).
- Two live Gemini chat checks using only the repository's synthetic document passed: a follow-up answer included an exact matching source quote, and a request for an unlisted medicine was refused without a citation.
- Vite production build passed.
- Four synthetic print conditions returned 0% word error in the quick local OCR smoke set; faint print correctly emitted a quality warning. This tiny English-only set is not a general accuracy measure.
- Browser screenshots were inspected at desktop and mobile sizes; synthetic printed and handwriting documents were checked.
- Two upstream Python deprecation warnings remain; neither failed a check.
- Missing Hindi/Marathi voices use Gemini TTS fallback. Browser tests mock audio playback; actual audible output remains device-dependent.

These checks show the requested demo workflow runs. They do not prove clinical, OCR or handwriting accuracy, production security or patient suitability.
