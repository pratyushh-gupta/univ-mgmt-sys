import { useAuth } from "../../context/AuthContext";

export default function Profile() {
  const { user } = useAuth();
  const initials = user?.name
    ?.split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <section className="profile-card">
      <div className="profile-header">
        <div className="profile-avatar">{initials}</div>
        <div>
          <h2>{user?.name}</h2>
          <p>Student ID: {user?.studentId}</p>
        </div>
      </div>

      <div className="profile-details">
        <div>
          <span>Department</span>
          <strong>{user?.department}</strong>
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
