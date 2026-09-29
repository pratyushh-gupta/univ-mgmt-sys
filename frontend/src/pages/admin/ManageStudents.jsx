import { useState } from "react";
import { apiRequest } from "../../api/client";
import { createStudent } from "../../api/students";
import useApiData from "../../hooks/useApiData";

const blankForm = () => ({ id: "", name: "", email: "", enrollment_number: "", department_id: "", semester_id: "", admission_year: new Date().getFullYear(), password: "" });

export default function ManageStudents() {
  const [form, setForm] = useState(blankForm);
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [year, setYear] = useState("");
  const [semester, setSemester] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);
  const [historyId, setHistoryId] = useState("");
  const [message, setMessage] = useState("");
  const params = new URLSearchParams({ search, page: String(page), page_size: "25", active_only: String(!includeInactive) });
  if (department) params.set("department_id", department);
  if (year) params.set("academic_year_id", year);
  if (semester) params.set("semester_id", semester);
  const students = useApiData(`/students?${params}` , { initialData: { items: [], total: 0 } });
  const departments = useApiData("/departments", { auth: false });
  const years = useApiData("/academic-years", { auth: false });
  const semesters = useApiData("/semesters", { auth: false });
  const history = useApiData(historyId ? `/students/${encodeURIComponent(historyId)}/history` : "", { enabled: Boolean(historyId) });
  async function add(event) {
    event.preventDefault(); setMessage("");
    try {
      await createStudent({ ...form, department_id: Number(form.department_id), semester_id: form.semester_id ? Number(form.semester_id) : null, admission_year: Number(form.admission_year) });
      setForm(blankForm()); setMessage("Student account created."); await students.refresh();
    } catch (error) { setMessage(error.message); }
  }
  async function toggleActive(row) {
    try { await apiRequest(`/students/${encodeURIComponent(row.user_id)}`, { method: "PATCH", body: { is_active: !row.active } }); await students.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  async function saveSemester(row, value) {
    try { await apiRequest(`/students/${encodeURIComponent(row.user_id)}`, { method: "PATCH", body: { semester_id: value ? Number(value) : null } }); setMessage("Academic assignment updated."); await students.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  return <>
    <section className="panel full"><div className="panel-title"><h2>Create Student Account</h2></div>
      <form className="inline-form" onSubmit={add}>
        <input required placeholder="Login ID" value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} />
        <input required placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input required placeholder="Enrollment Number" value={form.enrollment_number} onChange={(e) => setForm({ ...form, enrollment_number: e.target.value })} />
        <select required value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}><option value="">Department</option>{departments.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <select value={form.semester_id} onChange={(e) => setForm({ ...form, semester_id: e.target.value })}><option value="">No current semester</option>{semesters.data.map((row) => <option key={row.id} value={row.id}>{row.name} · {row.academic_year}</option>)}</select>
        <input required type="number" min="1900" max="2200" aria-label="Admission year" value={form.admission_year} onChange={(e) => setForm({ ...form, admission_year: e.target.value })} />
        <input required type="password" minLength={8} placeholder="Initial password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="login-btn">Add Student</button>
      </form>
    </section>
    <section className="panel full"><div className="panel-title"><h2>Students</h2><span className="badge">{students.data.total || 0} matching</span></div>
      {(message || students.error) && <p role="alert">{message || students.error}</p>}{students.loading && <p>Loading students…</p>}
      <div className="inline-form"><input placeholder="Search name, email or enrollment" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <select value={department} onChange={(e) => { setDepartment(e.target.value); setPage(1); }}><option value="">All departments</option>{departments.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <select value={year} onChange={(e) => { setYear(e.target.value); setPage(1); }}><option value="">All academic years</option>{years.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <select value={semester} onChange={(e) => { setSemester(e.target.value); setPage(1); }}><option value="">All semesters</option>{semesters.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <label><input type="checkbox" checked={includeInactive} onChange={(e) => { setIncludeInactive(e.target.checked); setPage(1); }} /> Include inactive</label>
      </div>
      <div className="table"><div className="table-head"><span>Enrollment</span><span>Name / Login</span><span>Department</span><span>Academic assignment</span><span>Actions</span></div>
        {(students.data.items || []).map((row) => <div className="table-row" key={row.student_id}><span>{row.enrollment_number}<small>Admitted {row.admission_year}</small></span><strong>{row.name}<small>{row.user_id}</small></strong><span>{row.department}</span>
          <select aria-label={`Semester for ${row.name}`} value={row.semester_id || ""} onChange={(e) => saveSemester(row, e.target.value)}><option value="">Unassigned</option>{semesters.data.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.academic_year}</option>)}</select>
          <span><button className="remove-btn" onClick={() => toggleActive(row)}>{row.active ? "Deactivate" : "Activate"}</button><button className="remove-btn" onClick={() => setHistoryId(row.user_id)}>History</button></span></div>)}
      </div>
      <div className="inline-form"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page} · {students.data.total || 0} students</span><button disabled={page * 25 >= (students.data.total || 0)} onClick={() => setPage(page + 1)}>Next</button></div>
    </section>
    {historyId && <section className="panel full"><div className="panel-title"><h2>Academic History</h2><button className="remove-btn" onClick={() => setHistoryId("")}>Close</button></div>{history.error && <p role="alert">{history.error}</p>}{history.loading && <p>Loading…</p>}{history.data.map((row, index) => <p key={`${row.course_code}-${index}`}>{row.academic_year} · {row.semester} · {row.course_code} · {row.credits} credits · {row.status} · {row.results.map((result) => `${result.grade} (${result.assessment_name})`).join(", ")}</p>)}</section>}
  </>;
}
