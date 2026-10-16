import { test, expect } from "@playwright/test";

test("patient can create and revoke a caregiver invitation", async ({ page }) => {
  await page.goto("/caregivers");
  await expect(page.getByRole("heading", { name: "Caregiver dashboard" })).toBeVisible();
  const invitedEmail = `caregiver-${Date.now()}@example.invalid`;
  await page.getByLabel("Caregiver email").fill(invitedEmail);
  await page.getByRole("button", { name: "Create invitation code" }).click();
  const invitation = page.locator(".invite-code-box");
  await expect(invitation).toContainText("Share this one-time code privately");
  await expect(invitation.locator("code")).toContainText(/[A-Za-z0-9_-]{20,}/);
  const relation = page.locator(".caregiver-relation").filter({ hasText: invitedEmail });
  await expect(relation).toContainText("pending");
  await relation.getByRole("button", { name: "Revoke access" }).click();
  await expect(page.locator(".success-note")).toContainText("Caregiver access revoked.");
  await expect(relation).toContainText("revoked");
});
