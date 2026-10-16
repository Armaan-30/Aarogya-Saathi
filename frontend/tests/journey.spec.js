import { test, expect } from "@playwright/test";
import path from "node:path";

test("complete sample review, translation, persisted recovery checklist", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Back home. Never on your own." }),
  ).toBeVisible();
  await page.goto("/upload?sample=clear");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(
    page.getByText("Demo Mode — Prerecorded AI Results"),
  ).toBeVisible();
  await page.getByRole("link", { name: "DemoMed A" }).click();
  await expect(page.getByRole("heading", { name: "DemoMed A" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Check official medicine information" })).toBeVisible();
  await expect(page.locator("a[target=_blank]")).toHaveCount(5);
  await page.getByRole("button", { name: "Back to document review" }).click();
  await expect(page.getByRole("link", { name: "Review my information" })).toBeVisible();
  await page.getByLabel("Explanation language").selectOption("hi");
  await expect(page.locator("p[lang=hi]")).toContainText("दस्तावेज़");
  await page.getByLabel("Explanation language").selectOption("mr");
  await expect(page.locator("p[lang=mr]")).toContainText("कागदपत्रात");
  await page.getByRole("link", { name: "Review my information" }).click();
  await expect(page.getByText("Choose Patient Reviewed or Needs clarification for every item before continuing.")).toBeVisible();
  await page.getByRole("button", { name: "Create my recovery plan" }).click();
  await expect(page.getByRole("alert")).toContainText("Review each item first.");
  const patientReviewedButtons = await page
    .getByRole("button", { name: "Patient Reviewed", exact: true })
    .all();
  for (const b of patientReviewedButtons) {
    await b.click();
    await expect(b).toHaveAttribute("aria-pressed", "true");
  }
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.getByRole("button", { name: "Create my recovery plan" }).click();
  await expect(
    page.getByRole("heading", { name: "Your checklist is ready." }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Complete DemoMed A", exact: true })
    .click();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Reopen DemoMed A", exact: true }),
  ).toBeVisible();
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});

test("incomplete instructions require clarification", async ({ page }) => {
  await page.goto("/upload?sample=incomplete");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await page.getByRole("link", { name: "Review my information" }).click();
  const cards = page.locator(".medical-card");
  await expect(
    cards.nth(0).getByRole("button", { name: "Patient Reviewed" }),
  ).toBeDisabled();
  await cards
    .nth(0)
    .getByRole("button", { name: "Needs clarification" })
    .click();
  await expect(cards.nth(0).getByRole("button", { name: "Needs clarification" })).toHaveAttribute("aria-pressed", "true");
  await cards.nth(1).getByRole("button", { name: "Patient Reviewed" }).click();
  await expect(cards.nth(1).getByRole("button", { name: "Patient Reviewed" })).toHaveAttribute("aria-pressed", "true");
  await cards
    .nth(2)
    .getByRole("button", { name: "Needs clarification" })
    .click();
  await page.setViewportSize({ width: 320, height: 900 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../screenshots/review-320.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Create my recovery plan" }).click();
  await expect(page.getByText("2 open questions")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Complete DemoMed B" }),
  ).toHaveCount(0);
});

test("file selection validates size and previews PDF", async ({ page }) => {
  await page.goto("/upload");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles({
      name: "big.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.alloc(5 * 1024 * 1024 + 1),
    });
  await expect(page.getByRole("alert")).toContainText("too large");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles(path.resolve("../demo/synthetic_documents/clear.pdf"));
  await expect(page.getByTitle("Selected PDF preview")).toBeVisible();
  await expect(page.getByLabel("Document type")).toHaveValue("printed");
});

test("scanned sample uses actual OCR", async ({ page }) => {
  await page.goto("/upload?sample=scanned");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(page.locator(".processing-badges")).toContainText(
    "Tesseract OCR",
  );
  await expect(page.getByRole("heading", { name: "DemoMed A" })).toBeVisible();
  await page.setViewportSize({ width: 320, height: 900 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("missing voice is explained without breaking the page", async ({
  page,
}) => {
  const speechRequests = [];
  await page.route("**/api/**/speech", async route => {
    const language = route.request().postDataJSON().language;
    speechRequests.push(language);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ language, mime_type: "audio/wav", audio_base64: "UklGRgAAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+" }),
    });
  });
  await page.addInitScript(() => {
    Object.defineProperty(window.speechSynthesis, "getVoices", { configurable: true, value: () => [] });
    window.AudioContext = class {
      constructor() { this.destination = {}; }
      resume() { return Promise.resolve(); }
      close() { return Promise.resolve(); }
      decodeAudioData() { return Promise.resolve({}); }
      createBufferSource() { return { connect() {}, start() {}, stop() {} }; }
    };
  });
  await page.goto("/upload?sample=clear");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await page.getByLabel("Explanation language").selectOption("hi");
  await expect(page.locator("p[lang=hi]")).toContainText("दस्तावेज़");
  await page.evaluate(() => { Object.defineProperty(window.speechSynthesis, "getVoices", { configurable: true, value: () => [] }); });
  await page.getByRole("button", { name: "Listen", exact: true }).click();
  await expect(page.locator(".voice-status")).toContainText("Audio is generated from the explanation");
  expect(speechRequests).toEqual(["hi"]);
  await page.getByLabel("Explanation language").selectOption("mr");
  await page.getByRole("button", { name: "Listen", exact: true }).click();
  await expect(page.locator(".voice-status")).toContainText("Audio is generated from the explanation");
  expect(speechRequests).toEqual(["hi", "mr"]);
});

test("document chat shows source evidence and keeps its conversation per document", async ({ page }) => {
  const history = { document_id: "chat-doc", document_name: "uploaded-discharge.pdf", messages: [] };
  await page.route("**/api/chat/history/**", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify(history),
  }));
  await page.route("**/api/chat/document", async route => {
    const body = route.request().postDataJSON();
    expect(body.document_id).toBe("chat-doc");
    expect(body.question).toBe("What follow-up did my doctor mention?");
    history.messages.push(
      { role: "user", content: body.question, citations: [], created_at: "2026-10-15T10:00:00Z" },
      { role: "assistant", content: "Return to the outpatient clinic on 22 October 2026.", citations: ["Return to the outpatient clinic on 22 October 2026 at 10:00."], created_at: "2026-10-15T10:00:01Z" },
    );
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(history) });
  });
  await page.goto("/chat/chat-doc");
  await page.getByLabel("Ask a question about this document").fill("What follow-up did my doctor mention?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.getByText("Return to the outpatient clinic on 22 October 2026.")).toBeVisible();
  await page.getByText("Source wording", { exact: true }).click();
  await expect(page.getByText("Return to the outpatient clinic on 22 October 2026 at 10:00.")).toBeVisible();
  await expect(page.getByText("Discussing: uploaded-discharge.pdf")).toBeVisible();
});

test("responsive pages fit 320, 390, 768 and 1440 pixels", async ({ page }) => {
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["/", "/upload"]) {
      await page.goto(route);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
    await page.goto("/");
    await expect(page.locator(".connection")).toContainText("connected");
    await page.screenshot({
      path: `../screenshots/home-${width}.png`,
      fullPage: true,
    });
  }
});
