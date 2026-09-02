import { useState } from "react";
import "./index.css";

function App() {
  const [page, setPage] = useState("Dashboard");
  const [loggedIn, setLoggedIn] = useState(false);

  if (!loggedIn) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="logo">🎓</div>
          <h1>University Portal</h1>
          <p className="login-subtitle">
            Online University Management System
          </p>

          <div className="input-group">
            <label>Student ID</label>
            <input placeholder="Enter Student ID" />
          </div>

          <div className="input-group">
            <label>Password</label>
            <input type="password" placeholder="Enter Password" />
          </div>

          <button
            className="login-btn"
            onClick={() => setLoggedIn(true)}
          >
            Login
          </button>

          <p className="demo-text">
            Demo: Enter any ID and password
          </p>
        </div>
      </div>
    );
  }

  const menu = [
    "Dashboard",
    "My Courses",
    "Attendance",
    "Results",
    "Assignments",
    "Notices",
    "Profile",
  ];

  return (
    <div className="app">

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <span>🎓</span>
          <div>
            <h2>UniPortal</h2>
            <small>Student Portal</small>
          </div>
        </div>

        <nav>
          {menu.map((item) => (
            <button
              key={item}
              className={page === item ? "nav-item active" : "nav-item"}
              onClick={() => setPage(item)}
            >
              {item === "Dashboard" && "🏠"}
              {item === "My Courses" && "📚"}
              {item === "Attendance" && "📊"}
              {item === "Results" && "📝"}
              {item === "Assignments" && "📋"}
              {item === "Notices" && "🔔"}
              {item === "Profile" && "👤"}
              <span>{item}</span>
            </button>
          ))}
        </nav>

        <button className="logout" onClick={() => setLoggedIn(false)}>
          🚪 Logout
        </button>
      </aside>

      {/* MAIN */}
      <main className="main">

        {/* TOP BAR */}
        <header className="topbar">
          <div>
            <h1>{page}</h1>
            <p>Welcome back, Harry 👋</p>
          </div>

          <div className="student-mini">
            <div className="avatar">HK</div>
            <div>
              <strong>Harry Kumar</strong>
              <small>Computer Science</small>
            </div>
          </div>
        </header>

        {/* CONTENT */}
        {page === "Dashboard" && <Dashboard />}
        {page === "My Courses" && <Courses />}
        {page === "Attendance" && <Attendance />}
        {page === "Results" && <Results />}
        {page === "Assignments" && <Assignments />}
        {page === "Notices" && <Notices />}
        {page === "Profile" && <Profile />}

      </main>
    </div>
  );
}


/* DASHBOARD */

function Dashboard() {
  return (
    <>
      <section className="welcome">
        <div>
          <h2>Good Morning, Harry! 👋</h2>
          <p>
            Here's what's happening with your academic progress.
          </p>
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

          <Class
            time="09:00 AM"
            subject="Operating Systems"
            room="Room 204"
          />

          <Class
            time="11:00 AM"
            subject="Software Engineering"
            room="Lab 3"
          />

          <Class
            time="02:00 PM"
            subject="Database Management"
            room="Room 105"
          />
        </section>

        <section className="panel">
          <div className="panel-title">
            <h2>Recent Notices</h2>
            <button>View All</button>
          </div>

          <div className="notice">
            <div className="notice-dot"></div>
            <div>
              <strong>Mid-Semester Examination</strong>
              <p>Examination schedule has been published.</p>
              <small>Today</small>
            </div>
          </div>

          <div className="notice">
            <div className="notice-dot"></div>
            <div>
              <strong>Project Submission</strong>
              <p>Submit your project before Friday.</p>
              <small>Yesterday</small>
            </div>
          </div>
        </section>

      </div>
    </>
  );
}


function Class({ time, subject, room }) {
  return (
    <div className="class-row">
      <div className="class-time">{time}</div>
      <div className="class-info">
        <strong>{subject}</strong>
        <span>{room}</span>
      </div>
      <span className="class-status">Upcoming</span>
    </div>
  );
}


/* COURSES */

function Courses() {
  const courses = [
    ["CS401", "Operating Systems", "Dr. Sharma", "85%"],
    ["CS402", "Database Management", "Prof. Singh", "92%"],
    ["CS403", "Software Engineering", "Dr. Verma", "88%"],
    ["CS404", "Computer Networks", "Prof. Gupta", "79%"],
    ["CS405", "Web Technologies", "Dr. Mehta", "91%"],
    ["CS406", "Data Structures", "Prof. Roy", "83%"],
  ];

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

        {courses.map((course) => (
          <div className="table-row" key={course[0]}>
            <span>{course[0]}</span>
            <strong>{course[1]}</strong>
            <span>{course[2]}</span>
            <span className="green-text">{course[3]}</span>
          </div>
        ))}
      </div>
    </section>
  );
}


