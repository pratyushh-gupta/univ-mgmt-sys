import { studentResults } from "../../data/mockData";

export default function Results() {
  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>Academic Results</h2>
        <span className="overall">CGPA: 8.42</span>
      </div>

      <div className="table">
        <div className="table-head result-head">
          <span>Subject</span>
          <span>Grade</span>
          <span>Grade Point</span>
        </div>

        {studentResults.map((r) => (
          <div className="table-row result-row" key={r.subject}>
            <strong>{r.subject}</strong>
            <span className="grade">{r.grade}</span>
            <span>{r.point}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
