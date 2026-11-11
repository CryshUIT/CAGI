import { useQuery, useQueries } from "@tanstack/react-query";
import { api } from "./api";
import { useTheta } from "./ThetaContext";
import { classifyIncident } from "./classify";
import type { ClassifiedIncident } from "./types";

export function useMeta() {
  return useQuery({ queryKey: ["meta"], queryFn: api.getMeta });
}

export function useIncidentList() {
  return useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents });
}

export function useIncidentDetail(id: string | undefined) {
  return useQuery({
    queryKey: ["incident", id],
    queryFn: () => api.getIncident(id!),
    enabled: !!id,
  });
}

/** Tai CHI TIET toan bo incident (can cho Overview KPI + donut), phan loai
 * theo theta/model dang chon trong ThetaContext. */
export function useClassifiedIncidents() {
  const { theta, model } = useTheta();
  const listQuery = useIncidentList();
  const ids = listQuery.data?.map((i) => i.incident_id) ?? [];

  const detailQueries = useQueries({
    queries: ids.map((id) => ({
      queryKey: ["incident", id],
      queryFn: () => api.getIncident(id),
      enabled: listQuery.isSuccess,
    })),
  });

  const isLoading = listQuery.isLoading || detailQueries.some((q) => q.isLoading);
  const isError = listQuery.isError || detailQueries.some((q) => q.isError);

  const classified: ClassifiedIncident[] = detailQueries
    .filter((q) => q.data)
    .map((q) => {
      const incident = q.data!;
      const result = classifyIncident(incident, theta, model);
      return { ...incident, outcome: result.outcome, firstAlertK: result.firstAlertK, firstAlertProb: result.firstAlertProb, leadTimeHours: result.leadTimeHours };
    });

  return { data: classified, isLoading, isError };
}
