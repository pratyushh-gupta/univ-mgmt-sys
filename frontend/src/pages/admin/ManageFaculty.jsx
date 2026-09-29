import { useState } from "react";
import { createFaculty, deactivateFaculty } from "../../api/faculty";
import useApiData from "../../hooks/useApiData";

const blankForm = () => ({ id: "", employee_id: "", name: "", email: "", department_id: "", designation: "", password: "" });

export default function ManageFaculty() {
  const { data: faculty, setData, loading, error, refresh } = useApiData("/faculty");
  const { data: departments, loading: departmentsLoading } = useApiData("/departments", { auth: false });
  const [form, setForm] = useState(blankForm);
  const [message, setMessage] = useState("");

  async function add(event) {
    event.preventDefault();
    setMessage("");
    try {
      const person = await createFaculty({ ...form, department_id: Number(form.department_id) });
      setData([...faculty, person]);
      setForm(blankForm());
    } catch (requestError) { setMessage(requestError.message); }
  }

  async function remove(id) {
    try { await deactivateFaculty(id); refresh(); }
    catch (requestError) { setMessage(requestError.message); }
  }

  return <>
    <section className="panel full">
      <div className="panel-title"><h2>Add Faculty Account</h2></div>
      <form className="inline-form" onSubmit={add}>
        <input required placeholder="Login ID" value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} />
        <input required placeholder="Employee ID" value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })} />
        <input required placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <select required aria-label="Department" value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}>
          <option value="">{departmentsLoading ? "Loading departments…" : "Select department"}</option>
          {departments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
        </select>
        <input placeholder="Designation" value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} />
        <input required type="password" minLength={8} placeholder="Initial Password (8+ characters)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="login-btn" type="submit" disabled={!departments.length}>Add Faculty</button>
      </form>
    </section>
    <section className="panel full">
      <div className="panel-title"><h2>Faculty</h2><span className="badge">{faculty.length} active</span></div>
      {(error || message) && <p role="alert">{message || error}</p>}{loading && <p>Loading faculty…</p>}
      <div className="table"><div className="table-head admin-table-head"><span>Employee ID</span><span>Name</span><span>Department</span><span>Email</span><span /></div>
        {faculty.map((person) => <div className="table-row admin-table-row" key={person.faculty_id}>
          <span>{person.employee_id}</span><strong>{person.name}</strong><span>{person.department}</span><span>{person.email}</span>
          <button className="remove-btn" onClick={() => remove(person.user_id)}>Deactivate</button>
        </div>)}
      </div>
    </section>
  </>;
}
