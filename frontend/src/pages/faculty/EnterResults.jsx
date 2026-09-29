import { useEffect, useState } from "react";
import { apiRequest } from "../../api/client";
import useApiData from "../../hooks/useApiData";

export default function EnterResults() {
  const { data: courses, loading, error } = useApiData("/faculty/courses");
  const [selectedCode, setSelectedCode] = useState("");
  const code = selectedCode || courses[0]?.code || "";
  const [rosterState, setRosterState] = useState({ courseCode: null, status: "idle", rows: [], error: "" });
  const [marks, setMarks] = useState({});
  const [message, setMessage] = useState("");
  const rosterMatchesCourse = rosterState.courseCode === code;
  const rosterReady = Boolean(code && rosterMatchesCourse && rosterState.status === "loaded");
  const rosterLoading = Boolean(code && (!rosterMatchesCourse || rosterState.status === "loading"));
  const rosterError = rosterMatchesCourse && rosterState.status === "error" ? rosterState.error : "";
  const roster = rosterReady ? rosterState.rows : [];

  useEffect(() => {
    if (!code) return undefined;
    const controller = new AbortController();
    apiRequest(`/faculty/roster/${encodeURIComponent(code)}`, { signal: controller.signal })
      .then((rows) => {
        if (controller.signal.aborted) return;
        setRosterState({ courseCode: code, status: "loaded", rows, error: "" });
        setMarks(Object.fromEntries(rows.map((student) => [student.id, ""])));
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setRosterState({ courseCode: code, status: "error", rows: [], error: requestError.message });
      });
    return () => controller.abort();
  }, [code]);

  async function save() {
    setMessage("");
    try {
      await apiRequest("/results", {
        method: "POST",
        body: {
          course_code: code,
          results: roster
            .filter((student) => marks[student.id] !== "")
            .map((student) => ({ student_id: student.id, marks: Number(marks[student.id]) })),
        },
      });
      setMessage("Results saved.");
    } catch (saveError) {
      setMessage(saveError.message);
    }
  }

  return (
    <section className="panel full">
      <div className="panel-title"><h2>Enter Results</h2></div>
      {error && <p role="alert">{error}</p>}
      {rosterError && <p role="alert">{rosterError}</p>}
      <div className="inline-form">
        <select
          value={code}
          onChange={(event) => {
            setSelectedCode(event.target.value);
            setRosterState({ courseCode: event.target.value, status: "loading", rows: [], error: "" });
            setMessage("");
          }}
          aria-label="Course"
          disabled={loading || !courses.length}
        >
          {courses.map((course) => <option key={course.code} value={course.code}>{course.code} — {course.name}</option>)}
        </select>
      </div>
      {loading && <p>Loading courses…</p>}
      {rosterLoading && <p role="status">Loading students for {code}…</p>}
      {message && <p role="status">{message}</p>}
      <div className="table">
        <div className="table-head result-head"><span>Student</span><span>ID</span><span>Marks (out of 100)</span></div>
        {roster.map((student) => (
          <div className="table-row result-row" key={student.id}>
            <strong>{student.name}</strong>
            <span>{student.id}</span>
            <input
              type="number" min="0" max="100" className="marks-input"
              value={marks[student.id] ?? ""}
              onChange={(event) => setMarks({ ...marks, [student.id]: event.target.value })}
            />
          </div>
        ))}
      </div>
      <button className="login-btn save-attendance-btn" disabled={!code || !rosterReady || !roster.length} onClick={save}>Save Results</button>
    </section>
  );
}
