// Logic phan loai outcome (Early/Late/Not Feasible/No alert/Not evaluable).
// Dinh nghia nay KHOP CHINH XAC voi code da dung trong du an:
//   scripts/n30_extra/run_lead_time_by_threshold_N30.py
//   scripts/n30_extra/extra_v4/_run_evaluation_v4.py
// (alert truoc e* = detected_before_endpoint/"early", alert tu e* tro di =
// late_detection/"late", e*<=2 khong co prefix truoc de danh gia = not
// feasible, khong co endpoint xac nhan = not evaluable, khong prefix nao
// vuot nguong = no alert). Theta chi doi nguong ap len diem SO DA LUU SAN
// (m1_cal/b3_cal) - KHONG tinh lai diem so.
import type { IncidentDetail, Outcome, PrefixPoint } from "./types";

export interface ClassificationResult {
  outcome: Outcome;
  firstAlertK: number | null;
  firstAlertProb: number | null;
  leadTimeHours: number | null;
}

function findFirstAlert(points: PrefixPoint[], theta: number, modelKey: "m1_cal" | "b3_cal") {
  const sorted = [...points].sort((a, b) => a.k - b.k);
  for (const p of sorted) {
    const v = p[modelKey];
    if (v !== null && v >= theta) {
      return { k: p.k, prob: v };
    }
  }
  return null;
}

function actionTimestamp(incident: IncidentDetail, k: number): string | null {
  const action = incident.actions.find((a) => a.idx === k);
  return action ? action.timestamp : null;
}

export function classifyIncident(
  incident: IncidentDetail,
  theta: number,
  modelKey: "m1_cal" | "b3_cal" = "m1_cal"
): ClassificationResult {
  const eStar = incident.e_star;

  if (!incident.endpoint_confirmed || eStar === null) {
    return { outcome: "not_evaluable", firstAlertK: null, firstAlertProb: null, leadTimeHours: null };
  }
  if (eStar <= 2) {
    return { outcome: "not_feasible", firstAlertK: null, firstAlertProb: null, leadTimeHours: null };
  }

  const alert = findFirstAlert(incident.prefix_points, theta, modelKey);
  if (!alert) {
    return { outcome: "no_alert", firstAlertK: null, firstAlertProb: null, leadTimeHours: null };
  }

  let leadTimeHours: number | null = null;
  const tAlert = actionTimestamp(incident, alert.k);
  const tExit = actionTimestamp(incident, eStar);
  if (tAlert && tExit) {
    const diffMs = new Date(tExit).getTime() - new Date(tAlert).getTime();
    leadTimeHours = diffMs / 1000 / 3600;
  }

  const outcome: Outcome = alert.k < eStar ? "early" : "late";
  return { outcome, firstAlertK: alert.k, firstAlertProb: alert.prob, leadTimeHours };
}

export const OUTCOME_LABEL: Record<Outcome, string> = {
  early: "Early",
  late: "Late",
  not_feasible: "Not Feasible",
  no_alert: "No Alert",
  not_evaluable: "Not Evaluable",
};

export const OUTCOME_COLOR: Record<Outcome, string> = {
  early: "#18D6A3",
  late: "#FFBA36",
  not_feasible: "#91A6C2",
  no_alert: "#91A6C2",
  not_evaluable: "#91A6C2",
};
