const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
export class ApiError extends Error {
  constructor(message, status) { super(message); this.name = "ApiError"; this.status = status; }
}
export async function apiRequest(path, { method = "GET", body, auth = true, ...options } = {}) {
  const headers = new Headers(options.headers || {});
  if (body !== undefined) headers.set("Content-Type", "application/json");
  const token = auth ? localStorage.getItem("access_token") : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError("Unable to reach the server. Check that the backend is running.", 0);
  }
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (response.status === 401 && auth && token) {
    localStorage.removeItem("access_token");
    window.dispatchEvent(new Event("auth:unauthorized"));
  }
  if (!response.ok) {
    const message = response.status >= 500 ? "The server could not complete the request." : (payload?.detail || `Request failed (${response.status}).`);
    throw new ApiError(typeof message === "string" ? message : "Please check the submitted information.", response.status);
  }
  return payload;
}
export function apiErrorMessage(error) { return error instanceof ApiError ? error.message : "Something went wrong. Please try again."; }
