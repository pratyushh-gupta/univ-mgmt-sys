import { useState } from "react";
import { createAssignment, gradeSubmission, listSubmissions, updateAssignment } from "../../api/assignments";
import { createExam } from "../../api/exams";
import useApiData from "../../hooks/useApiData";

const localISO = (value) => value ? new Date(value).toISOString() : "";
const localDateTime = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};

export default function AcademicWork() {
  const courses = useApiData("/faculty/courses");
  const assignments = useApiData("/assignments");
  const exams = useApiData("/exam-schedules");
  const results = useApiData("/results");
  const [assignmentForm, setAssignmentForm] = useState({ course_offering_id: "", title: "", description: "", due_date: "", max_marks: "100", status: "draft" });
  const [examForm, setExamForm] = useState({ course_offering_id: "", name: "", exam_type: "internal", exam_date: "", start_time: "09:00", end_time: "10:00", room: "", max_marks: "100" });
  const [selectedAssignment, setSelectedAssignment] = useState("");
  const [editingAssignment, setEditingAssignment] = useState("");
  const [submissions, setSubmissions] = useState([]);
  const [grades, setGrades] = useState({});
  const [message, setMessage] = useState("");
  const error = courses.error || assignments.error || exams.error || results.error;

  async function createNewAssignment(event) {
    event.preventDefault(); setMessage("");
    try {
      const payload = { ...assignmentForm, course_offering_id: Number(assignmentForm.course_offering_id), due_date: localISO(assignmentForm.due_date), max_marks: Number(assignmentForm.max_marks) };
      if (editingAssignment) { await updateAssignment(editingAssignment, payload); setMessage("Assignment updated."); }
      else { await createAssignment(payload); setMessage("Assignment created."); }
      await assignments.refresh(); setEditingAssignment("");
      setAssignmentForm({ ...assignmentForm, title: "", description: "", due_date: "" });
    } catch (requestError) { setMessage(requestError.message); }
  }
  async function createNewExam(event) {
    event.preventDefault(); setMessage("");
    try {
      await createExam({ name: examForm.name, exam_type: examForm.exam_type, semester_id: courses.data.find((row) => String(row.id) === String(examForm.course_offering_id))?.semester_id,
        start_date: examForm.exam_date, end_date: examForm.exam_date, course_offering_id: Number(examForm.course_offering_id), exam_date: examForm.exam_date,
        start_time: examForm.start_time, end_time: examForm.end_time, room: examForm.room || null, max_marks: Number(examForm.max_marks) });
      setMessage("Exam scheduled and enrolled students notified."); await exams.refresh();
      setExamForm({ ...examForm, name: "", exam_date: "" });
    } catch (requestError) { setMessage(requestError.message); }
  }
  async function loadSubmissions(id) {
    setSelectedAssignment(id); setSubmissions([]); setMessage("");
    if (!id) return;
    try { setSubmissions(await listSubmissions(id)); }
    catch (requestError) { setMessage(requestError.message); }
  }
  async function grade(id) {
    const values = grades[id] || {};
    setMessage("");
    try { await gradeSubmission(id, { marks: Number(values.marks), feedback: values.feedback || null }); setMessage("Submission graded."); await loadSubmissions(selectedAssignment); }
    catch (requestError) { setMessage(requestError.message); }
  }
  async function setAssignmentStatus(row) {
    const status = row.status === "published" ? "closed" : "published";
    try { await updateAssignment(row.id, { status }); setMessage(`Assignment ${status}.`); await assignments.refresh(); }
    catch (requestError) { setMessage(requestError.message); }
  }

  return <>
    {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    <section className="panel full"><div className="panel-title"><h2>{editingAssignment ? "Edit assignment" : "Create assignment"}</h2></div>
      <form className="inline-form" onSubmit={createNewAssignment}>
        <select required value={assignmentForm.course_offering_id} onChange={(e) => setAssignmentForm({ ...assignmentForm, course_offering_id: e.target.value })} aria-label="Course offering"><option value="">Choose course</option>{courses.data.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.section} · {row.semester}</option>)}</select>
        <input required placeholder="Assignment title" value={assignmentForm.title} onChange={(e) => setAssignmentForm({ ...assignmentForm, title: e.target.value })} />
        <input required type="datetime-local" aria-label="Due date" value={assignmentForm.due_date} onChange={(e) => setAssignmentForm({ ...assignmentForm, due_date: e.target.value })} />
        <input required type="number" min="0.01" step="0.01" aria-label="Maximum marks" value={assignmentForm.max_marks} onChange={(e) => setAssignmentForm({ ...assignmentForm, max_marks: e.target.value })} />
        <select value={assignmentForm.status} onChange={(e) => setAssignmentForm({ ...assignmentForm, status: e.target.value })} aria-label="Assignment state"><option value="draft">Draft</option><option value="published">Publish now</option></select>
        <button className="login-btn">{editingAssignment ? "Save changes" : "Create"}</button>{editingAssignment && <button type="button" onClick={() => setEditingAssignment("")}>Cancel edit</button>}
      </form>
      <textarea placeholder="Description or instructions" value={assignmentForm.description} onChange={(e) => setAssignmentForm({ ...assignmentForm, description: e.target.value })} />
    </section>
    <section className="panel full"><div className="panel-title"><h2>Assignments and submissions</h2></div>
      {assignments.loading && <p>Loading assignments…</p>}
      <div className="table"><div className="table-head"><span>Course / Assignment</span><span>Due</span><span>State</span><span>Submissions</span><span /></div>
        {assignments.data.map((row) => <div className="table-row" key={row.id}><strong>{row.course_code} · {row.title}</strong><span>{new Date(row.due_date).toLocaleString()}</span><span>{row.status}</span><button type="button" onClick={() => loadSubmissions(String(row.id))}>View roster</button><button type="button" onClick={() => { setEditingAssignment(String(row.id)); setAssignmentForm({ course_offering_id: String(row.course_offering_id), title: row.title, description: row.description || "", due_date: localDateTime(row.due_date), max_marks: String(row.max_marks), status: row.status }); }}>Edit</button><button type="button" onClick={() => setAssignmentStatus(row)}>{row.status === "published" ? "Close" : "Publish"}</button></div>)}
      </div>
      {!!selectedAssignment && <><h3>Submission status by student</h3>{submissions.map((row) => <div className="class-row" key={row.student_id}><div className="class-info"><strong>{row.student_name} · {row.enrollment_number}</strong><span>{row.status}{row.text_content ? ` · ${row.text_content}` : ""}{row.file_url ? ` · File reference: ${row.file_url}` : ""}</span></div>
        {row.id && row.status !== "not_submitted" && <div className="inline-form"><input type="number" min="0" step="0.01" max={assignments.data.find((assignment) => String(assignment.id) === selectedAssignment)?.max_marks} placeholder="Marks" value={grades[row.id]?.marks ?? row.marks ?? ""} onChange={(e) => setGrades({ ...grades, [row.id]: { ...grades[row.id], marks: e.target.value } })} /><input placeholder="Feedback" value={grades[row.id]?.feedback ?? row.feedback ?? ""} onChange={(e) => setGrades({ ...grades, [row.id]: { ...grades[row.id], feedback: e.target.value } })} /><button type="button" onClick={() => grade(row.id)}>Save grade</button></div>}
      </div>)}</>}
      {!assignments.loading && !assignments.data.length && <p>No assignments found for your offerings.</p>}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Schedule exam</h2></div>
      <form className="inline-form" onSubmit={createNewExam}>
        <select required value={examForm.course_offering_id} onChange={(e) => setExamForm({ ...examForm, course_offering_id: e.target.value })} aria-label="Exam course"><option value="">Choose course</option>{courses.data.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.semester}</option>)}</select>
        <input required placeholder="Exam name" value={examForm.name} onChange={(e) => setExamForm({ ...examForm, name: e.target.value })} />
        <select value={examForm.exam_type} onChange={(e) => setExamForm({ ...examForm, exam_type: e.target.value })}><option value="internal">Internal</option><option value="midterm">Midterm</option><option value="final">Final</option></select>
        <input required type="date" value={examForm.exam_date} onChange={(e) => setExamForm({ ...examForm, exam_date: e.target.value })} />
        <input required type="time" value={examForm.start_time} onChange={(e) => setExamForm({ ...examForm, start_time: e.target.value })} />
        <input required type="time" value={examForm.end_time} onChange={(e) => setExamForm({ ...examForm, end_time: e.target.value })} />
        <input placeholder="Room" value={examForm.room} onChange={(e) => setExamForm({ ...examForm, room: e.target.value })} />
        <input required type="number" min="0.01" step="0.01" aria-label="Maximum exam marks" value={examForm.max_marks} onChange={(e) => setExamForm({ ...examForm, max_marks: e.target.value })} />
        <button className="login-btn">Schedule</button>
      </form>
      {exams.loading && <p>Loading exams…</p>}{exams.data.map((row) => <div className="class-row" key={row.id}><div className="class-info"><strong>{row.course_code} · {row.exam_name} ({row.exam_type})</strong><span>{row.exam_date} · {row.start_time}–{row.end_time} · {row.room || "Room pending"}</span></div></div>)}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Results entered for my courses</h2></div>{results.loading && <p>Loading results…</p>}<div className="table"><div className="table-head"><span>Student</span><span>Course / Assessment</span><span>Marks</span><span>Grade</span><span>Status</span></div>{results.data.map((row) => <div className="table-row" key={row.id}><span>{row.student_name}</span><strong>{row.course_code} · {row.assessment_name}{row.is_final ? " · GPA final" : ""}</strong><span>{row.marks}/{row.max_marks}</span><span>{row.grade}</span><span>{row.status}</span></div>)}</div>{!results.loading && !results.data.length && <p>No results have been entered.</p>}</section>
  </>;
}
