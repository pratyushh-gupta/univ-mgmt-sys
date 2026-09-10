import { useAuth } from "../../context/AuthContext";
import { todaysClasses, notices } from "../../data/mockData";

export default function StudentHome() {
  const { user } = useAuth();

  return (
    <>
      <section className="welcome">
        <div>
          <h2>Good Morning, {user?.name?.split(" ")[0]}! 👋</h2>
          <p>Here's what's happening with your academic progress.</p>
        </div>
        <div className="semester">
          <span>Current Semester</span>
          <strong>Semester 4</strong>
        </div>
      </section>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-icon blue">📚</div>
          <div>
            <span>Total Courses</span>
            <h2>6</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">📊</div>
          <div>
            <span>Attendance</span>
            <h2>86%</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">⭐</div>
          <div>
            <span>Current CGPA</span>
            <h2>8.42</h2>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">📋</div>
          <div>
            <span>Assignments</span>
            <h2>4</h2>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-title">
            <h2>Today's Classes</h2>
            <button>View All</button>
          </div>

          {todaysClasses.map((c) => (
            <div className="class-row" key={c.subject}>
              <div className="class-time">{c.time}</div>
              <div className="class-info">
                <strong>{c.subject}</strong>
                <span>{c.room}</span>
              </div>
              <span className="class-status">Upcoming</span>
            </div>
          ))}
        </section>

        <section className="panel">
          <div className="panel-title">
            <h2>Recent Notices</h2>
            <button>View All</button>
          </div>

          {notices.map((n) => (
            <div className="notice" key={n.title}>
              <div className="notice-dot"></div>
              <div>
                <strong>{n.title}</strong>
                <p>{n.body}</p>
                <small>{n.date}</small>
              </div>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}
