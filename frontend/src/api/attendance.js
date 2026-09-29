import { apiRequest } from "./client";

export const createAttendanceSession = (body) => apiRequest("/attendance/sessions", { method: "POST", body });
export const updateAttendanceSession = (id, body) => apiRequest(`/attendance/sessions/${id}`, { method: "PUT", body });
export const listAttendanceSessions = (offeringId) => apiRequest(`/attendance/sessions/${offeringId}`);
export const listAttendanceSummary = (offeringId) => apiRequest(`/course-offerings/${offeringId}/attendance-summary`);
