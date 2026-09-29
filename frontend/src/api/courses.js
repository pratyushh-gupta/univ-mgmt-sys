import { apiRequest } from "./client";

export const listCourses = () => apiRequest("/courses", { auth: false });
export const createCourse = (body) => apiRequest("/courses", { method: "POST", body });
export const deactivateCourse = (code) => apiRequest(`/courses/${encodeURIComponent(code)}`, { method: "DELETE" });
export const listCourseOfferings = () => apiRequest("/course-offerings");
export const createCourseOffering = (body) => apiRequest("/course-offerings", { method: "POST", body });
export const listSemesters = () => apiRequest("/semesters", { auth: false });
export const listEnrollments = () => apiRequest("/enrollments");
export const createEnrollment = (body) => apiRequest("/enrollments", { method: "POST", body });
