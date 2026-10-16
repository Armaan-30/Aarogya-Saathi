import { request } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const directory = path.dirname(fileURLToPath(import.meta.url));
const statePath = path.resolve(directory, "../.auth/user.json");

export default async function globalSetup() {
  const api = await request.newContext({ baseURL: "http://127.0.0.1:8001" });
  const credentials = { email: "playwright-patient@example.invalid", password: "test-only-password-never-use-123" };
  let response = await api.post("/api/auth/login", { data: credentials });
  if (!response.ok()) response = await api.post("/api/auth/register", { data: credentials });
  if (!response.ok()) throw new Error(`Could not initialize isolated Playwright test account: ${response.status()}`);
  await mkdir(path.dirname(statePath), { recursive: true });
  await api.storageState({ path: statePath });
  await api.dispose();
}
