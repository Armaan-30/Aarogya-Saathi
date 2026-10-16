## IMPORTANT UPDATE — HYBRID OCR + GEMINI AI DOCUMENT PROCESSING

Update the AarogyaSaathi AI project to use a hybrid document-processing system that combines **Tesseract OCR, PyMuPDF, Google Gemini text analysis, and Gemini Vision**.

This functionality must integrate into our existing React frontend and Python FastAPI backend. Do not replace the existing architecture or redesign unrelated components.

### 1. Document Processing Strategy

The application must intelligently process three categories of medical documents.

**A. Printed PDF Documents**
- Use PyMuPDF to extract embedded text.
- If sufficient readable text exists, send it to Gemini for structured analysis.
- If the PDF is scanned or lacks readable text, render its pages as images and process them with Tesseract OCR.
- Use Gemini to extract and simplify medical instructions from the resulting text.

**B. Printed Prescription Images**
- Accept JPG, JPEG, and PNG images.
- Use Pillow and OpenCV when necessary to improve image readability through resizing, rotation correction, and contrast enhancement.
- Use Tesseract OCR to extract printed text.
- Send the extracted text to Gemini for medical information extraction and simplified explanations.
- Preserve the original image and extracted text for comparison.

**C. Handwritten Prescription Images**
- Detect possible handwriting or provide a user-selectable "Handwritten Prescription" mode. Do not assume handwriting can always be identified reliably.
- Send the original image directly to a vision-capable Gemini model.
- Ask Gemini to transcribe only what is visibly readable.
- Extract medication names, dosage instructions, frequencies, and doctor-provided precautions only when clearly supported by the document.
- Mark ambiguous or unreadable fields as "Needs Professional Verification."
- Do not invent missing information or guess medicine names.
- Display the original prescription alongside the AI interpretation.

### 2. Hybrid Processing Architecture

Implement this workflow:

Document Upload

↓

File Validation

↓

Document Type Selection / Detection

↓

**Printed PDF:** PyMuPDF → Text Extraction

**Scanned PDF / Printed Image:** Tesseract OCR → Extracted Text

**Handwritten Image:** Gemini Vision → Visible Text Transcription

↓

Gemini AI Text Analysis

↓

Structured Medical Information Extraction

↓

Pydantic Schema Validation + Source Evidence Checking

↓

Human Review and Safety Verification

↓

Patient Recovery Dashboard

The system must choose the correct processing path based on document characteristics and user selection.

Do not automatically assume that a high OCR confidence score guarantees a medically correct transcription.

### 3. Gemini AI Analysis

Use the existing free-tier Gemini API configuration:

`GEMINI_API_KEY`

`GEMINI_MODEL=gemini-2.5-flash-lite`

Use the official `google-genai` Python SDK.

Make the model configurable, verify that image input is supported by the selected model, and handle quota failures appropriately.

Use Gemini for:
- Medical document text understanding.
- Structured medicine information extraction.
- Identifying follow-up instructions.
- Simplifying complicated medical terminology.
- Producing English, Hindi, and Marathi explanations.
- Vision-based transcription of handwritten prescription images.

Do not send the same document repeatedly to Gemini unnecessarily. Minimize API calls to stay within free-tier limits.

### 4. Structured Output

Return validated JSON containing:

- Document type.
- Processing method used.
- Original extracted text.
- Simplified explanation.
- Medication names as written.
- Dosage and frequency as written.
- Duration if explicitly stated.
- Follow-up dates if present.
- Recovery instructions.
- Documented precautions.
- Source evidence.
- Uncertain or unreadable fields.
- Verification requirements.

Do not invent medication schedules or medical information missing from the source document.

### 5. Medical Safety Requirements

This is a healthcare application, so accuracy and transparency are essential.

