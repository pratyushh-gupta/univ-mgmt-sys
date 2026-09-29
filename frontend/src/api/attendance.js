import { apiRequest } from "./client";

export const createAttendanceSession = (body) => apiRequest("/attendance/sessions", { method: "POST", body });
export const listAttendanceSessions = (offeringId) => apiRequest(`/attendance/sessions/${offeringId}`);
