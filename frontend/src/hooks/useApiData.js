import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../api/client";
export default function useApiData(path, { enabled = true, initialData = [], auth = true } = {}) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    if (!enabled || !path) return;
    setLoading(true); setError("");
    try { setData(await apiRequest(path, { auth })); }
    catch (e) { setError(e.message || "Unable to load data."); }
    finally { setLoading(false); }
  }, [path, enabled, auth]);
  // Fetch asynchronously after render so the effect only synchronizes with the API.
  useEffect(() => { const timer = setTimeout(() => { void refresh(); }, 0); return () => clearTimeout(timer); }, [refresh]);
  return { data, setData, loading, error, refresh };
}
