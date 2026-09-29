import { useEffect, useState } from "react";
import { getOfferingRoster } from "../../api/faculty";
import { gradeResults } from "../../api/results";
import useApiData from "../../hooks/useApiData";

export default function EnterResults() {
  const { data: courses, loading, error } = useApiData("/faculty/courses");
  const [selectedOfferingId, setSelectedOfferingId] = useState("");
  const offeringId = selectedOfferingId || courses[0]?.id || "";
  const [rosterState, setRosterState] = useState({ offeringId: null, status: "idle", rows: [], error: "" });
  const [marks, setMarks] = useState({});
  const [isFinal, setIsFinal] = useState(true);
  const [message, setMessage] = useState("");
  const rosterMatchesCourse = String(rosterState.offeringId) === String(offeringId);
  const rosterReady = Boolean(offeringId && rosterMatchesCourse && rosterState.status === "loaded");
  const rosterLoading = Boolean(offeringId && (!rosterMatchesCourse || rosterState.status === "loading"));
  const rosterError = rosterMatchesCourse && rosterState.status === "error" ? rosterState.error : "";
  const roster = rosterReady ? rosterState.rows : [];

  useEffect(() => {
    if (!offeringId) return undefined;
    const controller = new AbortController();
    getOfferingRoster(offeringId, { signal: controller.signal })
      .then((rows) => {
        if (controller.signal.aborted) return;
        setRosterState({ offeringId, status: "loaded", rows, error: "" });
        setMarks(Object.fromEntries(rows.map((student) => [student.student_id, ""])));
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setRosterState({ offeringId, status: "error", rows: [], error: requestError.message });
      });
    return () => controller.abort();
  }, [offeringId]);

  async function save() {
    setMessage("");
    try {
      await gradeResults({
        course_offering_id: Number(offeringId),
        assessment_name: "Final",
        results: roster
          .filter((student) => marks[student.student_id] !== "")
          .map((student) => ({ student_id: student.student_id, marks: Number(marks[student.student_id]), max_marks: 100, is_final: isFinal })),
      });
      setMessage("Results saved as draft. An administrator or faculty member can publish them when ready.");
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
          value={offeringId}
          onChange={(event) => {
            setSelectedOfferingId(event.target.value);
            setRosterState({ offeringId: event.target.value, status: "loading", rows: [], error: "" });
            setMessage("");
          }}
          aria-label="Course"
          disabled={loading || !courses.length}
        >
          {courses.map((course) => <option key={course.id} value={course.id}>{course.code} — {course.name} · {course.semester} · Section {course.section}</option>)}
        </select>
      </div>
      <label><input type="checkbox" checked={isFinal} onChange={(event) => setIsFinal(event.target.checked)} /> This is the final course result used for GPA</label>
      {loading && <p>Loading courses…</p>}
      {rosterLoading && <p role="status">Loading students for {courses.find((course) => String(course.id) === String(offeringId))?.code || "selected offering"}…</p>}
      {message && <p role="status">{message}</p>}
      <div className="table">
        <div className="table-head result-head"><span>Student</span><span>ID</span><span>Marks (out of 100)</span></div>
        {roster.map((student) => (
          <div className="table-row result-row" key={student.id}>
            <strong>{student.name}</strong>
            <span>{student.id}</span>
            <input
              type="number" min="0" max="100" className="marks-input"
              value={marks[student.student_id] ?? ""}
              onChange={(event) => setMarks({ ...marks, [student.student_id]: event.target.value })}
            />
          </div>
        ))}
      </div>
      <button className="login-btn save-attendance-btn" disabled={!offeringId || !rosterReady || !roster.length} onClick={save}>Save Results</button>
    </section>
  );
}
