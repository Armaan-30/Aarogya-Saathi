# AarogyaSaathi AI — three-minute demo

Start the frontend and backend, then open http://localhost:5173. On first use, create a local account with an email and password; caregiver invitation code is optional. Existing local records are assigned to that first account. Use only the bundled synthetic files; never upload real patient records. Check audio on the presentation device and keep the readable explanation as a backup.

1. **0:00–0:20 · Welcome.** Introduce AarogyaSaathi as a local hackathon prototype that helps people understand discharge instructions.
2. **0:20–0:35 · Choose a language.** Switch the interface to Hindi or Marathi and show that the main navigation and key copy follow the selection.
3. **0:35–1:00 · Upload.** Upload `demo/synthetic_documents/clear.pdf`. The app analyzes uploaded documents using the configured live service; announce that it is a live Gemini request. Only use synthetic data.
4. **1:00–1:30 · Understand.** Show the explanation, extracted medicine directions, source evidence, warning and follow-up. Click the medicine name to open the in-site information page, which links only to Indian government resources. The page identifies OCR text as unverified and does not infer the patient's condition.
5. **1:30–2:00 · Safety review.** Click **Review my information**. Compare each item with the original and select **Patient Reviewed** or **Needs clarification**. Uncertain items cannot be confirmed. The synthetic incomplete case demonstrates blocked medicine details and follow-up.
6. **2:00–2:25 · Recovery space.** Create the plan. Mark a task complete and refresh to demonstrate SQLite persistence. Show the documented follow-up and open questions. These are checklist reminders, not push notifications or recurring medicine alarms.
7. **2:25–2:45 · Regional language and voice.** Translate the explanation into Hindi or Marathi, then press **Listen**. If the device has no matching system voice, the backend generates speech using configured Gemini TTS. This needs internet and free-tier quota; the UI discloses that the translated text is sent to Google's speech service. No paid fallback is used.
8. **Medicine use and price.** Click a medicine name to search CDSCO-approved indications. Treat those as general approved uses, not proof of the patient's diagnosis or the prescriber's reason; check active ingredient and strength. For current rupee pricing, follow the link to NPPA Pharma Sahi Daam and select the exact brand, pack and strength. The app will not guess a price.
9. **Ask about the upload.** From the document analysis or sidebar, open **Ask AarogyaSaathi**. Ask a question answered directly by the uploaded text, expand **Source wording**, then ask something the document does not say to show the refusal. Responses use Gemini and require the configured Free-tier quota. Use only synthetic or otherwise non-identifiable test files.
10. **Caregiver permission (optional).** Open **Caregivers**, invite a second synthetic email, and show the one-time code and 48-hour expiry. No email is sent: register a second account with that email and code, then show its shared dashboard. Return to the patient account to revoke access and confirm it disappears. Keep the code private even in a demo.

## Hybrid OCR and Vision

Upload `demo/synthetic_documents/clear.pdf` for embedded PDF text extraction. For a printed scan, upload `demo/synthetic_documents/scanned.png`; Tesseract OCR handles the visible print. For the Vision path, upload `demo/synthetic_documents/handwritten.png` and explicitly select **Handwritten prescription**. The original image is sent to Gemini for visible-text transcription; successful image input does not prove transcription accuracy. Every handwritten medicine requires professional verification. `demo/synthetic_documents/blurry.png` demonstrates an unreadable image result.

The former visible sample-picker and analysis-mode selector have been removed from the product UI. Synthetic fixtures remain in the repository for repeatable automated tests and can be called through internal test routes; they are not presented as user-facing prescriptions.

## Offline automated fixture checks

Playwright uses bundled synthetic cases through test-only navigation/API calls. The prerecorded handwriting fixture is clearly labelled and is not a live transcription. The scanned case still exercises local Tesseract. Never describe a fixture result as live AI. To disable live requests, set `DEMO_MODE=true` in `backend/.env` and restart the backend. The primary UI accepts uploads, so use a configured live backend for manual uploaded-file demonstrations.

English speech uses the device's browser/OS voice. Hindi and Marathi use that voice when installed, otherwise the backend's configured Gemini TTS with free-tier quota. If the service is offline or quota is exhausted, an error is shown and the explanation remains readable.
