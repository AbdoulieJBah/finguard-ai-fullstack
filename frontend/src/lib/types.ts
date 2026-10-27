export type Role = "Administrator" | "Compliance Officer" | "Risk Analyst";

export const AUDIT_ROLES: string[] = ["Administrator", "Compliance Officer"];

export type User = { id: number; name: string; email: string; role: string };

export type Account = {
  id: number;
  account_number: string;
  name: string;
  type: string;
  currency: string;
  balance: number;
  status: string;
};

export type Transaction = {
  id: number;
  reference: string;
  counterparty: string;
  amount: number;
  direction: string;
  category: string;
  description: string;
  created_at: string;
  status: string;
};

export type TransferResult = {
  reference: string;
  status: string;
  amount: number;
  currency: string;
  available_balance: number;
  created_at: string;
};

export type DashboardMetrics = {
  risk_score: number;
  fraud_alerts: number;
  aml_cases: number;
  high_priority_alerts: number;
  assessments_logged: number;
  assessments_30d: number;
};

export type RiskTrend = { month: string; risk: number; fraud: number; aml: number };

export type Alert = {
  id: number;
  kind: "fraud" | "aml";
  title: string;
  subject: string;
  level: string;
  status: string;
  reason: string;
  amount: number | null;
  assessment_id: number | null;
  created_at: string;
};

export type AssessmentBase = {
  recommendation: string;
  factors: string[];
  assessment_id: number;
  engine: string;
};

export type CreditResult = AssessmentBase & { risk_score: number; risk_level: string; debt_ratio: number };
export type FraudResult = AssessmentBase & { fraud_score: number; fraud_level: string; alert_id: number | null };
export type AmlResult = AssessmentBase & { aml_score: number; aml_level: string; alert_id: number | null };

export type AuditLogResponse = {
  items: { id: number; action: string; user: string; time: string; status: string }[];
  total_events: number;
  assessments_logged: number;
  failed_logins_24h: number;
};

export type SystemHealth = {
  backend: string;
  version: string;
  database: string;
  database_engine: string;
  database_latency_ms: number | null;
  persistent_storage: boolean;
  risk_engine: string;
  copilot: string;
  uptime_seconds: number;
  checked_at: string;
};
