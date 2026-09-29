import { apiRequest } from "./client";

export const listNotifications = () => apiRequest("/notifications");
export const markNotificationRead = (id) => apiRequest(`/notifications/${id}/read`, { method: "PATCH" });
