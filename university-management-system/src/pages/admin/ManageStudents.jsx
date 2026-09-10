import { useState } from "react";
import { allStudents } from "../../data/mockData";

export default function ManageStudents() {
  const [students, setStudents] = useState(allStudents);
  const [form, setForm] = useState({ id: "", name: "", department: "", semester: "", email: "" });

  function handleAdd(e) {
    e.preventDefault();
    if (!form.id || !form.name) return;
    // TODO: FastAPI POST /students yahan call hoga.
    setStudents([...students, { ...form, semester: Number(form.semester) || 1 }]);
    setForm({ id: "", name: "", department: "", semester: "", email: "" });
  }

  function handleRemove(id) {
    // TODO: FastAPI DELETE /students/{id} yahan call hoga.
    setStudents(students.filter((s) => s.id !== id));
  }

  return (
    <>
      <section className="panel full">
        <div className="panel-title">
          <h2>Add New Student</h2>
        </div>

        <form className="inline-form" onSubmit={handleAdd}>
          <input
            placeholder="Student ID"
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
            placeholder="Semester"
            type="number"
            value={form.semester}
            onChange={(e) => setForm({ ...form, semester: e.target.value })}
          />
          <input
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <button className="login-btn" type="submit">Add Student</button>
        </form>
      </section>

      <section className="panel full">
        <div className="panel-title">
          <h2>All Students</h2>
          <span className="badge">{students.length} total</span>
        </div>

        <div className="table">
          <div className="table-head admin-table-head">
            <span>ID</span>
            <span>Name</span>
            <span>Department</span>
            <span>Semester</span>
            <span></span>
          </div>

          {students.map((s) => (
            <div className="table-row admin-table-row" key={s.id}>
              <span>{s.id}</span>
              <strong>{s.name}</strong>
              <span>{s.department}</span>
              <span>Sem {s.semester}</span>
              <button className="remove-btn" onClick={() => handleRemove(s.id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