/* ATTENDANCE */

function Attendance() {
  const subjects = [
    ["Operating Systems", 85],
    ["Database Management", 92],
    ["Software Engineering", 88],
    ["Computer Networks", 79],
    ["Web Technologies", 91],
    ["Data Structures", 83],
  ];

  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Attendance Overview</h2>
        <span className="overall">Overall: 86%</span>
      </div>

      {subjects.map(([name, percentage]) => (
        <div className="attendance" key={name}>
          <div className="attendance-top">
            <strong>{name}</strong>
            <span>{percentage}%</span>
          </div>

          <div className="progress">
            <div
              className="progress-fill"
              style={{ width: `${percentage}%` }}
            ></div>
          </div>
        </div>
      ))}
    </section>
  );
}


/* RESULTS */

function Results() {
  const results = [
    ["Operating Systems", "A", "9"],
    ["Database Management", "A+", "10"],
    ["Software Engineering", "A", "9"],
    ["Computer Networks", "B+", "8"],
    ["Web Technologies", "A+", "10"],
    ["Data Structures", "A", "9"],
  ];

  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Academic Results</h2>
        <span className="overall">CGPA: 8.42</span>
      </div>

      <div className="table">
        <div className="table-head result-head">
          <span>Subject</span>
          <span>Grade</span>
          <span>Grade Point</span>
        </div>

        {results.map((result) => (
          <div className="table-row result-row" key={result[0]}>
            <strong>{result[0]}</strong>
            <span className="grade">{result[1]}</span>
            <span>{result[2]}</span>
          </div>
        ))}
      </div>
    </section>
  );
}


/* ASSIGNMENTS */

function Assignments() {
  return (
    <div className="cards">

      <Assignment
        title="Operating Systems Assignment"
        subject="Operating Systems"
        due="September 5, 2026"
        status="Pending"
      />

      <Assignment
        title="University Management System"
        subject="Software Engineering"
        due="September 7, 2026"
        status="Pending"
      />

      <Assignment
        title="Database Normalization"
        subject="Database Management"
        due="September 10, 2026"
        status="Submitted"
      />

    </div>
  );
}


function Assignment({ title, subject, due, status }) {
  return (
    <div className="assignment-card">
      <div className="assignment-icon">📄</div>
      <h3>{title}</h3>
      <p>{subject}</p>

      <div className="assignment-bottom">
        <span>Due: {due}</span>
        <span className={status === "Submitted" ? "submitted" : "pending"}>
          {status}
        </span>
      </div>
    </div>
  );
}


/* NOTICES */

function Notices() {
  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>University Notices</h2>
      </div>

      <div className="large-notice">
        <h3>📢 Mid-Semester Examination Schedule</h3>
        <p>
          The mid-semester examination schedule has been published.
          Students are requested to check the examination portal.
        </p>
        <small>September 2, 2026</small>
      </div>

      <div className="large-notice">
        <h3>📢 Project Submission Deadline</h3>
        <p>
          All students must submit their Software Engineering project
          before the deadline.
        </p>
        <small>September 1, 2026</small>
      </div>

      <div className="large-notice">
        <h3>📢 Library Timing Updated</h3>
        <p>
          The university library will remain open until 8:00 PM
          during examination preparation.
        </p>
        <small>August 30, 2026</small>
      </div>
    </section>
  );
}


/* PROFILE */

function Profile() {
  return (
    <section className="profile-card">

      <div className="profile-header">
        <div className="profile-avatar">HK</div>
        <div>
          <h2>Harry Kumar</h2>
          <p>Student ID: 2024CS1042</p>
        </div>
      </div>

      <div className="profile-details">
        <div>
          <span>Department</span>
          <strong>Computer Science & Engineering</strong>
        </div>

        <div>
          <span>Semester</span>
          <strong>4th Semester</strong>
        </div>

        <div>
          <span>Email</span>
          <strong>harry@university.edu</strong>
        </div>

        <div>
          <span>Phone</span>
          <strong>+91 98765 43210</strong>
        </div>
      </div>

    </section>
  );
}

export default App;