import { apiRequest } from "./client";

export const listNotices = () => apiRequest("/notices", { auth: false });
export const createNotice = (body) => apiRequest("/notices", { method: "POST", body });
