import useApiData from "../../hooks/useApiData";

const days = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Timetable() {
  const { data, loading, error } = useApiData("/class-schedules");
  return <section className="panel full"><div className="panel-title"><h2>Class Timetable</h2></div>
    {loading && <p>Loading timetable…</p>}{error && <p role="alert">{error}</p>}
    <div className="table"><div className="table-head"><span>Day</span><span>Time</span><span>Course</span><span>Faculty / Section</span><span>Room</span></div>
      {data.map((row) => <div className="table-row" key={row.id}><strong>{days[row.day_of_week]}</strong><span>{row.start_time}–{row.end_time}</span><span>{row.course_code} · {row.course_name}</span><span>{row.faculty} · {row.section || ""}</span><span>{row.room || "—"}</span></div>)}
    </div>{!loading && !error && !data.length && <p>No class schedule has been published for your current enrollments.</p>}
  </section>;
}
