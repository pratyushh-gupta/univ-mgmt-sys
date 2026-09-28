import { assignments } from "../../data/mockData";

export default function Assignments() {
  return (
    <div className="cards">
      {assignments.map((a) => (
        <div className="assignment-card" key={a.title}>
          <div className="assignment-icon">📄</div>
          <h3>{a.title}</h3>
          <p>{a.subject}</p>

          <div className="assignment-bottom">
            <span>Due: {a.due}</span>
            <span className={a.status === "Submitted" ? "submitted" : "pending"}>
              {a.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
