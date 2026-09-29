import { apiRequest } from "./client";

export const listClassSchedules = () => apiRequest("/class-schedules");
export const createClassSchedule = (body) => apiRequest("/class-schedules", { method: "POST", body });
export const deactivateClassSchedule = (id) => apiRequest(`/class-schedules/${id}`, { method: "DELETE" });
