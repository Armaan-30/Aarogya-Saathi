import { test, expect } from "@playwright/test";

test("interface language can be changed and stays separate from medical source text", async ({ page }) => {
  await page.goto("/");
  const language = page.locator("#app-language");
  await language.selectOption("hi");
  await expect(page.getByRole("heading", { name: "आपकी देखभाल की जगह में स्वागत है" })).toBeVisible();
  await page.locator(".sidebar").getByRole("link", { name: "दस्तावेज़ अपलोड करें" }).click();
  await expect(page.getByRole("heading", { name: "आइए, आपके निर्देशों को आसानी से समझें।" })).toBeVisible();

  await language.selectOption("mr");
  await expect(page.getByRole("heading", { name: "तुमच्या सूचना समजायला सोप्या करूया." })).toBeVisible();
  await page.goto("/upload?sample=clear");
  await page.getByRole("button", { name: "कागदपत्राचे विश्लेषण करा" }).click();
  await expect(page.getByText("DemoMed A", { exact: true }).first()).toBeVisible();
});
