import { useState } from "react";
import { dropSelf, enrollSelf } from "../../api/enrollments";
import useApiData from "../../hooks/useApiData";

export default function CourseRegistration() {
  const { data, loading, error, refresh } = useApiData("/student/course-offerings", { initialData: { items: [] } });
  const [message, setMessage] = useState("");
  async function act(item) {
    setMessage("");
    try {
      if (item.enrollment_status === "active") await dropSelf(item.enrollment_id);
      else await enrollSelf(item.id);
      setMessage(item.enrollment_status === "active" ? "Enrollment dropped." : "Enrollment confirmed.");
      await refresh();
    } catch (requestError) { setMessage(requestError.message); }
  }
  return <>
    <section className="welcome"><div><h2>Course Registration</h2><p>Register for offerings in your current academic period.</p></div><div className="semester"><span>{data.academic_year || "Academic year"}</span><strong>{data.semester || "No current semester"}</strong></div></section>
    <section className="panel full"><div className="panel-title"><h2>Available Offerings</h2></div>
      {loading && <p>Loading offerings…</p>}{error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
      <div className="table"><div className="table-head"><span>Course</span><span>Credits</span><span>Faculty / Section</span><span>Seats</span><span>Status / Action</span></div>
        {(data.items || []).map((item) => {
          const enrolled = item.enrollment_status === "active";
          const status = enrolled ? "Enrolled" : item.is_closed ? "Closed" : item.is_full ? "Full" : item.enrollment_status || "Available";
          return <div className="table-row" key={item.id}><strong>{item.code} · {item.name}</strong><span>{item.credits}</span><span>{item.faculty} · {item.section}</span><span>{item.available_seats ?? "Open"}</span>
            <span>{status} {enrolled && <button className="remove-btn" onClick={() => act(item)}>Drop</button>}{!enrolled && !item.is_closed && !item.is_full && item.enrollment_status !== "completed" && <button className="login-btn" onClick={() => act(item)}>Enroll</button>}</span></div>;
        })}
      </div>
      {!loading && !error && !(data.items || []).length && <p>No offerings are available for your current semester.</p>}
    </section>
  </>;
}
