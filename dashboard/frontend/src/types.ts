export interface ShapContribution {
  feature: string;
  contribution: number;
  feature_value: number | null;
  aadapt_ids: string[];
}

export interface PrefixPoint {
  prefix_label: string;
  k: number;
  m1_raw: number | null;
  m1_cal: number | null;
  b3_raw: number | null;
  b3_cal: number | null;
  m1_top_shap: ShapContribution[];
  b3_top_shap: ShapContribution[];
}

export interface ActionEvent {
  idx: number;
  event_type: string;
  timestamp: string;
  src: string;
  dst: string;
  src_short: string;
  dst_short: string;
  token: string | null;
  amount_norm: number | null;
  tx_hash: string | null;
  protocol: string | null;
}

export interface IncidentDetail {
  incident_id: string;
  name: string;
  chain: string;
  seed_address: string;
  start_block: number;
  endpoint_confirmed: boolean;
  endpoint_type: string | null;
  e_star: number | null;
  e_star_action_type: string | null;
  e_star_protocol: string | null;
  n_actions_total: number;
  kind: string;
  label: number;
  source_report: string | null;
  source_url: string | null;
  prefix_points: PrefixPoint[];
  actions: ActionEvent[];
}

export interface IncidentListItem {
  incident_id: string;
  name: string;
  chain: string;
  endpoint_confirmed: boolean;
  e_star: number | null;
  n_actions_total: number;
  label: number;
}

export interface DashboardMeta {
  n_incidents: number;
  m1_theta_oof: number;
  b3_theta_oof: number;
  pooled_pr_auc_m1: number;
  pooled_pr_auc_b3: number;
  target_fpr: number;
  seed: number;
  generated_note: string;
}

export type Outcome = "early" | "late" | "not_feasible" | "no_alert" | "not_evaluable";

export interface ClassifiedIncident extends IncidentDetail {
  outcome: Outcome;
  firstAlertK: number | null;
  firstAlertProb: number | null;
  leadTimeHours: number | null;
}
