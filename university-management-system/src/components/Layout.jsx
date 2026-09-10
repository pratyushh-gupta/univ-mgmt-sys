import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Reusable dashboard shell used by Admin, Faculty and Student areas.
 * `menu` = [{ to, label, icon, end }]
 */
export default function Layout({ menu, brandLabel, pageTitle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials = user?.name
    ?.split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span>🎓</span>
          <div>
            <h2>UniPortal</h2>
            <small>{brandLabel}</small>
          </div>
        </div>

        <nav>
          {menu.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? "nav-item active" : "nav-item"
              }
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <button className="logout" onClick={handleLogout}>
          🚪 Logout
        </button>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>{pageTitle}</h1>
            <p>Welcome back, {user?.name?.split(" ")[0]} 👋</p>
          </div>

          <div className="student-mini">
            <div className="avatar">{initials}</div>
            <div>
              <strong>{user?.name}</strong>
              <small>{user?.department || user?.role}</small>
            </div>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
