import useApiData from "../../hooks/useApiData";

export default function AcademicWork() {
  const assignments = useApiData("/assignments");
  const exams = useApiData("/exam-schedules");
  const results = useApiData("/results");
  const error = assignments.error || exams.error || results.error;
  return <>
    {error && <p role="alert">{error}</p>}
    <section className="panel full"><div className="panel-title"><h2>My Assignments</h2></div>{assignments.loading && <p>Loading assignments…</p>}{assignments.data.map((row) => <div className="class-row" key={row.id}><div className="class-info"><strong>{row.course_code} · {row.title}</strong><span>Due {row.due_date} · Max {row.max_marks}</span></div><span className="badge">{row.status}</span></div>)}{!assignments.loading && !assignments.data.length && <p>No assignments found for your course offerings.</p>}</section>
    <section className="panel full"><div className="panel-title"><h2>Exam Schedule</h2></div>{exams.loading && <p>Loading exams…</p>}{exams.data.map((row) => <div className="class-row" key={row.id}><div className="class-info"><strong>{row.course_code} · {row.exam_name}</strong><span>{row.exam_date} · {row.start_time}–{row.end_time} · {row.room || "Room pending"}</span></div></div>)}{!exams.loading && !exams.data.length && <p>No exams are scheduled for your courses.</p>}</section>
    <section className="panel full"><div className="panel-title"><h2>Entered Results</h2></div>{results.loading && <p>Loading results…</p>}<div className="table"><div className="table-head"><span>Student</span><span>Course / Assessment</span><span>Marks</span><span>Grade</span><span>Status</span></div>{results.data.map((row) => <div className="table-row" key={row.id}><span>{row.student_name}</span><strong>{row.course_code} · {row.assessment_name}</strong><span>{row.marks}/{row.max_marks}</span><span>{row.grade}</span><span>{row.status}</span></div>)}</div>{!results.loading && !results.data.length && <p>No results have been entered.</p>}</section>
  </>;
}
