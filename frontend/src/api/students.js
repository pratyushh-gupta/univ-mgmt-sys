import { apiRequest } from "./client";

export const listStudents = () => apiRequest("/students");
export const createStudent = (body) => apiRequest("/students", { method: "POST", body });
export const deactivateStudent = (id) => apiRequest(`/students/${encodeURIComponent(id)}`, { method: "DELETE" });
export const getStudentProfile = () => apiRequest("/student/profile");
export const getStudentCourses = () => apiRequest("/student/courses");
export const getStudentAttendance = () => apiRequest("/student/attendance");
export const getStudentResults = () => apiRequest("/student/results");
export const getStudentAssignments = () => apiRequest("/student/assignments");
