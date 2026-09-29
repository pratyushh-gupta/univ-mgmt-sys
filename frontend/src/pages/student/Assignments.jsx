import { useState } from "react";
import { saveAssignmentDraft, submitAssignment } from "../../api/assignments";
import useApiData from "../../hooks/useApiData";

export default function Assignments() {
  const { data: assignments, loading, error, refresh } = useApiData("/student/assignments");
  const [drafts, setDrafts] = useState({});
  const [message, setMessage] = useState("");
  const submissionText = (id) => drafts[id] ?? assignments.find((row) => row.id === id)?.text_content ?? "";

  async function submit(id) {
    setMessage("");
    try {
      await submitAssignment(id, { text_content: submissionText(id) || null });
      setDrafts({ ...drafts, [id]: "" });
      setMessage("Assignment submitted.");
      refresh();
    } catch (requestError) { setMessage(requestError.message); }
  }

  async function saveDraft(id) {
    setMessage("");
    try { await saveAssignmentDraft(id, { text_content: submissionText(id) || null }); setMessage("Draft saved."); refresh(); }
    catch (requestError) { setMessage(requestError.message); }
  }

  return <section className="panel full"><div className="panel-title"><h2>Assignments</h2></div>
    {loading && <p>Loading assignments…</p>}{error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    <div className="cards">{assignments.map((assignment) => <div className="assignment-card" key={assignment.id}>
      <div className="assignment-icon">📄</div><h3>{assignment.title}</h3><p>{assignment.subject}</p>
      <div className="assignment-bottom"><span>Published: {assignment.published_at ? new Date(assignment.published_at).toLocaleDateString() : "—"} · Due: {new Date(assignment.due).toLocaleString()}</span><span className={assignment.status === "submitted" || assignment.status === "graded" ? "submitted" : "pending"}>{assignment.status.replaceAll("_", " ")}</span></div>
      {assignment.status !== "submitted" && assignment.status !== "late" && assignment.status !== "graded" && assignment.status !== "returned" && <>
        <textarea aria-label={`Submission for ${assignment.title}`} placeholder="Write your submission" value={submissionText(assignment.id)} onChange={(event) => setDrafts({ ...drafts, [assignment.id]: event.target.value })} />
        <button className="secondary-btn" disabled={!submissionText(assignment.id).trim()} onClick={() => saveDraft(assignment.id)}>Save draft</button>
        <button className="login-btn" disabled={!submissionText(assignment.id).trim()} onClick={() => submit(assignment.id)}>Submit</button>
      </>}
      {assignment.marks != null && <p>Grade: {assignment.marks}/{assignment.max_marks}{assignment.feedback && ` · ${assignment.feedback}`}</p>}
    </div>)}</div>
    {!loading && !error && !assignments.length && <p>No published assignments are available for your enrolled offerings.</p>}
  </section>;
}
