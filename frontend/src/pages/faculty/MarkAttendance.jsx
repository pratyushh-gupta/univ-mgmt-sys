import { useState } from "react";
import { facultyCourseRoster } from "../../data/mockData";

export default function MarkAttendance() {
  const [status, setStatus] = useState(
    Object.fromEntries(facultyCourseRoster.map((s) => [s.id, "present"]))
  );

  function toggle(id, value) {
    setStatus({ ...status, [id]: value });
  }

  function handleSave() {
    // TODO: FastAPI POST /attendance yahan call hoga: { course_id, date, status }
    alert("Attendance saved (demo only — backend jab ready hoga tab yeh save hoga).");
  }

  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Mark Attendance — Operating Systems</h2>
        <span className="badge">{new Date().toLocaleDateString()}</span>
      </div>

      <div className="table">
        <div className="table-head result-head">
          <span>Student</span>
          <span>ID</span>
          <span>Status</span>
        </div>

        {facultyCourseRoster.map((s) => (
          <div className="table-row result-row" key={s.id}>
            <strong>{s.name}</strong>
            <span>{s.id}</span>
            <div className="attendance-toggle">
              <button
                type="button"
                className={status[s.id] === "present" ? "toggle-btn present active" : "toggle-btn present"}
                onClick={() => toggle(s.id, "present")}
              >
                Present
              </button>
              <button
                type="button"
                className={status[s.id] === "absent" ? "toggle-btn absent active" : "toggle-btn absent"}
                onClick={() => toggle(s.id, "absent")}
              >
                Absent
              </button>
            </div>
          </div>
        ))}
      </div>

      <button className="login-btn save-attendance-btn" onClick={handleSave}>
        Save Attendance
      </button>
    </section>
  );
}
