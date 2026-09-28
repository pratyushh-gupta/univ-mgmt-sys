import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

// Demo users. Jab FastAPI backend connect hoga, ye login() function
// asli /auth/login API call karega aur JWT token store karega.
const DEMO_USERS = {
  admin: { name: "Admin User", role: "admin" },
  faculty: { name: "Dr. Sharma", role: "faculty", department: "Computer Science" },
  student: { name: "Prem Kumar", role: "student", studentId: "2024CS1042", department: "Computer Science" },
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  // role: "admin" | "faculty" | "student"
  function login(role) {
    setUser(DEMO_USERS[role] || DEMO_USERS.student);
  }

  function logout() {
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
