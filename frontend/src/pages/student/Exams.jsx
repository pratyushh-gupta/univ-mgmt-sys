import useApiData from "../../hooks/useApiData";

export default function Exams() {
  const { data, loading, error } = useApiData("/student/exams");
  return <section className="panel full"><div className="panel-title"><h2>Exam Schedule</h2></div>
    {loading && <p>Loading exams…</p>}{error && <p role="alert">{error}</p>}
    {data.map((exam) => <div className="class-row" key={exam.id}><div className="class-info"><strong>{exam.exam_name} · {exam.course_code} — {exam.course_name}</strong><span>{exam.exam_date} · {exam.start_time}–{exam.end_time} · {exam.room || "Room pending"}</span></div><span className="badge">{exam.exam_type}</span></div>)}
    {!loading && !error && !data.length && <p>No exams are scheduled for your active enrollments.</p>}
  </section>;
}
