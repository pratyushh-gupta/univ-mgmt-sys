import { apiRequest } from "./client";

export const listAdmissions = (query = "") => apiRequest(`/admin/admissions${query}`);
export const createAdmission = (body) => apiRequest("/admin/admissions", { method: "POST", body });
export const reviewAdmission = (id, body) => apiRequest(`/admin/admissions/${id}/review`, { method: "PATCH", body });
