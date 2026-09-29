import useApiData from "../../hooks/useApiData";

export default function Notifications() {
  const { data, loading, error } = useApiData("/notifications");
  return <section className="panel full"><div className="panel-title"><h2>Notifications</h2></div>
    {loading && <p>Loading notifications…</p>}{error && <p role="alert">{error}</p>}
    {data.map((notice) => <div className="notice" key={notice.id}><div className="notice-dot"/><div><strong>{notice.title}</strong><p>{notice.message}</p><small>{notice.created_at}</small></div></div>)}
    {!loading && !error && !data.length && <p>You have no notifications.</p>}
  </section>;
}
