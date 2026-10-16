# Production-readiness plan

This is a planning artifact for moving from the synthetic-data hackathon MVP toward a reviewed pilot. It is not a claim that the app is clinically or legally approved.

The prototype now has local account sessions, per-patient document ownership, consent-based caregiver invitations/revocation, access/task audit events, and explicit reminder status. Caregiver invitations are manually shared one-time codes (no email is sent). These controls are for the localhost synthetic-data demo only. Password recovery, identity verification, MFA, robust rate limiting, account/data deletion, encryption-at-rest and production incident controls are not implemented.

## P0 — Keep the demo safe and repeatable

- Use fictional documents only; rotate the API credential shared in chat before any presentation or repository sharing.
- Keep the demo key server-side, set quota limits and alerting in the provider console, and have a prerecorded/offline walkthrough ready.
- Continue requiring source comparison and professional clarification for uncertain, low-confidence or handwritten medicine details.
- Record a small, versioned set of synthetic OCR/handwriting evaluation examples and review errors before changing prompts or models.
- Have a clinician review any patient-facing language and safety copy before a real-user trial.

## P1 — Design a controlled pilot before real records

- Extend and independently review the prototype's patient/caregiver roles, authenticated document/plan ownership checks, session expiry and task permissions. Add identity verification, MFA and account recovery before remote use.
- Replace local SQLite and local file storage with encrypted, access-controlled storage; implement retention/deletion, backup and incident-response procedures.
- Minimize provider data sent to Gemini, disclose the transfer clearly, review provider retention and contractual terms, and add per-user quotas and abuse controls.
- Extend the prototype's document access, caregiver access and task-change audit events to cover export, review decisions and deletion without logging API keys or unnecessary health data.
- Add distributed rate limits, request size/time limits, malware/file scanning, dependency patching, managed secrets and production monitoring.
- Complete privacy, security and clinical risk review with qualified reviewers for the actual deployment jurisdiction and intended users.
- Run a supervised usability pilot with informed participants and synthetic or properly governed data; define stop conditions and escalation routes.

## P2 — Mobile client

- The current FastAPI endpoints already separate the client from core workflows, so a React Native/Expo client is technically feasible.
- Before real patient data, migrate the existing prototype sessions and ownership controls to a reviewed identity provider and secure managed storage; implement deletion and retention behavior and repeat authorization testing. The current SQLite database and uploaded files stay local and are not encrypted at rest.
- Build mobile-specific camera/document capture, upload progress/cancellation, accessible review screens, secure local session storage and OS notification permission flows.
- Treat notifications as optional user-configured reminders based only on explicit source instructions; never infer a dose or time. Test timezone changes, restart behavior, duplicate alerts and opt-out.
- Validate API contracts, error states, small-screen comparisons, Android/iOS behavior, offline behavior and accessibility before release.

## Release gates

Do not call the product production-ready until security and privacy review, clinical-language review, representative OCR/transcription evaluation, authenticated authorization tests, data lifecycle controls, provider review and a monitored pilot have all passed for the chosen deployment context.
