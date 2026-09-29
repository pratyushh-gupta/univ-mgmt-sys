import { apiRequest } from "./client";

export const listDepartments = () => apiRequest("/departments", { auth: false });
export const createDepartment = (body) => apiRequest("/departments", { method: "POST", body });
