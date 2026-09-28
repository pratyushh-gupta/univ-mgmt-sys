import { useState } from "react";
import { allFaculty } from "../../data/mockData";

export default function ManageFaculty() {
  const [faculty, setFaculty] = useState(allFaculty);
  const [form, setForm] = useState({ id: "", name: "", department: "", subject: "", email: "" });

  function handleAdd(e) {
    e.preventDefault();
    if (!form.id || !form.name) return;
    // TODO: FastAPI POST /faculty yahan call hoga.
    setFaculty([...faculty, form]);
    setForm({ id: "", name: "", department: "", subject: "", email: "" });
  }

  function handleRemove(id) {
    // TODO: FastAPI DELETE /faculty/{id} yahan call hoga.
    setFaculty(faculty.filter((f) => f.id !== id));
  }

  return (
    <>
      <section className="panel full">
        <div className="panel-title">
          <h2>Add New Faculty</h2>
        </div>

        <form className="inline-form" onSubmit={handleAdd}>
          <input
            placeholder="Faculty ID"
            value={form.id}
            onChange={(e) => setForm({ ...form, id: e.target.value })}
          />
          <input
            placeholder="Full Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <input
            placeholder="Department"
            value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })}
          />
          <input
            placeholder="Subject"
            value={form.subject}
            onChange={(e) => setForm({ ...form, subject: e.target.value })}
          />
          <input
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <button className="login-btn" type="submit">Add Faculty</button>
        </form>
      </section>

      <section className="panel full">
        <div className="panel-title">
          <h2>All Faculty</h2>
          <span className="badge">{faculty.length} total</span>
        </div>

        <div className="table">
          <div className="table-head admin-table-head">
            <span>ID</span>
            <span>Name</span>
            <span>Department</span>
            <span>Subject</span>
            <span></span>
          </div>

          {faculty.map((f) => (
            <div className="table-row admin-table-row" key={f.id}>
              <span>{f.id}</span>
              <strong>{f.name}</strong>
              <span>{f.department}</span>
              <span>{f.subject}</span>
              <button className="remove-btn" onClick={() => handleRemove(f.id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
