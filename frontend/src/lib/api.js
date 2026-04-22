const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return response.json();
}

export const api = {
  runRecommendation: (payload) =>
    fetchJson("/api/recommendations/run", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  createMandate: (payload) =>
    fetchJson("/api/mandates", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  getDefaultRun: () => fetchJson("/api/runs/default"),
  getLatestRun: () => fetchJson("/api/runs/latest"),
  getRunById: (runId) => fetchJson(`/api/runs/${runId}`),
  getMandates: () => fetchJson("/api/mandates"),
  getMandateById: (mandateId) => fetchJson(`/api/mandates/${mandateId}`),
  getLatestAuditJson: () => fetchJson("/api/audit/latest?format=json"),
  getAuditExportUrl: (format = "ndjson") => `${API_BASE}/api/audit/export?format=${format}`
};