- Never guess unclear handwritten medication names or dosages.
- Never prescribe medicines or change treatment instructions.
- Never interpret uncertain OCR results as confirmed medical facts.
- Show original document excerpts alongside extracted information.
- Clearly label whether information came from OCR or Gemini Vision.
- Flag ambiguous fields.
- Require human review before creating actionable medication reminders.
- Require appropriate healthcare-professional clarification for unresolved medication information.
- Never claim that patient review equals clinical verification.
- Explain that the system assists with understanding doctor-provided instructions and does not replace medical professionals.

Use synthetic medical documents only during development and demonstration.

### 6. React Frontend Improvements

Improve the existing document upload and analysis pages to support this hybrid workflow.

Include:

**Document Upload**
- PDF, JPG, JPEG, PNG support.
- Printed Document mode.
- Handwritten Prescription mode.
- Automatic extraction where appropriate.
- Processing progress indicator.

**Analysis Results**
- Original document preview.
- Extracted text panel.
- AI-simplified explanation.
- Medication information cards.
- Clear uncertainty warnings.
- Processing method indicator: PyMuPDF, Tesseract OCR, or Gemini Vision.
- Verification controls.

For desktop, use a two-column layout showing the original document and AI results.

For mobile, stack these sections vertically with accessible navigation.

Maintain the existing premium medical teal, navy, and white UI/UX design.

### 7. Backend Implementation

Organize the code into separate services:

- `document_extractor.py` — PDF and document handling.
- `image_preprocessor.py` — Image preparation.
- `ocr_service.py` — Tesseract OCR.
- `gemini_vision_service.py` — Handwriting transcription.
- `gemini_analysis_service.py` — Medical text analysis.
- `verification_service.py` — Source validation and safety checks.

Keep services modular and reusable for our future React Native mobile application.

Handle invalid files, unreadable images, missing OCR dependencies, Gemini quota errors, API timeouts, and unavailable models gracefully.

### 8. Testing Requirements

Test the complete workflow using synthetic documents:

1. A clear printed discharge summary PDF.
2. A scanned printed prescription.
3. A handwritten fictional prescription.
4. A blurry or partially unreadable prescription.
5. A document with missing medicine dosage information.

Verify that:
- Printed PDF extraction works.
- Tesseract OCR processes scanned text.
- Gemini Vision can analyze supported image inputs when the API is available.
- Gemini structures extracted information correctly.
- Unreadable fields are marked uncertain.
- The application never silently invents missing medicine details.
- Results appear correctly on desktop and mobile.
- Confirmed information can flow into the recovery dashboard.
- Unresolved medication details cannot generate actionable reminders.

Use mocked Gemini responses for automated tests. Run live integration checks only when a configured API key and available quota permit them.

### 9. Hackathon Demonstration

Prepare two primary examples:

**Demo 1 — Printed Hospital Discharge Summary**

Upload PDF → PyMuPDF/Tesseract → Gemini Analysis → Simplified Explanation → Verification → Recovery Dashboard.

**Demo 2 — Handwritten Prescription**

Upload Image → Gemini Vision → Handwriting Transcription → Gemini Analysis → Highlight Uncertain Fields → Professional Verification Required.

For handwritten prescriptions, demonstrate how the system identifies uncertainty rather than pretending every medication is recognized accurately.

Clearly distinguish live AI processing from prerecorded demonstration results.

### 10. Implementation Instructions

Inspect the existing repository before making changes.

Integrate the hybrid processing system without breaking existing functionality.

Do not rebuild the entire project from scratch.

Prioritize:
1. Working printed PDF and OCR processing.
2. Reliable Gemini structured text analysis.
3. Gemini Vision handwriting support.
4. Medical information verification.
5. Clean React analysis interface.
6. Functional recovery dashboard.
7. Automated tests and demo examples.

Keep all technologies free-tier-first and avoid paid APIs.

Do not claim that handwritten prescriptions can be interpreted with guaranteed accuracy.

**BEGIN IMPLEMENTING THIS HYBRID OCR + GEMINI DOCUMENT PROCESSING PIPELINE NOW.**