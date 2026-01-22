CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Inputs
CREATE TABLE IF NOT EXISTS market_signals (
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  resource_id TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  value NUMERIC NOT NULL,
  period TEXT
);

CREATE TABLE IF NOT EXISTS ops_signals (
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  scope_type TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  value NUMERIC NOT NULL,
  period TEXT
);

-- ERP/MES/WMS canonical facts (minimal)
CREATE TABLE IF NOT EXISTS erp_orders (
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  order_id TEXT PRIMARY KEY,
  sku TEXT NOT NULL,
  location TEXT NOT NULL,
  qty NUMERIC NOT NULL,
  need_date DATE,
  net_price NUMERIC
);

CREATE TABLE IF NOT EXISTS wms_shipments (
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  shipment_id TEXT PRIMARY KEY,
  order_id TEXT,
  supplier_id TEXT,
  delivered_qty NUMERIC NOT NULL,
  ordered_qty NUMERIC NOT NULL,
  delivered_on_time BOOLEAN NOT NULL,
  lead_time_days NUMERIC,
  period TEXT
);

CREATE TABLE IF NOT EXISTS mes_production (
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  record_id TEXT PRIMARY KEY,
  plant_id TEXT NOT NULL,
  sku TEXT NOT NULL,
  input_qty NUMERIC NOT NULL,
  good_qty NUMERIC NOT NULL,
  scrap_qty NUMERIC NOT NULL,
  period TEXT
);

-- Agent state
CREATE TABLE IF NOT EXISTS agent_cases (
  case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'AT_RISK',
  owner TEXT,
  resource_id TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  risk_score INT NOT NULL,
  confidence NUMERIC NOT NULL DEFAULT 0.7,
  lead_time_to_failure_days INT,
  root_signals JSONB NOT NULL DEFAULT '{}'::jsonb,
  last_observed_period TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_cases_status ON agent_cases(status);
CREATE INDEX IF NOT EXISTS idx_agent_cases_resource ON agent_cases(resource_id);

-- Scenario outputs per case
CREATE TABLE IF NOT EXISTS agent_scenarios (
  scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  scenario_name TEXT NOT NULL,
  supply_factor NUMERIC NOT NULL,
  price_factor NUMERIC NOT NULL,
  demand_factor NUMERIC NOT NULL,
  gap_qty NUMERIC NOT NULL,
  revenue_at_risk NUMERIC NOT NULL,
  cost_impact NUMERIC NOT NULL,
  service_impact NUMERIC NOT NULL,
  risk_exposure NUMERIC NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS agent_recommendations (
  rec_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  rank INT NOT NULL,
  action_type TEXT NOT NULL,
  action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  service_score INT NOT NULL,
  cost_score INT NOT NULL,
  risk_score INT NOT NULL,
  decision_score INT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_actions (
  action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  channel TEXT NOT NULL,
  action_type TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  result TEXT
);

CREATE TABLE IF NOT EXISTS agent_predictions (
  pred_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resource_id TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  risk_score INT NOT NULL,
  confidence NUMERIC NOT NULL,
  predicted_window_days INT,
  features JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Data quality results
CREATE TABLE IF NOT EXISTS dq_results (
  dq_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  gate_name TEXT NOT NULL,
  severity TEXT NOT NULL,
  passed BOOLEAN NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  message TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb
);
