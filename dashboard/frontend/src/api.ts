import type { DashboardMeta, IncidentDetail, IncidentListItem } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getMeta: () => getJson<DashboardMeta>("/meta"),
  listIncidents: () => getJson<IncidentListItem[]>("/incidents"),
  getIncident: (id: string) => getJson<IncidentDetail>(`/incidents/${id}`),
  getNewAnalysisStatus: () => getJson<{ enabled: boolean; message: string }>("/new-analysis"),
};
