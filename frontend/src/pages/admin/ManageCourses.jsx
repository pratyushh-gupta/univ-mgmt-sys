import { useState } from "react";
import { apiRequest } from "../../api/client";
import { createDepartment } from "../../api/departments";
import { createCourse, createCourseOffering, deactivateCourse } from "../../api/courses";
import useApiData from "../../hooks/useApiData";

export default function ManageCourses() {
  const [departmentForm, setDepartmentForm] = useState({ name: "", code: "", description: "" });
  const [courseForm, setCourseForm] = useState({ code: "", name: "", department_id: "", credits: 3, description: "" });
  const [offeringForm, setOfferingForm] = useState({ course_id: "", faculty_id: "", semester_id: "", section: "A", capacity: "", room: "" });
  const [editCourse, setEditCourse] = useState(null);
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");
  const courses = useApiData(`/courses?search=${encodeURIComponent(search)}&page_size=100`, { auth: false, initialData: { items: [], total: 0 } });
  const departments = useApiData("/departments", { auth: false });
  const faculty = useApiData("/faculty");
  const semesters = useApiData("/semesters", { auth: false });
  const offerings = useApiData("/course-offerings?active_only=false&page_size=100", { initialData: { items: [], total: 0 } });
  async function run(action, success) {
    setMessage("");
    try { await action(); setMessage(success); await Promise.all([courses.refresh(), offerings.refresh()]); }
    catch (error) { setMessage(error.message); }
  }
  async function submitDepartment(event) {
    event.preventDefault();
    try { await createDepartment(departmentForm); setDepartmentForm({ name: "", code: "", description: "" }); await departments.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  async function submitCourse(event) {
    event.preventDefault();
    await run(async () => { await createCourse({ ...courseForm, department_id: Number(courseForm.department_id), credits: Number(courseForm.credits) }); setCourseForm({ code: "", name: "", department_id: "", credits: 3, description: "" }); }, "Course created.");
  }
  async function submitOffering(event) {
    event.preventDefault();
    await run(() => createCourseOffering({ ...offeringForm, course_id: Number(offeringForm.course_id), faculty_id: Number(offeringForm.faculty_id), semester_id: Number(offeringForm.semester_id), capacity: offeringForm.capacity ? Number(offeringForm.capacity) : null }), "Course offering created.");
  }
  async function saveCourse(event) {
    event.preventDefault();
    await run(async () => { await apiRequest(`/courses/${editCourse.id}`, { method: "PATCH", body: { name: editCourse.name, description: editCourse.description, credits: Number(editCourse.credits), department_id: Number(editCourse.department_id) } }); setEditCourse(null); }, "Course updated.");
  }
  return <>
    {message && <p role="status">{message}</p>}
    <section className="panel full"><div className="panel-title"><h2>Add Department</h2></div><form className="inline-form" onSubmit={submitDepartment}><input required placeholder="Department name" value={departmentForm.name} onChange={(e) => setDepartmentForm({ ...departmentForm, name: e.target.value })} /><input required placeholder="Department code" value={departmentForm.code} onChange={(e) => setDepartmentForm({ ...departmentForm, code: e.target.value })} /><input placeholder="Description" value={departmentForm.description} onChange={(e) => setDepartmentForm({ ...departmentForm, description: e.target.value })} /><button className="login-btn">Add Department</button></form></section>
    <section className="panel full"><div className="panel-title"><h2>Add Course</h2></div><form className="inline-form" onSubmit={submitCourse}><input required placeholder="Course code" value={courseForm.code} onChange={(e) => setCourseForm({ ...courseForm, code: e.target.value })} /><input required placeholder="Course title" value={courseForm.name} onChange={(e) => setCourseForm({ ...courseForm, name: e.target.value })} /><select required value={courseForm.department_id} onChange={(e) => setCourseForm({ ...courseForm, department_id: e.target.value })}><option value="">Department</option>{departments.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select><input type="number" min="1" value={courseForm.credits} onChange={(e) => setCourseForm({ ...courseForm, credits: e.target.value })} /><input placeholder="Description" value={courseForm.description} onChange={(e) => setCourseForm({ ...courseForm, description: e.target.value })} /><button className="login-btn">Add Course</button></form></section>
    <section className="panel full"><div className="panel-title"><h2>Create Course Offering</h2></div><form className="inline-form" onSubmit={submitOffering}><select required value={offeringForm.course_id} onChange={(e) => setOfferingForm({ ...offeringForm, course_id: e.target.value })}><option value="">Course</option>{(courses.data.items || []).map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select><select required value={offeringForm.faculty_id} onChange={(e) => setOfferingForm({ ...offeringForm, faculty_id: e.target.value })}><option value="">Faculty</option>{faculty.data.map((row) => <option key={row.faculty_id} value={row.faculty_id}>{row.name}</option>)}</select><select required value={offeringForm.semester_id} onChange={(e) => setOfferingForm({ ...offeringForm, semester_id: e.target.value })}><option value="">Semester</option>{semesters.data.map((row) => <option key={row.id} value={row.id}>{row.name} · {row.academic_year}</option>)}</select><input required placeholder="Section" value={offeringForm.section} onChange={(e) => setOfferingForm({ ...offeringForm, section: e.target.value })} /><input type="number" min="1" placeholder="Capacity" value={offeringForm.capacity} onChange={(e) => setOfferingForm({ ...offeringForm, capacity: e.target.value })} /><input placeholder="Room" value={offeringForm.room} onChange={(e) => setOfferingForm({ ...offeringForm, room: e.target.value })} /><button className="login-btn">Schedule Offering</button></form></section>
    <section className="panel full"><div className="panel-title"><h2>Course Offerings</h2><span className="badge">{offerings.data.total || 0}</span></div>{offerings.error && <p role="alert">{offerings.error}</p>}<div className="table"><div className="table-head"><span>Course</span><span>Faculty</span><span>Semester</span><span>Section</span><span>Seats / status</span></div>{(offerings.data.items || []).map((row) => <div className="table-row" key={row.id}><strong>{row.code} · {row.name}</strong><span>{row.faculty}</span><span>{row.semester}</span><span>{row.section}</span><span>{row.students} / {row.capacity ?? "∞"} · {row.is_active ? "Open" : "Closed"} <button className="remove-btn" onClick={() => run(() => apiRequest(`/course-offerings/${row.id}`, { method: "PATCH", body: { is_active: !row.is_active } }), row.is_active ? "Offering closed." : "Offering opened.")}>{row.is_active ? "Close" : "Reopen"}</button></span></div>)}</div></section>
    <section className="panel full"><div className="panel-title"><h2>Course Catalog</h2><span className="badge">{courses.data.total || 0}</span></div><input placeholder="Search course code or title" value={search} onChange={(e) => setSearch(e.target.value)} />{courses.error && <p role="alert">{courses.error}</p>}<div className="table"><div className="table-head"><span>Code</span><span>Course title</span><span>Department</span><span>Credits</span><span /></div>{(courses.data.items || []).map((row) => <div className="table-row" key={row.id}><span>{row.code}</span><strong>{row.name}</strong><span>{row.department}</span><span>{row.credits}</span><span><button className="remove-btn" onClick={() => setEditCourse({ ...row })}>Edit</button><button className="remove-btn" onClick={() => run(() => deactivateCourse(row.code), "Course deactivated.")}>Deactivate</button></span></div>)}</div></section>
    {editCourse && <section className="panel full"><div className="panel-title"><h2>Edit {editCourse.code}</h2></div><form className="inline-form" onSubmit={saveCourse}><input required value={editCourse.name} onChange={(e) => setEditCourse({ ...editCourse, name: e.target.value })} /><select value={editCourse.department_id} onChange={(e) => setEditCourse({ ...editCourse, department_id: e.target.value })}>{departments.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select><input type="number" min="1" value={editCourse.credits} onChange={(e) => setEditCourse({ ...editCourse, credits: e.target.value })} /><input placeholder="Description" value={editCourse.description || ""} onChange={(e) => setEditCourse({ ...editCourse, description: e.target.value })} /><button className="login-btn">Save</button><button type="button" onClick={() => setEditCourse(null)}>Cancel</button></form></section>}
  </>;
}
