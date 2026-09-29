import { useState } from "react";
import { createEnrollment } from "../../api/enrollments";
import { apiRequest } from "../../api/client";
import useApiData from "../../hooks/useApiData";

export default function ManageEnrollments() {
  const [offeringId, setOfferingId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const students = useApiData("/students?page_size=100");
  const offerings = useApiData("/course-offerings?page_size=100");
  const enrollments = useApiData(`/enrollments?search=${encodeURIComponent(query)}&page_size=100`, { initialData: { items: [], total: 0 } });
  async function enroll(event) {
    event.preventDefault(); setMessage("");
    try { await createEnrollment({ student_id: Number(studentId), course_offering_id: Number(offeringId) }); setMessage("Student enrolled."); await enrollments.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  async function drop(id) {
    try { await apiRequest(`/enrollments/${id}`, { method: "DELETE" }); setMessage("Enrollment dropped."); await enrollments.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  return <>
    <section className="panel full"><div className="panel-title"><h2>Admin Enrollment</h2></div>{message && <p role="status">{message}</p>}
      <form className="inline-form" onSubmit={enroll}><select required value={studentId} onChange={(e) => setStudentId(e.target.value)}><option value="">Choose active student</option>{(students.data.items || []).map((row) => <option key={row.student_id} value={row.student_id}>{row.enrollment_number} · {row.name}</option>)}</select>
        <select required value={offeringId} onChange={(e) => setOfferingId(e.target.value)}><option value="">Choose offering</option>{(offerings.data.items || []).map((row) => <option key={row.id} value={row.id}>{row.code} · {row.section} · {row.semester}</option>)}</select><button className="login-btn">Enroll student</button></form>
      {students.error && <p role="alert">{students.error}</p>}{offerings.error && <p role="alert">{offerings.error}</p>}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Enrollment History</h2><span className="badge">{enrollments.data.total || 0}</span></div><input placeholder="Search student" value={query} onChange={(e) => setQuery(e.target.value)} />{enrollments.error && <p role="alert">{enrollments.error}</p>}
      <div className="table"><div className="table-head"><span>Student</span><span>Course</span><span>Enrolled</span><span>Status</span><span /></div>{(enrollments.data.items || []).map((row) => <div className="table-row" key={row.id}><strong>{row.student}</strong><span>{row.course_code}</span><span>{row.enrolled_at.slice(0, 10)}</span><span>{row.status}</span>{row.status === "active" && <button className="remove-btn" onClick={() => drop(row.id)}>Drop</button>}</div>)}</div>
    </section>
  </>;
}
