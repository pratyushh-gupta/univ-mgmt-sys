import { apiRequest } from "./client";
export function loginRequest(user_id, password) {
  return apiRequest("/auth/login", { method: "POST", auth: false, body: { user_id, password } });
}
export function currentUser() { return apiRequest("/auth/me"); }
