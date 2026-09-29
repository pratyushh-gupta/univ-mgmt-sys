import useApiData from "../../hooks/useApiData";

export default function AdminHome() {
  const overview = useApiData("/admin/overview");
  const students = useApiData("/students?page_size=5", { initialData: { items: [], total: 0 } });
  const faculty = useApiData("/faculty");
  const metrics = overview.data;
  return <>
    <section className="welcome"><div><h2>University Overview</h2><p>Live academic and operational data.</p></div></section>
    {[overview.error, students.error, faculty.error].filter(Boolean).map((error) => <p role="alert" key={error}>{error}</p>)}
    <div className="stats">{[["🎒", "Active Students", metrics.active_students], ["🧑‍🏫", "Faculty", metrics.faculty], ["📚", "Active Courses", metrics.active_courses], ["🏫", "Departments", metrics.departments], ["🗂️", "Course Offerings", metrics.active_course_offerings], ["✅", "Enrollments", metrics.current_enrollments], ["📨", "Pending Admissions", metrics.pending_admissions]].map(([icon, label, count]) => <div className="stat-card" key={label}><div className="stat-icon blue">{icon}</div><div><span>{label}</span><h2>{count ?? "…"}</h2></div></div>)}</div>
    <div className="dashboard-grid"><section className="panel"><div className="panel-title"><h2>Recent Students</h2></div>{(students.data.items || []).map((row) => <div className="class-row" key={row.student_id}><div className="class-info"><strong>{row.name}</strong><span>{row.department} · {row.semester_name || "No semester"}</span></div><span className="class-status">{row.enrollment_number}</span></div>)}</section>
      <section className="panel"><div className="panel-title"><h2>Recent Faculty</h2></div>{faculty.data.slice(0, 5).map((row) => <div className="notice" key={row.faculty_id}><div className="notice-dot"/><div><strong>{row.name}</strong><p>{row.department}</p></div></div>)}</section>
      <section className="panel"><div className="panel-title"><h2>Recent Notices</h2></div>{(metrics.recent_notices || []).map((title) => <p key={title}>{title}</p>)}{!metrics.recent_notices?.length && <p>No published notices.</p>}</section>
      <section className="panel"><div className="panel-title"><h2>Recent Activity</h2></div>{(metrics.recent_audit_activity || []).map((row, index) => <p key={`${row.action}-${index}`}>{row.action} · {row.entity_type} · {row.created_at.slice(0, 10)}</p>)}{!metrics.recent_audit_activity?.length && <p>No audit activity yet.</p>}</section>
    </div>
  </>;
}
