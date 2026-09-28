import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Wraps a role's routes. Redirects to /login if not logged in,
 * or if the logged-in user's role doesn't match this section.
 */
export default function ProtectedRoute({ allowedRole, children }) {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== allowedRole) return <Navigate to={`/${user.role}`} replace />;

  return children;
}
