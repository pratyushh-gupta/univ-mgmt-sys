import { apiRequest } from "./client";

export const listResults = () => apiRequest("/results");
export const gradeResults = (body) => apiRequest("/results/batch", { method: "POST", body });
export const publishResult = (id) => apiRequest(`/results/${id}/publish`, { method: "POST" });
