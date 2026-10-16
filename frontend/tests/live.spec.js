import { test, expect } from "@playwright/test";
import path from "node:path";

test("real Gemini upload, translations and reviewed plan", async ({ page }) => {
  test.skip(
    process.env.RUN_LIVE !== "true",
    "Opt in with RUN_LIVE=true; consumes available free-tier quota.",
  );
  test.setTimeout(180000);
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/upload");
  await page
    .locator("input[type=file]")
    .first()
    .setInputFiles(path.resolve("../demo/synthetic_documents/clear.pdf"));
  await page.getByRole("button", { name: "Analyze document" }).click();
  await expect(page.getByText("Live Gemini AI · Unreviewed")).toBeVisible({
    timeout: 90000,
  });
  await page.getByLabel("Explanation language").selectOption("hi");
  await expect(page.locator("p[lang=hi]")).toBeVisible({ timeout: 60000 });
  await page.getByLabel("Explanation language").selectOption("mr");
  await expect(page.locator("p[lang=mr]")).toBeVisible({ timeout: 60000 });
  await page.getByRole("link", { name: "Review my information" }).click();
  await expect(page.locator(".medical-card").first()).toBeVisible();
  for (const card of await page.locator(".medical-card").all()) {
    const review = card.getByRole("button", {
      name: "Patient Reviewed",
      exact: true,
    });
    await (
      (await review.isEnabled())
        ? review
        : card.getByRole("button", { name: "Needs clarification" })
    ).click();
  }
  await page.getByRole("button", { name: "Create my recovery plan" }).click();
  await expect(
    page.getByRole("heading", { name: "Your checklist is ready." }),
  ).toBeVisible();
  await page.screenshot({
    path: "../screenshots/live-recovery-1440.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
