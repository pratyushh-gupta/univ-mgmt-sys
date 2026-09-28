import { allStudents, allFaculty, allCourses } from "../../data/mockData";

export default function AdminHome() {
  return (
    <>
      <section className="welcome">
        <div>
          <h2>University Overview 🏛️</h2>
          <p>Manage students, faculty and courses from one place.</p>
        </div>
        <div className="semester">
          <span>Academic Year</span>
          <strong>2026 - 27</strong>
        </div>
      </section>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-icon blue">🎒</div>
          <div>
            <span>Total Students</span>
            <h2>{allStudents.length}</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">🧑‍🏫</div>
          <div>
            <span>Total Faculty</span>
            <h2>{allFaculty.length}</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">📚</div>
          <div>
            <span>Active Courses</span>
            <h2>{allCourses.length}</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">🏫</div>
          <div>
            <span>Departments</span>
            <h2>3</h2>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-title">
            <h2>Recently Added Students</h2>
            <button>View All</button>
          </div>

          {allStudents.slice(0, 3).map((s) => (
            <div className="class-row" key={s.id}>
              <div className="class-info">
                <strong>{s.name}</strong>
                <span>{s.department} · Sem {s.semester}</span>
              </div>
              <span className="class-status">{s.id}</span>
            </div>
          ))}
        </section>

        <section className="panel">
          <div className="panel-title">
            <h2>Faculty</h2>
            <button>View All</button>
          </div>

          {allFaculty.map((f) => (
            <div className="notice" key={f.id}>
              <div className="notice-dot"></div>
              <div>
                <strong>{f.name}</strong>
                <p>{f.subject}</p>
                <small>{f.department}</small>
              </div>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}
