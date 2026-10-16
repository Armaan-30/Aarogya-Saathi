import { test, expect } from "@playwright/test";
import path from "node:path";

test("handwriting demo compares original, blocks confirmation and saves open questions", async ({
  page,
}) => {
  await page.goto("/upload?sample=handwritten");
  await expect(page.getByLabel("Document type")).toHaveValue("handwritten");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(
    page.getByText("Demo Mode — Prerecorded AI Results"),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: "Original prescription for comparison" }),
  ).toBeVisible();
  await expect(page.locator(".processing-badges")).toContainText(
    "Gemini Vision (prerecorded)",
  );
  await expect(page.locator(".medical-card").first()).toContainText(
    "Needs Professional Verification",
  );
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width === 390 || width === 1440)
      await page.screenshot({
        path: `../screenshots/hybrid-${width}.png`,
        fullPage: true,
      });
  }
  await page.getByRole("link", { name: "Review my information" }).click();
  await expect(page.locator(".medical-card").first()).toBeVisible();
  for (const card of await page.locator(".medical-card").all()) {
    await expect(
      card.getByRole("button", { name: "Patient Reviewed", exact: true }),
    ).toBeDisabled();
    await card.getByRole("button", { name: "Needs clarification" }).click();
  }
  await page.getByRole("button", { name: "Create my recovery plan" }).click();
  await expect(page.getByText("3 open questions")).toBeVisible();
  await expect(page.locator(".care-task")).toHaveCount(0);
});

test("blurry demo shows no actionable instructions", async ({ page }) => {
  await page.goto("/upload?sample=blurry");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(
    page.getByRole("heading", { name: "No actionable instructions extracted" }),
  ).toBeVisible();
  await expect(page.locator(".medical-card")).toHaveCount(0);
});

test("uploading a file selects document type without a demo-mode control", async ({ page }) => {
  await page.goto("/upload");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles(path.resolve("../demo/synthetic_documents/handwritten.png"));
  await page.getByLabel("Document type").selectOption("handwritten");
  await expect(page.getByLabel("Document type")).toHaveValue("handwritten");
  await expect(page.locator("#mode")).toHaveCount(0);
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles(path.resolve("../demo/synthetic_documents/clear.pdf"));
  await expect(page.getByLabel("Document type")).toHaveValue("printed");
});

test("live image input, safe review and saved result reuse", async ({
  page,
}) => {
  test.skip(
    process.env.RUN_LIVE_VISION !== "true",
    "Opt in to real image-input requests with available free-tier quota.",
  );
  test.setTimeout(180000);
  await page.goto("/upload");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles(path.resolve("../demo/synthetic_documents/handwritten.png"));
  await page.getByLabel("Document type").selectOption("handwritten");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(page.getByText("Live Gemini AI · Unreviewed")).toBeVisible({
    timeout: 95000,
  });
  await expect(page.getByText(/Image input succeeded with/)).toBeVisible();
  await expect(page.locator(".processing-badges")).toContainText(
    "Gemini Vision",
  );
  const firstURL = page.url();
  await page.getByRole("link", { name: "Review my information" }).click();
  await expect(page.locator(".medical-card").first()).toBeVisible();
  for (const card of await page.locator(".medical-card").all()) {
    const button = card.getByRole("button", {
      name: "Patient Reviewed",
      exact: true,
    });
    await (
      (await button.isEnabled())
        ? button
        : card.getByRole("button", { name: "Needs clarification" })
    ).click();
  }
  await page.getByRole("button", { name: "Create my recovery plan" }).click();
  await expect(
    page.getByRole("heading", { name: "Your checklist is ready." }),
  ).toBeVisible();
  await expect(
    page.locator(".care-task").filter({ hasText: "DemoMed C" }),
  ).toHaveCount(0);
  await page.goto("/upload");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles(path.resolve("../demo/synthetic_documents/handwritten.png"));
  await page.getByLabel("Document type").selectOption("handwritten");
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(page).toHaveURL(firstURL);
  await expect(
    page.getByText("Saved live result reused · no new analysis call"),
  ).toBeVisible();
});
