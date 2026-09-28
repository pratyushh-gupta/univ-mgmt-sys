import { studentCourses } from "../../data/mockData";

export default function Courses() {
  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>My Courses</h2>
        <span className="badge">Semester 4</span>
      </div>

      <div className="table">
        <div className="table-head">
          <span>Course Code</span>
          <span>Course Name</span>
          <span>Faculty</span>
          <span>Attendance</span>
        </div>

        {studentCourses.map((c) => (
          <div className="table-row" key={c.code}>
            <span>{c.code}</span>
            <strong>{c.name}</strong>
            <span>{c.faculty}</span>
            <span className="green-text">{c.attendance}%</span>
          </div>
        ))}
      </div>
    </section>
  );
}
