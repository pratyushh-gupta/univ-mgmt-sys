import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

import Login from "./pages/Login";

import StudentHome from "./pages/student/StudentHome";
import Courses from "./pages/student/Courses";
import Attendance from "./pages/student/Attendance";
import Results from "./pages/student/Results";
import Assignments from "./pages/student/Assignments";
import Notices from "./pages/student/Notices";
import Profile from "./pages/student/Profile";
import CourseRegistration from "./pages/student/CourseRegistration";
import AcademicHistory from "./pages/student/AcademicHistory";
import Exams from "./pages/student/Exams";
import Notifications from "./pages/student/Notifications";
import Timetable from "./pages/student/Timetable";

import AdminHome from "./pages/admin/AdminHome";
import ManageStudents from "./pages/admin/ManageStudents";
import ManageFaculty from "./pages/admin/ManageFaculty";
import ManageCourses from "./pages/admin/ManageCourses";
import Admissions from "./pages/admin/Admissions";
import ManageEnrollments from "./pages/admin/ManageEnrollments";
import AcademicOperations from "./pages/admin/AcademicOperations";

import FacultyHome from "./pages/faculty/FacultyHome";
import MyCourses from "./pages/faculty/MyCourses";
import MarkAttendance from "./pages/faculty/MarkAttendance";
import EnterResults from "./pages/faculty/EnterResults";
import Roster from "./pages/faculty/Roster";
import AcademicWork from "./pages/faculty/AcademicWork";
import FacultyTimetable from "./pages/student/Timetable";

const studentMenu = [
  { to: "/student", label: "Dashboard", icon: "🏠", end: true },
  { to: "/student/courses", label: "My Courses", icon: "📚" },
  { to: "/student/registration", label: "Course Registration", icon: "📝" },
  { to: "/student/attendance", label: "Attendance", icon: "📊" },
  { to: "/student/timetable", label: "Timetable", icon: "🗓️" },
  { to: "/student/results", label: "Results", icon: "📝" },
  { to: "/student/exams", label: "Exams", icon: "🗓️" },
  { to: "/student/assignments", label: "Assignments", icon: "📋" },
  { to: "/student/notices", label: "Notices", icon: "🔔" },
  { to: "/student/notifications", label: "Notifications", icon: "📣" },
  { to: "/student/history", label: "Academic History", icon: "📜" },
  { to: "/student/profile", label: "Profile", icon: "👤" },
];

const adminMenu = [
  { to: "/admin", label: "Overview", icon: "🏠", end: true },
  { to: "/admin/students", label: "Students", icon: "🎒" },
  { to: "/admin/admissions", label: "Admissions", icon: "📨" },
  { to: "/admin/enrollments", label: "Enrollments", icon: "✅" },
  { to: "/admin/academic-operations", label: "Academic Operations", icon: "📊" },
  { to: "/admin/faculty", label: "Faculty", icon: "🧑‍🏫" },
  { to: "/admin/courses", label: "Courses", icon: "📚" },
];

const facultyMenu = [
  { to: "/faculty", label: "Dashboard", icon: "🏠", end: true },
  { to: "/faculty/courses", label: "My Courses", icon: "📚" },
  { to: "/faculty/roster", label: "Class Rosters", icon: "👥" },
  { to: "/faculty/work", label: "Assignments & Exams", icon: "📋" },
  { to: "/faculty/timetable", label: "Teaching Timetable", icon: "🗓️" },
  { to: "/faculty/attendance", label: "Mark Attendance", icon: "📊" },
  { to: "/faculty/results", label: "Enter Results", icon: "📝" },
];

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* STUDENT */}
          <Route
            path="/student"
            element={
              <ProtectedRoute allowedRole="student">
                <Layout menu={studentMenu} brandLabel="Student Portal" pageTitle="Student Portal" />
              </ProtectedRoute>
            }
          >
            <Route index element={<StudentHome />} />
            <Route path="courses" element={<Courses />} />
            <Route path="registration" element={<CourseRegistration />} />
            <Route path="history" element={<AcademicHistory />} />
            <Route path="exams" element={<Exams />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="attendance" element={<Attendance />} />
            <Route path="timetable" element={<Timetable />} />
            <Route path="results" element={<Results />} />
            <Route path="assignments" element={<Assignments />} />
            <Route path="notices" element={<Notices />} />
            <Route path="profile" element={<Profile />} />
          </Route>

          {/* ADMIN */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRole="admin">
                <Layout menu={adminMenu} brandLabel="Admin Panel" pageTitle="Admin Panel" />
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminHome />} />
            <Route path="students" element={<ManageStudents />} />
            <Route path="admissions" element={<Admissions />} />
            <Route path="enrollments" element={<ManageEnrollments />} />
            <Route path="academic-operations" element={<AcademicOperations />} />
            <Route path="faculty" element={<ManageFaculty />} />
            <Route path="courses" element={<ManageCourses />} />
          </Route>

          {/* FACULTY */}
          <Route
            path="/faculty"
            element={
              <ProtectedRoute allowedRole="faculty">
                <Layout menu={facultyMenu} brandLabel="Faculty Portal" pageTitle="Faculty Portal" />
              </ProtectedRoute>
            }
          >
            <Route index element={<FacultyHome />} />
            <Route path="courses" element={<MyCourses />} />
            <Route path="roster" element={<Roster />} />
            <Route path="work" element={<AcademicWork />} />
            <Route path="timetable" element={<FacultyTimetable />} />
            <Route path="attendance" element={<MarkAttendance />} />
            <Route path="results" element={<EnterResults />} />
          </Route>

          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
