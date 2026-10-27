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

export type FraudFactor = { label: string; value: string; contribution: number };

export type TransferResult = {
  reference: string;
  status: string;
  amount: number;
  currency: string;
  available_balance: number;
  created_at: string;
  fraud_check?: {
    level: string;
    probability: number;
    score: number;
    alert_id: number | null;
    assessment_id: number;
    top_factors: FraudFactor[];
    model_version: string;
  };
};

export type FraudContribution = { feature: string; label: string; value: string; contribution: number };

export type FraudModelResult = {
  amount: number;
  sender_balance: number;
  transaction_type: string;
  hour: number;
  probability: number;
  score: number;
  level: string;
  logit: number;
  base_value: number;
  contributions: FraudContribution[];
  thresholds: { high: number; medium: number };
  assessment_id: number;
  alert_id: number | null;
  model_version: string;
};

type ThresholdMetrics = { threshold: number; precision: number; recall: number; f1: number; alerts_per_10k: number };

export type FraudModelCard = {
  name: string;
  version: string;
  trained_at: string;
  algorithm: string;
  data: { source: string; license: string; rows: number; frauds: number; fraud_rate: number };
  split: Record<string, { steps: number[]; rows: number; frauds: number; fraud_rate: number }>;
  thresholds: { high: number; medium: number };
  metrics: { test: { pr_auc: number; roc_auc: number; brier: number; at_high: ThresholdMetrics; at_medium: ThresholdMetrics } };
  comparison: { model: string; strategy: string; validation: { pr_auc: number }; test: { pr_auc: number; roc_auc: number }; deployed?: boolean }[];
  limitations: string[];
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
