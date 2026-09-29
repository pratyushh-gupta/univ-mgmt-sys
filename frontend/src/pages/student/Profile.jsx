import useApiData from "../../hooks/useApiData";

export default function Profile() {
  const { data: profile, loading, error } = useApiData("/student/profile", { initialData: {} });
  const initials = profile.name?.split(" ").map((word) => word[0]).join("").slice(0, 2).toUpperCase();
  return <section className="profile-card">
    {loading && <p>Loading profile…</p>}{error && <p role="alert">{error}</p>}
    {!loading && !error && <>
      <div className="profile-header"><div className="profile-avatar">{initials}</div><div><h2>{profile.name}</h2><p>Enrollment Number: {profile.enrollment_number}</p></div></div>
      <div className="profile-details"><div><span>Department</span><strong>{profile.department}</strong></div>
        <div><span>Semester</span><strong>{profile.semester ? `Semester ${profile.semester}` : "Not provided"}</strong></div>
        <div><span>Email</span><strong>{profile.email}</strong></div><div><span>Admission Year</span><strong>{profile.admission_year}</strong></div>
        <div><span>Phone</span><strong>{profile.phone || "Not provided"}</strong></div><div><span>Address</span><strong>{profile.address || "Not provided"}</strong></div>
      </div>
    </>}
  </section>;
}
