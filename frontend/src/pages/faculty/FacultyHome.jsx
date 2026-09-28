import { useAuth } from "../../context/AuthContext";
import { facultyCourseRoster } from "../../data/mockData";

export default function FacultyHome() {
  const { user } = useAuth();
  const avgAttendance = Math.round(
    facultyCourseRoster.reduce((sum, s) => sum + s.attendance, 0) / facultyCourseRoster.length
  );

  return (
    <>
      <section className="welcome">
        <div>
          <h2>Welcome, {user?.name}! 🧑‍🏫</h2>
          <p>Here's an overview of your classes today.</p>
        </div>
        <div className="semester">
          <span>Department</span>
          <strong>{user?.department}</strong>
        </div>
      </section>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-icon blue">📚</div>
          <div>
            <span>Courses Teaching</span>
            <h2>3</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">🎒</div>
          <div>
            <span>Total Students</span>
            <h2>{facultyCourseRoster.length}</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">📊</div>
          <div>
            <span>Avg. Attendance</span>
            <h2>{avgAttendance}%</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">📝</div>
          <div>
            <span>Pending Grading</span>
            <h2>2</h2>
          </div>
        </div>
      </div>

      <section className="panel full">
        <div className="panel-title">
          <h2>Class Roster Snapshot</h2>
          <span className="overall">Operating Systems</span>
        </div>

        <div className="table">
          <div className="table-head result-head">
            <span>Student</span>
            <span>Attendance</span>
            <span>Marks</span>
          </div>

          {facultyCourseRoster.map((s) => (
            <div className="table-row result-row" key={s.id}>
              <strong>{s.name}</strong>
              <span className="green-text">{s.attendance}%</span>
              <span>{s.marks}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
