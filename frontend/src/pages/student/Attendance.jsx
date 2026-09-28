import { studentCourses } from "../../data/mockData";

export default function Attendance() {
  const overall = Math.round(
    studentCourses.reduce((sum, c) => sum + c.attendance, 0) / studentCourses.length
  );

  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Attendance Overview</h2>
        <span className="overall">Overall: {overall}%</span>
      </div>

      {studentCourses.map((c) => (
        <div className="attendance" key={c.code}>
          <div className="attendance-top">
            <strong>{c.name}</strong>
            <span>{c.attendance}%</span>
          </div>

          <div className="progress">
            <div className="progress-fill" style={{ width: `${c.attendance}%` }}></div>
          </div>
        </div>
      ))}
    </section>
  );
}
