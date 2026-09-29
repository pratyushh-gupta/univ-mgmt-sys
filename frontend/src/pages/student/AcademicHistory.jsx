import useApiData from "../../hooks/useApiData";

export default function AcademicHistory() {
  const { data, loading, error } = useApiData("/student/history");
  return <section className="panel full"><div className="panel-title"><h2>Academic History</h2></div>
    {loading && <p>Loading academic history…</p>}{error && <p role="alert">{error}</p>}
    <div className="table"><div className="table-head"><span>Period</span><span>Course</span><span>Credits</span><span>Enrollment</span><span>Results</span></div>
      {data.map((row, index) => <div className="table-row" key={`${row.course_code}-${index}`}><span>{row.academic_year} · {row.semester}</span><strong>{row.course_code} · {row.course_name}</strong><span>{row.credits}</span><span>{row.status}</span><span>{row.results.length ? row.results.map((result) => `${result.assessment_name}: ${result.grade}`).join(", ") : "No published result"}</span></div>)}
    </div>{!loading && !error && !data.length && <p>No academic history is available yet.</p>}
  </section>;
}
