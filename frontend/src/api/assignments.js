import { apiRequest } from "./client";

export const listAssignments = () => apiRequest("/assignments");
export const createAssignment = (body) => apiRequest("/assignments", { method: "POST", body });
export const submitAssignment = (id, body) => apiRequest(`/assignments/${id}/submissions`, { method: "POST", body });
export const saveAssignmentDraft = (id, body) => apiRequest(`/assignments/${id}/submissions/draft`, { method: "PUT", body });
export const updateAssignment = (id, body) => apiRequest(`/assignments/${id}`, { method: "PATCH", body });
export const listSubmissions = (id) => apiRequest(`/assignments/${id}/submissions`);
export const gradeSubmission = (id, body) => apiRequest(`/submissions/${id}/grade`, { method: "PATCH", body });
