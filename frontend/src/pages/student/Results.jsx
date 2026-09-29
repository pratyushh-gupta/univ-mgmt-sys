import useApiData from "../../hooks/useApiData";

export default function Results() {
  const { data, loading, error } = useApiData("/student/results", { initialData: { cgpa: null, results: [], sgpa_by_semester: [] } });
  return <section className="panel full"><div className="panel-title"><h2>Academic Results</h2><span className="overall">CGPA: {data.cgpa == null ? "Not available" : data.cgpa}</span></div>
    {loading && <p>Loading published results…</p>}{error && <p role="alert">{error}</p>}
    <h3>Semester GPA</h3><div className="table"><div className="table-head"><span>Academic period</span><span>Credits</span><span>SGPA</span></div>
      {(data.sgpa_by_semester || []).map((row) => <div className="table-row" key={row.semester_id}><strong>{row.academic_year} · {row.semester}</strong><span>{row.credits}</span><span>{row.sgpa}</span></div>)}
    </div>
    <h3>Published course results</h3><div className="table"><div className="table-head"><span>Semester / Course</span><span>Marks</span><span>Grade</span><span>Grade point</span><span>Credits</span></div>
      {(data.results || []).map((row) => <div className="table-row" key={`${row.course_offering_id}-${row.assessment}`}><strong>{row.academic_year} · {row.semester} · {row.course_code} · {row.subject}<small> · {row.assessment}{row.is_final ? " (final)" : ""}</small></strong><span>{row.marks}/{row.max_marks}</span><span className="grade">{row.grade || "—"}</span><span>{row.point ?? "—"}</span><span>{row.credits}</span></div>)}
    </div>
    {!loading && !error && !data.results?.length && <p>No published results are available yet.</p>}
  </section>;
}
