import useApiData from "../../hooks/useApiData";

export default function StudentHome() {
  const { data, loading, error } = useApiData("/student/dashboard", { initialData: { student: {}, attendance_summary: {}, upcoming_exams: [], recent_results: [] } });
  const notices = useApiData("/notices");
  const notifications = useApiData("/notifications");
  return <>
    <section className="welcome"><div><h2>Welcome, {data.student?.name || "Student"}</h2><p>{data.student?.enrollment_number} · {data.student?.department}</p></div><div className="semester"><span>{data.current_academic_year || "Academic year"}</span><strong>{data.current_semester || "No semester assigned"}</strong></div></section>
    {loading && <p>Loading academic summary…</p>}{error && <p role="alert">{error}</p>}
    <div className="stats"><div className="stat-card"><div className="stat-icon blue">📚</div><div><span>Active Courses</span><h2>{data.enrolled_course_count ?? "—"}</h2></div></div><div className="stat-card"><div className="stat-icon green">📊</div><div><span>Attendance</span><h2>{data.attendance_summary?.percentage ?? 0}%</h2></div></div><div className="stat-card"><div className="stat-icon purple">📋</div><div><span>Pending Assignments</span><h2>{data.pending_assignments ?? "—"}</h2></div></div><div className="stat-card"><div className="stat-icon orange">🔔</div><div><span>Unread Notifications</span><h2>{data.unread_notifications ?? notifications.data.length}</h2></div></div></div>
    <div className="dashboard-grid"><section className="panel"><div className="panel-title"><h2>Upcoming Exams</h2></div>{data.upcoming_exams?.map((exam, index) => <div className="class-row" key={`${exam.name}-${index}`}><div className="class-info"><strong>{exam.name} · {exam.course_code}</strong><span>{exam.exam_date} · {exam.start_time} · {exam.room || "Room pending"}</span></div></div>)}{!loading && !data.upcoming_exams?.length && <p>No upcoming exams.</p>}</section>
      <section className="panel"><div className="panel-title"><h2>Recent Results</h2></div>{data.recent_results?.map((row, index) => <div className="class-row" key={`${row.course_code}-${index}`}><div className="class-info"><strong>{row.course_code} · {row.assessment_name}</strong><span>{row.marks}/{row.max_marks}</span></div><span className="badge">{row.grade}</span></div>)}{!loading && !data.recent_results?.length && <p>No published results.</p>}</section>
      <section className="panel"><div className="panel-title"><h2>Recent Notices</h2></div>{notices.data.slice(0, 4).map((notice) => <div className="notice" key={notice.id}><div className="notice-dot"/><div><strong>{notice.title}</strong><p>{notice.body}</p><small>{notice.date}</small></div></div>)}{!notices.loading && !notices.data.length && <p>No notices.</p>}</section>
      <section className="panel"><div className="panel-title"><h2>Attendance Summary</h2></div><p>{data.attendance_summary?.present ?? 0} present or late of {data.attendance_summary?.total ?? 0} recorded sessions.</p></section>
    </div>
  </>;
}
