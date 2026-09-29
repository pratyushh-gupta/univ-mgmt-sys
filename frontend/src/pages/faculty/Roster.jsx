import { useEffect, useState } from "react";
import { getOfferingRoster } from "../../api/faculty";
import useApiData from "../../hooks/useApiData";

export default function Roster() {
  const { data: courses, loading, error } = useApiData("/faculty/courses");
  const [offeringId, setOfferingId] = useState("");
  const [rows, setRows] = useState([]);
  const [requestError, setRequestError] = useState("");
  const selected = offeringId || courses[0]?.id || "";
  useEffect(() => {
    if (!selected) return undefined;
    const controller = new AbortController();
    getOfferingRoster(selected, { signal: controller.signal }).then(setRows).catch((e) => { if (!controller.signal.aborted) setRequestError(e.message); });
    return () => controller.abort();
  }, [selected]);
  return <section className="panel full"><div className="panel-title"><h2>Course Roster</h2></div>
    {loading && <p>Loading offerings…</p>}{error && <p role="alert">{error}</p>}{requestError && <p role="alert">{requestError}</p>}
    <select value={selected} onChange={(e) => { setOfferingId(e.target.value); setRequestError(""); }} aria-label="Course offering">{courses.map((course) => <option key={course.id} value={course.id}>{course.code} · {course.section} · {course.semester}</option>)}</select>
    <div className="table"><div className="table-head"><span>Enrollment</span><span>Name</span><span>Login ID</span></div>{rows.map((row) => <div className="table-row" key={row.student_id}><span>{row.enrollment_number}</span><strong>{row.name}</strong><span>{row.id}</span></div>)}</div>
    {!loading && !rows.length && !requestError && <p>No enrolled students are assigned to this offering.</p>}
  </section>;
}
