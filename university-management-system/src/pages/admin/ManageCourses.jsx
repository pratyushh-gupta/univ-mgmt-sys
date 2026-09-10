import { useState } from "react";
import { allCourses } from "../../data/mockData";

export default function ManageCourses() {
  const [courses, setCourses] = useState(allCourses);
  const [form, setForm] = useState({ code: "", name: "", faculty: "", department: "" });

  function handleAdd(e) {
    e.preventDefault();
    if (!form.code || !form.name) return;
    // TODO: FastAPI POST /courses yahan call hoga.
    setCourses([...courses, { ...form, enrolled: 0 }]);
    setForm({ code: "", name: "", faculty: "", department: "" });
  }

  function handleRemove(code) {
    // TODO: FastAPI DELETE /courses/{code} yahan call hoga.
    setCourses(courses.filter((c) => c.code !== code));
  }

  return (
    <>
      <section className="panel full">
        <div className="panel-title">
          <h2>Add New Course</h2>
        </div>

        <form className="inline-form" onSubmit={handleAdd}>
          <input
            placeholder="Course Code"
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value })}
          />
          <input
            placeholder="Course Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <input
            placeholder="Assigned Faculty"
            value={form.faculty}
            onChange={(e) => setForm({ ...form, faculty: e.target.value })}
          />
          <input
            placeholder="Department"
            value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })}
          />
          <button className="login-btn" type="submit">Add Course</button>
        </form>
      </section>

      <section className="panel full">
        <div className="panel-title">
          <h2>All Courses</h2>
          <span className="badge">{courses.length} total</span>
        </div>

        <div className="table">
          <div className="table-head admin-table-head">
            <span>Code</span>
            <span>Name</span>
            <span>Faculty</span>
            <span>Enrolled</span>
            <span></span>
          </div>

          {courses.map((c) => (
            <div className="table-row admin-table-row" key={c.code}>
              <span>{c.code}</span>
              <strong>{c.name}</strong>
              <span>{c.faculty}</span>
              <span>{c.enrolled}</span>
              <button className="remove-btn" onClick={() => handleRemove(c.code)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
