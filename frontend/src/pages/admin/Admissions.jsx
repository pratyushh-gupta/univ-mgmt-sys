import { useState } from "react";
import { createAdmission, reviewAdmission } from "../../api/admissions";
import useApiData from "../../hooks/useApiData";

const emptyApplication = () => ({ applicant_name: "", email: "", phone: "", address: "", department_id: "", academic_year_id: "", intended_program: "" });

export default function Admissions() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [form, setForm] = useState(emptyApplication);
  const [selected, setSelected] = useState(null);
  const [credentials, setCredentials] = useState({ user_id: "", initial_password: "", enrollment_number: "", semester_id: "" });
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const query = new URLSearchParams({ search, ...(status ? { status } : {}) }).toString();
  const applications = useApiData(`/admin/admissions?${query}`, { initialData: { items: [], total: 0 } });
  const departments = useApiData("/departments", { auth: false });
  const years = useApiData("/academic-years", { auth: false });
  const semesters = useApiData("/semesters", { auth: false });
  const selectedApplication = applications.data.items?.find((row) => row.id === Number(selected));
  async function submit(event) {
    event.preventDefault(); setMessage("");
    try {
      await createAdmission({ ...form, department_id: Number(form.department_id), academic_year_id: Number(form.academic_year_id) });
      setForm(emptyApplication()); setMessage("Application created."); await applications.refresh();
    } catch (error) { setMessage(error.message); }
  }
  async function review(nextStatus) {
    if (!selectedApplication) return;
    setMessage("");
    const body = nextStatus === "approved"
      ? { status: nextStatus, ...credentials, semester_id: Number(credentials.semester_id) }
      : { status: nextStatus, rejection_reason: reason };
    try {
      await reviewAdmission(selectedApplication.id, body);
      setMessage(`Application ${nextStatus}.`); setSelected(null); setCredentials({ user_id: "", initial_password: "", enrollment_number: "", semester_id: "" }); setReason(""); await applications.refresh();
    } catch (error) { setMessage(error.message); }
  }
  return <>
    <section className="panel full"><div className="panel-title"><h2>Create Admission Application</h2></div>
      <form className="inline-form" onSubmit={submit}>
        <input required placeholder="Applicant name" value={form.applicant_name} onChange={(e) => setForm({ ...form, applicant_name: e.target.value })} />
        <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <input required placeholder="Intended program" value={form.intended_program} onChange={(e) => setForm({ ...form, intended_program: e.target.value })} />
        <select required value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}><option value="">Department</option>{departments.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <select required value={form.academic_year_id} onChange={(e) => setForm({ ...form, academic_year_id: e.target.value })}><option value="">Academic year</option>{years.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <input placeholder="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
        <button className="login-btn">Create application</button>
      </form>
    </section>
    <section className="panel full"><div className="panel-title"><h2>Applications</h2><span className="badge">{applications.data.total || 0}</span></div>
      {message && <p role="status">{message}</p>}{applications.error && <p role="alert">{applications.error}</p>}
      <div className="inline-form"><input placeholder="Search name or email" value={search} onChange={(e) => setSearch(e.target.value)} /><select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option>{["submitted", "under_review", "approved", "rejected", "withdrawn"].map((value) => <option key={value}>{value}</option>)}</select></div>
      {applications.loading && <p>Loading applications…</p>}
      <div className="table"><div className="table-head"><span>Applicant</span><span>Program</span><span>Department / Year</span><span>Status</span><span /></div>
        {(applications.data.items || []).map((row) => <div className="table-row" key={row.id}><strong>{row.applicant_name}<small>{row.email}</small></strong><span>{row.intended_program}</span><span>{row.department} · {row.academic_year}</span><span>{row.status}</span><button className="remove-btn" disabled={!['submitted', 'under_review'].includes(row.status)} onClick={() => setSelected(row.id)}>Review</button></div>)}
      </div>
    </section>
    {selectedApplication && <section className="panel full"><div className="panel-title"><h2>Review {selectedApplication.applicant_name}</h2></div>
      <p>{selectedApplication.email} · {selectedApplication.intended_program}</p>
      <div className="inline-form"><input placeholder="New student login ID" value={credentials.user_id} onChange={(e) => setCredentials({ ...credentials, user_id: e.target.value })} />
        <input type="password" minLength={12} placeholder="Initial password (12+ characters)" value={credentials.initial_password} onChange={(e) => setCredentials({ ...credentials, initial_password: e.target.value })} />
        <input placeholder="Enrollment number (optional)" value={credentials.enrollment_number} onChange={(e) => setCredentials({ ...credentials, enrollment_number: e.target.value })} />
        <select value={credentials.semester_id} onChange={(e) => setCredentials({ ...credentials, semester_id: e.target.value })}><option value="">Choose semester</option>{semesters.data.filter((row) => row.academic_year_id === selectedApplication.academic_year_id).map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <button className="login-btn" disabled={!credentials.user_id || credentials.initial_password.length < 12 || !credentials.semester_id} onClick={() => review("approved")}>Approve and create student</button>
      </div>
      <div className="inline-form"><input placeholder="Rejection reason" value={reason} onChange={(e) => setReason(e.target.value)} /><button className="remove-btn" disabled={!reason.trim()} onClick={() => review("rejected")}>Reject</button><button className="remove-btn" onClick={() => review("under_review")}>Mark under review</button><button className="remove-btn" onClick={() => setSelected(null)}>Close</button></div>
    </section>}
  </>;
}
