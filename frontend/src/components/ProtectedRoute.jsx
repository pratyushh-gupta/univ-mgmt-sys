import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
export default function ProtectedRoute({ allowedRole, children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="panel">Checking your session…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== allowedRole) return <Navigate to={`/${user.role}`} replace />;
  return children;
}
