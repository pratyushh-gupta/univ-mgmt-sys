import { fullNotices } from "../../data/mockData";

export default function Notices() {
  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>University Notices</h2>
      </div>

      {fullNotices.map((n) => (
        <div className="large-notice" key={n.title}>
          <h3>📢 {n.title}</h3>
          <p>{n.body}</p>
          <small>{n.date}</small>
        </div>
      ))}
    </section>
  );
}
