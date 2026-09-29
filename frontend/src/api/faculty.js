import { apiRequest } from "./client";

export const listFaculty = () => apiRequest("/faculty");
export const createFaculty = (body) => apiRequest("/faculty", { method: "POST", body });
export const deactivateFaculty = (id) => apiRequest(`/faculty/${encodeURIComponent(id)}`, { method: "DELETE" });
export const getFacultyOfferings = () => apiRequest("/faculty/courses");
export const getOfferingRoster = (id, options = {}) => apiRequest(`/course-offerings/${id}/roster`, options);
