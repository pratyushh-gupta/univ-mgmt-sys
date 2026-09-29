import { createContext, useContext, useEffect, useState } from "react";
import { apiRequest } from "../api/client";
import { loginRequest } from "../api/auth";
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem("access_token")));
  useEffect(() => {
    const clearSession = () => setUser(null);
    window.addEventListener("auth:unauthorized", clearSession);
    return () => window.removeEventListener("auth:unauthorized", clearSession);
  }, []);
  useEffect(() => {
    if (!localStorage.getItem("access_token")) return;
    apiRequest("/auth/me").then(setUser).catch(() => { localStorage.removeItem("access_token"); setUser(null); }).finally(() => setLoading(false));
  }, []);
  async function login(userId, password) {
    const result = await loginRequest(userId, password);
    localStorage.setItem("access_token", result.access_token);
    setUser(result.user);
    return result.user;
  }
  function logout() { localStorage.removeItem("access_token"); setUser(null); }
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() { const ctx = useContext(AuthContext); if (!ctx) throw new Error("useAuth must be used inside AuthProvider"); return ctx; }
