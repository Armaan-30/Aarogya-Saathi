import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(frontendDir, "..");
const testDb = path.join(rootDir, "backend", "aarogya-playwright.db").replaceAll("\\", "/");
const apiTarget = "http://127.0.0.1:8001";
export default defineConfig({
  testDir: "./tests",
  timeout: 60000,
  workers: 1,
  globalSetup: "./tests/global-setup.js",
  use: { baseURL: "http://127.0.0.1:5174", channel: "chrome", headless: true, storageState: "./.auth/user.json" },
  webServer: [
    {
      command: "backend\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001",
      cwd: rootDir,
      url: `${apiTarget}/api/health`,
      reuseExistingServer: false,
      env: { DATABASE_URL: `sqlite:///${testDb}`, DEMO_MODE: "true", FREE_TIER_CONFIRMED: "false", GEMINI_API_KEY: "" },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5174 --strictPort",
      cwd: frontendDir,
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
      env: { VITE_API_TARGET: apiTarget },
    },
  ],
  reporter: "list",
});
