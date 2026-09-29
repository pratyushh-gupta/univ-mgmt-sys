import { apiRequest } from "./client";

export const listExams = () => apiRequest("/exams");
export const createExam = (body) => apiRequest("/exams", { method: "POST", body });
export const listExamSchedules = () => apiRequest("/exam-schedules");
export const createExamSchedule = (body) => apiRequest("/exam-schedules", { method: "POST", body });
