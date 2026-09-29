import { useEffect, useState } from "react";
import { getOfferingRoster } from "../../api/faculty";
import { createAttendanceSession, listAttendanceSessions, listAttendanceSummary, updateAttendanceSession } from "../../api/attendance";
import useApiData from "../../hooks/useApiData";

export default function MarkAttendance() {
  const { data: courses, loading, error } = useApiData("/faculty/courses");
  const [selectedOfferingId, setSelectedOfferingId] = useState("");
  const offeringId = selectedOfferingId || courses[0]?.id || "";
  const [rosterState, setRosterState] = useState({ offeringId: null, status: "idle", rows: [], error: "" });
  const [status, setStatus] = useState({});
  const [date, setDate] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [sessions, setSessions] = useState([]);
  const [sessionError, setSessionError] = useState("");
  const [attendanceSummary, setAttendanceSummary] = useState([]);
  const [message, setMessage] = useState("");
  const rosterMatchesCourse = String(rosterState.offeringId) === String(offeringId);
  const rosterReady = Boolean(offeringId && rosterMatchesCourse && rosterState.status === "loaded");
  const rosterLoading = Boolean(offeringId && (!rosterMatchesCourse || rosterState.status === "loading"));
  const rosterError = rosterMatchesCourse && rosterState.status === "error" ? rosterState.error : "";
  const roster = rosterReady ? rosterState.rows : [];

  useEffect(() => {
    const timer = setTimeout(() => {
      const now = new Date();
      setDate(new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10));
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!offeringId) return undefined;
    const controller = new AbortController();
    getOfferingRoster(offeringId, { signal: controller.signal })
      .then((rows) => {
        if (controller.signal.aborted) return;
        setRosterState({ offeringId, status: "loaded", rows, error: "" });
        setStatus(Object.fromEntries(rows.map((student) => [student.student_id, "present"])));
        setSessionId("");
        setDate(new Date().toISOString().slice(0, 10));
        listAttendanceSessions(offeringId).then(setSessions).catch((requestError) => setSessionError(requestError.message));
        listAttendanceSummary(offeringId).then((summary) => setAttendanceSummary(summary.students)).catch((requestError) => setSessionError(requestError.message));
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setRosterState({ offeringId, status: "error", rows: [], error: requestError.message });
      });
    return () => controller.abort();
  }, [offeringId]);

  function selectSession(id) {
    setSessionId(id);
    setMessage("");
    const selected = sessions.find((session) => String(session.id) === String(id));
    if (!selected) return;
    setDate(selected.session_date);
    const nextStatus = Object.fromEntries(roster.map((student) => [student.student_id, "present"]));
    selected.records.forEach((record) => { nextStatus[record.student_id] = record.status; });
    setStatus(nextStatus);
  }

  async function save() {
    setMessage("");
    try {
      const body = {
        course_offering_id: Number(offeringId),
        session_date: date,
        status: "published",
        records: roster.map((student) => ({ student_id: student.student_id, status: status[student.student_id] || "present" })),
      };
      const saved = sessionId ? await updateAttendanceSession(sessionId, body) : await createAttendanceSession(body);
      const savedId = saved.attendance_session_id || Number(sessionId);
      setSessionId(String(savedId));
      setSessions(await listAttendanceSessions(offeringId));
      setMessage(sessionId ? "Attendance session updated." : "Attendance saved.");
    } catch (saveError) {
      setMessage(saveError.message);
    }
  }

  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Mark Attendance</h2>
        <span className="badge">{date}</span>
      </div>
      {error && <p role="alert">{error}</p>}
      {rosterError && <p role="alert">{rosterError}</p>}
      {sessionError && <p role="alert">{sessionError}</p>}
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
        <input type="date" value={date} onChange={(event) => setDate(event.target.value)} aria-label="Attendance date" />
        <select value={sessionId} onChange={(event) => selectSession(event.target.value)} aria-label="Edit existing session">
          <option value="">New session</option>{sessions.map((session) => <option key={session.id} value={session.id}>{session.session_date} · {session.topic || `Session ${session.id}`}</option>)}
        </select>
      </div>
      {loading && <p>Loading courses…</p>}
      {rosterLoading && <p role="status">Loading students for {courses.find((course) => String(course.id) === String(offeringId))?.code || "selected offering"}…</p>}
      {message && <p role="status">{message}</p>}
      {attendanceSummary.length > 0 && <details><summary>Current course attendance summary</summary><div className="table"><div className="table-head"><span>Student</span><span>Attended</span><span>Absent</span><span>Total</span><span>Attendance</span></div>{attendanceSummary.map((row) => <div className="table-row" key={row.student_id}><strong>{row.enrollment_number} · {row.name}</strong><span>{row.attended_sessions}</span><span>{row.absent_sessions}</span><span>{row.total_sessions}</span><span>{row.attendance == null ? "No records" : `${row.attendance}%`}{row.low_attendance ? " · Low" : ""}</span></div>)}</div></details>}
      <div className="table">
        <div className="table-head result-head"><span>Student</span><span>ID</span><span>Status</span></div>
        {roster.map((student) => (
          <div className="table-row result-row" key={student.id}>
            <strong>{student.name}</strong>
            <span>{student.id}</span>
            <div className="attendance-toggle">
              <button type="button" className={status[student.student_id] === "present" ? "toggle-btn present active" : "toggle-btn present"} onClick={() => setStatus({ ...status, [student.student_id]: "present" })}>Present</button>
              <button type="button" className={status[student.student_id] === "absent" ? "toggle-btn absent active" : "toggle-btn absent"} onClick={() => setStatus({ ...status, [student.student_id]: "absent" })}>Absent</button>
            </div>
          </div>
        ))}
      </div>
      <button className="login-btn save-attendance-btn" disabled={!offeringId || !date || !rosterReady || !roster.length} onClick={save}>{sessionId ? "Update Attendance" : "Save Attendance"}</button>
    </section>
  );
}
