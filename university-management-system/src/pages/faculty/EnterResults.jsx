import { useState } from "react";
import { facultyCourseRoster } from "../../data/mockData";

export default function EnterResults() {
  const [marks, setMarks] = useState(
    Object.fromEntries(facultyCourseRoster.map((s) => [s.id, s.marks]))
  );

  function handleChange(id, value) {
    setMarks({ ...marks, [id]: value });
  }

  function handleSave() {
    // TODO: FastAPI POST /results yahan call hoga: { course_id, student_id, marks }
    alert("Marks saved (demo only — backend jab ready hoga tab yeh save hoga).");
  }

  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Enter Results — Operating Systems</h2>
      </div>

      <div className="table">
        <div className="table-head result-head">
          <span>Student</span>
          <span>ID</span>
          <span>Marks (out of 100)</span>
        </div>

        {facultyCourseRoster.map((s) => (
          <div className="table-row result-row" key={s.id}>
            <strong>{s.name}</strong>
            <span>{s.id}</span>
            <input
              type="number"
              min="0"
              max="100"
              className="marks-input"
              value={marks[s.id]}
              onChange={(e) => handleChange(s.id, e.target.value)}
            />
          </div>
        ))}
      </div>

      <button className="login-btn save-attendance-btn" onClick={handleSave}>
        Save Results
      </button>
    </section>
  );
}
