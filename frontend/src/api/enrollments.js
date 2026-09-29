import { apiRequest } from "./client";

export const listEnrollments = (query = "") => apiRequest(`/enrollments${query}`);
export const createEnrollment = (body) => apiRequest("/enrollments", { method: "POST", body });
export const bulkEnroll = (body) => apiRequest("/enrollments/bulk", { method: "POST", body });
export const listAvailableOfferings = () => apiRequest("/student/course-offerings");
export const enrollSelf = (courseOfferingId) => apiRequest("/student/enrollments", { method: "POST", body: { course_offering_id: courseOfferingId } });
export const dropSelf = (id) => apiRequest(`/student/enrollments/${id}`, { method: "DELETE" });
export const getAcademicHistory = () => apiRequest("/student/history");
