import useApiData from "../../hooks/useApiData";

export default function Attendance() {
  const { data, loading, error } = useApiData("/student/attendance", {
    initialData: { overall: null, courses: [], semesters: [], threshold_percent: 75 },
  });
  return <section className="panel full">
    <div className="panel-title"><h2>Attendance Overview</h2><span className="overall">Overall: {data.overall == null ? "No records" : `${data.overall}%`}</span></div>
    {loading && <p>Loading attendance…</p>}{error && <p role="alert">{error}</p>}
    {data.low_attendance && <p role="status">Your attendance is below the {data.threshold_percent}% university warning threshold.</p>}
    <p>{data.attended_sessions ?? 0} attended of {data.total_sessions ?? 0} recorded sessions ({data.absent_sessions ?? 0} absent).</p>
    <h3>By semester</h3><div className="table"><div className="table-head"><span>Academic period</span><span>Attended</span><span>Absent</span><span>Total</span><span>Attendance</span></div>
      {(data.semesters || []).map((row) => <div className="table-row" key={row.semester_id}><strong>{row.academic_year} · {row.semester}</strong><span>{row.attended_sessions}</span><span>{row.absent_sessions}</span><span>{row.total_sessions}</span><span>{row.attendance == null ? "No records" : `${row.attendance}%`}</span></div>)}
    </div>
    <h3>By course</h3><div className="table"><div className="table-head"><span>Course</span><span>Attended</span><span>Absent</span><span>Total sessions</span><span>Attendance</span></div>
      {(data.courses || []).map((course) => <div className="table-row" key={course.course_offering_id}><strong>{course.code} · {course.name}</strong><span>{course.attended_sessions}</span><span>{course.absent_sessions}</span><span>{course.total_sessions}</span><span>{course.attendance == null ? "No records" : `${course.attendance}%`}{course.low_attendance && <small> · Low</small>}</span></div>)}
    </div>
    {!loading && !error && !data.courses?.length && <p>No attendance has been recorded for your enrollments.</p>}
  </section>;
}
