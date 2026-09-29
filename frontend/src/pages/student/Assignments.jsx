import { useState } from "react";
import { submitAssignment } from "../../api/assignments";
import useApiData from "../../hooks/useApiData";

export default function Assignments() {
  const { data: assignments, loading, error, refresh } = useApiData("/student/assignments");
  const [drafts, setDrafts] = useState({});
  const [message, setMessage] = useState("");

  async function submit(id) {
    setMessage("");
    try {
      await submitAssignment(id, { text_content: drafts[id] || null });
      setDrafts({ ...drafts, [id]: "" });
      setMessage("Assignment submitted.");
      refresh();
    } catch (requestError) { setMessage(requestError.message); }
  }

  return <section className="panel full"><div className="panel-title"><h2>Assignments</h2></div>
    {loading && <p>Loading assignments…</p>}{error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    <div className="cards">{assignments.map((assignment) => <div className="assignment-card" key={assignment.id}>
      <div className="assignment-icon">📄</div><h3>{assignment.title}</h3><p>{assignment.subject}</p>
      <div className="assignment-bottom"><span>Due: {new Date(assignment.due).toLocaleString()}</span><span className={assignment.status === "Submitted" ? "submitted" : "pending"}>{assignment.status}</span></div>
      {assignment.status !== "Submitted" && <>
        <textarea aria-label={`Submission for ${assignment.title}`} placeholder="Write your submission" value={drafts[assignment.id] || ""} onChange={(event) => setDrafts({ ...drafts, [assignment.id]: event.target.value })} />
        <button className="login-btn" disabled={!drafts[assignment.id]?.trim()} onClick={() => submit(assignment.id)}>Submit</button>
      </>}
    </div>)}</div>
    {!loading && !error && !assignments.length && <p>No published assignments are available for your enrolled offerings.</p>}
  </section>;
}
