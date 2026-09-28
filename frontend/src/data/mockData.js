// Temporary mock data.
// Jab FastAPI backend ready ho jaye, ye sab data API calls (services/api.js) se aayega.

export const studentCourses = [
  { code: "CS401", name: "Operating Systems", faculty: "Dr. Sharma", attendance: 85 },
  { code: "CS402", name: "Database Management", faculty: "Prof. Singh", attendance: 92 },
  { code: "CS403", name: "Software Engineering", faculty: "Dr. Verma", attendance: 88 },
  { code: "CS404", name: "Computer Networks", faculty: "Prof. Gupta", attendance: 79 },
  { code: "CS405", name: "Web Technologies", faculty: "Dr. Mehta", attendance: 91 },
  { code: "CS406", name: "Data Structures", faculty: "Prof. Roy", attendance: 83 },
];

export const studentResults = [
  { subject: "Operating Systems", grade: "A", point: "9" },
  { subject: "Database Management", grade: "A+", point: "10" },
  { subject: "Software Engineering", grade: "A", point: "9" },
  { subject: "Computer Networks", grade: "B+", point: "8" },
  { subject: "Web Technologies", grade: "A+", point: "10" },
  { subject: "Data Structures", grade: "A", point: "9" },
];

export const todaysClasses = [
  { time: "09:00 AM", subject: "Operating Systems", room: "Room 204" },
  { time: "11:00 AM", subject: "Software Engineering", room: "Lab 3" },
  { time: "02:00 PM", subject: "Database Management", room: "Room 105" },
];

export const notices = [
  {
    title: "Mid-Semester Examination",
    body: "Examination schedule has been published.",
    date: "Today",
  },
  {
    title: "Project Submission",
    body: "Submit your project before Friday.",
    date: "Yesterday",
  },
];

export const fullNotices = [
  {
    title: "Mid-Semester Examination Schedule",
    body: "The mid-semester examination schedule has been published. Students are requested to check the examination portal.",
    date: "September 2, 2026",
  },
  {
    title: "Project Submission Deadline",
    body: "All students must submit their Software Engineering project before the deadline.",
    date: "September 1, 2026",
  },
  {
    title: "Library Timing Updated",
    body: "The university library will remain open until 8:00 PM during examination preparation.",
    date: "August 30, 2026",
  },
];

export const assignments = [
  {
    title: "Operating Systems Assignment",
    subject: "Operating Systems",
    due: "September 5, 2026",
    status: "Pending",
  },
  {
    title: "University Management System",
    subject: "Software Engineering",
    due: "September 7, 2026",
    status: "Pending",
  },
  {
    title: "Database Normalization",
    subject: "Database Management",
    due: "September 10, 2026",
    status: "Submitted",
  },
];

// Admin-side mock data

export const allStudents = [
  { id: "2024CS1042", name: "Prem Kumar", department: "Computer Science", semester: 5, email: "prem@university.edu" },
  { id: "2024CS1043", name: "Pratyush Gupta", department: "Computer Science", semester: 5, email: "pratyush@university.edu" },
  { id: "2024EC1021", name: "Koushal", department: "Computer Science", semester: 5, email: "koushal@university.edu" },
  { id: "2023ME1011", name: "Nayan ", department: "Computer Science", semester: 5, email: "nayan@university.edu" },
  { id: "2023ME1012", name: "Jahid ", department: "Computer Science", semester: 6, email: "jahid@university.edu" },
];

export const allFaculty = [
  { id: "F001", name: "Dr. Sharma", department: "Computer Science", subject: "Operating Systems", email: "sharma@university.edu" },
  { id: "F002", name: "Prof. Singh", department: "Computer Science", subject: "Database Management", email: "singh@university.edu" },
  { id: "F003", name: "Dr. Verma", department: "Computer Science", subject: "Software Engineering", email: "verma@university.edu" },
];

export const allCourses = [
  { code: "CS401", name: "Operating Systems", faculty: "Dr. Sharma", department: "Computer Science", enrolled: 42 },
  { code: "CS402", name: "Database Management", faculty: "Prof. Singh", department: "Computer Science", enrolled: 38 },
  { code: "CS403", name: "Software Engineering", faculty: "Dr. Verma", department: "Computer Science", enrolled: 45 },
];

// Faculty-side mock data

export const facultyCourseRoster = [
  { id: "2024CS1042", name: "Prem Kumar", attendance: 85, marks: 78 },
  { id: "2024CS1043", name: "Pratyush Gupta", attendance: 92, marks: 88 },
  { id: "2024CS1044", name: "Koushal", attendance: 74, marks: 65 },
  { id: "2024CS1045", name: "Nayan ", attendance: 96, marks: 91 }
];
