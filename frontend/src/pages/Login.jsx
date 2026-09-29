import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiErrorMessage } from "../api/client";
export default function Login() {
  const [role, setRole] = useState("student");
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login, user, loading } = useAuth(); const navigate = useNavigate();
  useEffect(() => { if (!loading && user) navigate(`/${user.role}`, { replace: true }); }, [loading, user, navigate]);
  async function handleLogin(e) {
    e.preventDefault(); setError(""); setSubmitting(true);
    try { const user = await login(userId, password); navigate(`/${user.role}`, { replace: true }); }
    catch (err) { setError(apiErrorMessage(err)); }
    finally { setSubmitting(false); }
  }
  return <div className="login-page"><div className="login-card"><div className="logo">🎓</div><h1>University Portal</h1><p className="login-subtitle">Online University Management System</p>
    <div className="input-group"><label>Login as</label><div className="role-switch">{["student", "faculty", "admin"].map((r) => <button type="button" key={r} className={role === r ? "role-btn active" : "role-btn"} onClick={() => setRole(r)}>{r === "student" ? "🎒" : r === "faculty" ? "🧑‍🏫" : "🛡️"}<span>{r[0].toUpperCase() + r.slice(1)}</span></button>)}</div></div>
    <form onSubmit={handleLogin}><div className="input-group"><label htmlFor="user-id">{role === "student" ? "Student ID" : "User ID"}</label><input id="user-id" required value={userId} onChange={(e) => setUserId(e.target.value)} placeholder={`Enter your ${role === "student" ? "Student ID" : "User ID"}`} /></div>
    <div className="input-group"><label htmlFor="password">Password</label><input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter Password" /></div>
    {error && <p role="alert" className="error-message">{error}</p>}<button className="login-btn" type="submit" disabled={submitting}>{submitting ? "Signing in…" : `Login as ${role[0].toUpperCase() + role.slice(1)}`}</button></form>
  </div></div>;
}
