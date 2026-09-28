import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [role, setRole] = useState("student");
  const { login } = useAuth();
  const navigate = useNavigate();

  function handleLogin(e) {
    e.preventDefault();
    // TODO: FastAPI /auth/login ko call karo yahan, JWT token save karo.
    login(role);
    navigate(`/${role}`);
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="logo">🎓</div>
        <h1>University Portal</h1>
        <p className="login-subtitle">Online University Management System</p>

        <div className="input-group">
          <label>Login as</label>
          <div className="role-switch">
            {["student", "faculty", "admin"].map((r) => (
              <button
                type="button"
                key={r}
                className={role === r ? "role-btn active" : "role-btn"}
                onClick={() => setRole(r)}
              >
                {r === "student" && "🎒"}
                {r === "faculty" && "🧑‍🏫"}
                {r === "admin" && "🛡️"}
                <span>{r[0].toUpperCase() + r.slice(1)}</span>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label>{role === "student" ? "Student ID" : "User ID"}</label>
            <input placeholder={`Enter your ${role === "student" ? "Student ID" : "User ID"}`} />
          </div>

          <div className="input-group">
            <label>Password</label>
            <input type="password" placeholder="Enter Password" />
          </div>

          <button className="login-btn" type="submit">
            Login as {role[0].toUpperCase() + role.slice(1)}
          </button>
        </form>

        <p className="demo-text">Demo: Enter any ID and password</p>
      </div>
    </div>
  );
}
