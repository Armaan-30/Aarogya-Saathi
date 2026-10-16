export async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 100000);
  try {
    const response = await fetch(`/api${path}`, {
      ...options,
      signal: controller.signal,
      credentials: "include",
      headers:
        options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" },
    });
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json().catch(() => ({}))
      : {};
    if (!response.ok)
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Please check your input and try again.",
      );
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error("Processing took too long. Please try again.");
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach the backend. Make sure it is running on port 8000.",
      );
    if (error instanceof SyntaxError)
      throw new Error("The server returned an unreadable response. Please retry.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
export const post = (path, body) =>
  api(path, { method: "POST", body: JSON.stringify(body) });
