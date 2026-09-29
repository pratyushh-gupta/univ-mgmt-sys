import { useState } from "react";
import { publishResult } from "../../api/results";
import { createExam } from "../../api/exams";
import { createClassSchedule, deactivateClassSchedule, updateClassSchedule } from "../../api/timetable";
import { updateExamSchedule } from "../../api/exams";
import { apiRequest } from "../../api/client";
import useApiData from "../../hooks/useApiData";

const days = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function AcademicOperations() {
  const departments = useApiData("/departments");
  const semesters = useApiData("/semesters");
  const offerings = useApiData("/course-offerings?page_size=100", { initialData: { items: [] } });
  const faculty = useApiData("/faculty");
  const students = useApiData("/students?page_size=100", { initialData: { items: [] } });
  const schedules = useApiData("/class-schedules");
  const exams = useApiData("/exams");
  const results = useApiData("/results");
  const assignments = useApiData("/assignments");
  const [filters, setFilters] = useState({ department_id: "", semester_id: "", course_offering_id: "", faculty_id: "", student_id: "" });
  const [page, setPage] = useState(1);
  const query = new URLSearchParams(Object.entries({ ...filters, page, page_size: 50 }).filter(([, value]) => value !== "").map(([key, value]) => [key, String(value)]));
  const attendance = useApiData(`/admin/attendance?${query}` , { initialData: { items: [], total: 0 } });
  const [scheduleForm, setScheduleForm] = useState({ course_offering_id: "", day_of_week: 1, start_time: "09:00", end_time: "10:00", room: "" });
  const [editingSchedule, setEditingSchedule] = useState("");
  const [message, setMessage] = useState("");
  const [selectedSession, setSelectedSession] = useState(null);
  const [examForm, setExamForm] = useState({ course_offering_id: "", name: "", exam_type: "internal", exam_date: "", start_time: "09:00", end_time: "10:00", room: "", max_marks: "100" });

  async function submitSchedule(event) {
    event.preventDefault(); setMessage("");
    try {
      if (editingSchedule) await updateClassSchedule(editingSchedule, { ...scheduleForm, course_offering_id: Number(scheduleForm.course_offering_id), day_of_week: Number(scheduleForm.day_of_week) });
      else await createClassSchedule({ ...scheduleForm, course_offering_id: Number(scheduleForm.course_offering_id), day_of_week: Number(scheduleForm.day_of_week) });
      setMessage(editingSchedule ? "Timetable entry updated." : "Timetable entry created."); setEditingSchedule("");
      await schedules.refresh();
    } catch (error) { setMessage(error.message); }
  }
  async function removeSchedule(id) {
    if (!window.confirm("Remove this schedule from the published timetable?")) return;
    try { await deactivateClassSchedule(id); setMessage("Schedule removed from the published timetable."); await schedules.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  async function showSession(id) {
    try { setSelectedSession(await apiRequest(`/admin/attendance/sessions/${id}`)); }
    catch (error) { setMessage(error.message); }
  }
  async function editExam(row) {
    const start_time = window.prompt("Start time (HH:MM)", row.start_time.slice(0, 5));
    if (start_time === null) return;
    const end_time = window.prompt("End time (HH:MM)", row.end_time.slice(0, 5));
    if (end_time === null) return;
    try { await updateExamSchedule(row.id, { start_time, end_time }); setMessage("Exam schedule updated."); await exams.refresh(); }
    catch (error) { setMessage(error.message); }
  }
  async function addExam(event) {
    event.preventDefault(); setMessage("");
    const offering = offerings.data.items.find((row) => String(row.id) === String(examForm.course_offering_id));
    try {
      await createExam({ name: examForm.name, exam_type: examForm.exam_type, semester_id: offering.semester_id,
        start_date: examForm.exam_date, end_date: examForm.exam_date, course_offering_id: offering.id,
        exam_date: examForm.exam_date, start_time: examForm.start_time, end_time: examForm.end_time,
        room: examForm.room || null, max_marks: Number(examForm.max_marks) });
      setMessage("Exam scheduled; active enrollees have been notified."); await exams.refresh();
      setExamForm({ ...examForm, name: "", exam_date: "" });
    } catch (error) { setMessage(error.message); }
  }
  async function publish(id) {
    try { await publishResult(id); setMessage("Result published; the student was notified."); await results.refresh(); }
    catch (error) { setMessage(error.message); }
  }

  return <>
    {message && <p role="status">{message}</p>}
    <section className="panel full"><div className="panel-title"><h2>Attendance overview</h2><span className="badge">{attendance.data.total ?? 0} records</span></div>
      <div className="inline-form">
        <select value={filters.department_id} aria-label="Filter department" onChange={(e) => { setFilters({ ...filters, department_id: e.target.value }); setPage(1); }}><option value="">All departments</option>{departments.data.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
        <select value={filters.semester_id} aria-label="Filter semester" onChange={(e) => { setFilters({ ...filters, semester_id: e.target.value }); setPage(1); }}><option value="">All semesters</option>{semesters.data.map((row) => <option key={row.id} value={row.id}>{row.academic_year} · {row.name}</option>)}</select>
        <select value={filters.course_offering_id} aria-label="Filter course" onChange={(e) => { setFilters({ ...filters, course_offering_id: e.target.value }); setPage(1); }}><option value="">All courses</option>{(offerings.data.items || []).map((row) => <option key={row.id} value={row.id}>{row.code} · {row.section}</option>)}</select>
        <select value={filters.faculty_id} aria-label="Filter faculty" onChange={(e) => { setFilters({ ...filters, faculty_id: e.target.value }); setPage(1); }}><option value="">All faculty</option>{faculty.data.map((row) => <option key={row.faculty_id} value={row.faculty_id}>{row.name}</option>)}</select>
        <select value={filters.student_id} aria-label="Filter student" onChange={(e) => { setFilters({ ...filters, student_id: e.target.value }); setPage(1); }}><option value="">All students</option>{(students.data.items || []).map((row) => <option key={row.student_id} value={row.student_id}>{row.enrollment_number} · {row.name}</option>)}</select>
      </div>
      {attendance.loading && <p>Loading attendance…</p>}{attendance.error && <p role="alert">{attendance.error}</p>}
      <p>Present {attendance.data.summary?.present ?? 0} · Absent {attendance.data.summary?.absent ?? 0} · Late {attendance.data.summary?.late ?? 0} · Weighted attendance {attendance.data.summary?.attendance_percent == null ? "No records" : `${attendance.data.summary.attendance_percent}%`}</p>
      <div className="table"><div className="table-head"><span>Date / Topic</span><span>Student</span><span>Course</span><span>Faculty</span><span>Status</span><span /></div>{attendance.data.items.map((row) => <div className="table-row" key={row.id}><span>{row.date} · {row.topic || "—"}</span><strong>{row.enrollment_number} · {row.student}</strong><span>{row.course_code} · {row.course}</span><span>{row.faculty}</span><span>{row.status}</span><button onClick={() => showSession(row.session_id)}>Session details</button></div>)}</div>
      {!!attendance.data.total && <div className="inline-form"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page}</span><button disabled={page * 50 >= attendance.data.total} onClick={() => setPage(page + 1)}>Next</button></div>}
      {!attendance.loading && !attendance.data.total && <p>No attendance records match these filters.</p>}
      {selectedSession && <div className="panel"><button onClick={() => setSelectedSession(null)}>Close details</button><h3>{selectedSession.course_code} · {selectedSession.session_date} · {selectedSession.topic || "Session"}</h3>{selectedSession.records.map((row) => <p key={row.student_id}>{row.student} · {row.status}</p>)}</div>}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Timetable management</h2></div>
      <form className="inline-form" onSubmit={submitSchedule}>
        <select required value={scheduleForm.course_offering_id} onChange={(e) => setScheduleForm({ ...scheduleForm, course_offering_id: e.target.value })}><option value="">Choose offering</option>{(offerings.data.items || []).map((row) => <option key={row.id} value={row.id}>{row.code} · {row.semester} · {row.section}</option>)}</select>
        <select value={scheduleForm.day_of_week} onChange={(e) => setScheduleForm({ ...scheduleForm, day_of_week: e.target.value })}>{days.slice(1).map((day, index) => <option key={day} value={index + 1}>{day}</option>)}</select>
        <input required type="time" value={scheduleForm.start_time} onChange={(e) => setScheduleForm({ ...scheduleForm, start_time: e.target.value })} />
        <input required type="time" value={scheduleForm.end_time} onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })} />
        <input placeholder="Room" value={scheduleForm.room} onChange={(e) => setScheduleForm({ ...scheduleForm, room: e.target.value })} />
        <button className="login-btn">{editingSchedule ? "Save changes" : "Add schedule"}</button>{editingSchedule && <button type="button" onClick={() => setEditingSchedule("")}>Cancel edit</button>}
      </form>
      {schedules.error && <p role="alert">{schedules.error}</p>}
      <div className="table"><div className="table-head"><span>Day</span><span>Time</span><span>Course / Section</span><span>Faculty</span><span>Room</span><span /></div>{schedules.data.map((row) => <div className="table-row" key={row.id}><strong>{days[row.day_of_week]}</strong><span>{row.start_time}–{row.end_time}</span><span>{row.course_code} · {row.section}</span><span>{row.faculty}</span><span>{row.room || "—"}</span><div><button onClick={() => { setEditingSchedule(String(row.id)); setScheduleForm({ course_offering_id: String(row.course_offering_id), day_of_week: row.day_of_week, start_time: row.start_time.slice(0, 5), end_time: row.end_time.slice(0, 5), room: row.room || "" }); }}>Edit</button><button className="remove-btn" onClick={() => removeSchedule(row.id)}>Remove</button></div></div>)}</div>
      {!schedules.loading && !schedules.data.length && <p>No schedules have been configured.</p>}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Exam schedule management</h2></div>{exams.loading && <p>Loading exams…</p>}{exams.error && <p role="alert">{exams.error}</p>}
      <form className="inline-form" onSubmit={addExam}><select required value={examForm.course_offering_id} onChange={(e) => setExamForm({ ...examForm, course_offering_id: e.target.value })}><option value="">Choose offering</option>{(offerings.data.items || []).map((row) => <option key={row.id} value={row.id}>{row.code} · {row.section} · {row.semester}</option>)}</select><input required placeholder="Exam name" value={examForm.name} onChange={(e) => setExamForm({ ...examForm, name: e.target.value })} /><select value={examForm.exam_type} onChange={(e) => setExamForm({ ...examForm, exam_type: e.target.value })}><option value="internal">Internal</option><option value="midterm">Midterm</option><option value="final">Final</option></select><input required type="date" value={examForm.exam_date} onChange={(e) => setExamForm({ ...examForm, exam_date: e.target.value })} /><input required type="time" value={examForm.start_time} onChange={(e) => setExamForm({ ...examForm, start_time: e.target.value })} /><input required type="time" value={examForm.end_time} onChange={(e) => setExamForm({ ...examForm, end_time: e.target.value })} /><input placeholder="Room" value={examForm.room} onChange={(e) => setExamForm({ ...examForm, room: e.target.value })} /><input required type="number" min="0.01" step="0.01" value={examForm.max_marks} aria-label="Exam maximum marks" onChange={(e) => setExamForm({ ...examForm, max_marks: e.target.value })} /><button className="login-btn">Schedule exam</button></form>
      {exams.data.map((exam) => <div key={exam.id}><h3>{exam.name} · {exam.exam_type} · {exam.status}</h3>{exam.schedules.map((row) => <div className="class-row" key={row.id}><div className="class-info"><strong>{row.course_code} · {row.exam_date}</strong><span>{row.start_time}–{row.end_time} · {row.room || "Room pending"} · Max {row.max_marks}</span></div><button onClick={() => editExam(row)}>Edit time</button></div>)}</div>)}
      {!exams.loading && !exams.data.length && <p>No exams are scheduled.</p>}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Result review and publication</h2></div>{results.loading && <p>Loading results…</p>}{results.error && <p role="alert">{results.error}</p>}
      <div className="table"><div className="table-head"><span>Student</span><span>Course / assessment</span><span>Marks</span><span>Grade point</span><span>Status</span><span /></div>{results.data.map((row) => <div className="table-row" key={row.id}><strong>{row.student_name}</strong><span>{row.course_code} · {row.assessment_name}{row.is_final ? " · GPA final" : ""}</span><span>{row.marks}/{row.max_marks}</span><span>{row.grade_point}</span><span>{row.status}</span>{row.status !== "published" && <button onClick={() => publish(row.id)}>Publish</button>}</div>)}</div>
      {!results.loading && !results.data.length && <p>No results are available.</p>}
    </section>
    <section className="panel full"><div className="panel-title"><h2>Assignment overview</h2></div>{assignments.loading && <p>Loading assignments…</p>}{assignments.error && <p role="alert">{assignments.error}</p>}{assignments.data.map((row) => <div className="class-row" key={row.id}><div className="class-info"><strong>{row.course_code} · {row.title}</strong><span>Due {row.due_date} · {row.status} · {row.max_marks} marks</span></div></div>)}{!assignments.loading && !assignments.data.length && <p>No assignments have been created.</p>}</section>
  </>;
}
