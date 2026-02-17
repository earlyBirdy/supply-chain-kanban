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


-- Kanban (Operational cards as first-class objects)
CREATE TABLE IF NOT EXISTS kanban_cards (
  card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Mapping to ontology objects
  case_id UUID UNIQUE REFERENCES agent_cases(case_id) ON DELETE SET NULL,
  resource_id TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,

  -- Card semantics
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo','in_progress','blocked','resolved')),
  priority INT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
  assignee TEXT,
  tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],

  -- SLA fields
  sla_hours INT NOT NULL DEFAULT 72 CHECK (sla_hours >= 1),
  sla_due_at TIMESTAMPTZ,
  breached BOOLEAN NOT NULL DEFAULT FALSE,

  blocked_reason TEXT,
  last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,

  -- SLA policy guardrails (enforced at DB level)
  CHECK (status <> 'blocked' OR blocked_reason IS NOT NULL),
  CHECK (status <> 'resolved' OR resolved_at IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_kanban_cards_status ON kanban_cards(status);
CREATE INDEX IF NOT EXISTS idx_kanban_cards_resource ON kanban_cards(resource_id);
CREATE INDEX IF NOT EXISTS idx_kanban_cards_updated ON kanban_cards(updated_at);


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


-- Materialization batches (idempotent UI-safe)
CREATE TABLE IF NOT EXISTS pending_actions (
  pending_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  card_id UUID REFERENCES kanban_cards(card_id) ON DELETE SET NULL,
  materialization_id UUID REFERENCES materializations(materialization_id) ON DELETE SET NULL,

  status TEXT NOT NULL DEFAULT 'pending',
  approval_required BOOLEAN NOT NULL DEFAULT false,
  action_type TEXT NOT NULL,
  action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  rationale TEXT NOT NULL DEFAULT '',
  rank INT NOT NULL DEFAULT 0,

  approved_by TEXT,
  approved_at TIMESTAMPTZ,
  executed_action_id UUID,
  execution_result TEXT,

  superseded_by UUID REFERENCES pending_actions(pending_id),
  superseded_at TIMESTAMPTZ,
  canceled_at TIMESTAMPTZ,
  canceled_reason TEXT,

  decision_idempotency_key TEXT,
  decision_request_hash TEXT,
  execution_idempotency_key TEXT,
  execution_request_hash TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pending_actions_case_updated ON pending_actions(case_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pending_actions_card_updated ON pending_actions(card_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pending_actions_materialization ON pending_actions(materialization_id);

CREATE TABLE IF NOT EXISTS agent_actions (
  action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  channel TEXT NOT NULL,
  action_type TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  result TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_actions_case_created ON agent_actions(case_id, created_at DESC);

-- API idempotency (demo)
CREATE TABLE IF NOT EXISTS idempotency_keys (
  key TEXT PRIMARY KEY,
  request_hash TEXT NOT NULL,
  response JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_keys(created_at DESC);


CREATE INDEX IF NOT EXISTS idx_agent_actions_type_created ON agent_actions(action_type, created_at DESC);

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
CREATE INDEX IF NOT EXISTS idx_dq_results_ts ON dq_results(ts DESC);


CREATE TABLE IF NOT EXISTS agent_predictions (
  pred_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  resource_id TEXT NOT NULL,
  risk_score NUMERIC NOT NULL,
  confidence NUMERIC,
  predicted_window_days INT,
  features JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_agent_predictions_resource_ts ON agent_predictions(resource_id, ts DESC);

CREATE TABLE IF NOT EXISTS agent_recommendations (
  rec_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  rank INT NOT NULL DEFAULT 0,
  action_type TEXT NOT NULL,
  action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  rationale TEXT NOT NULL DEFAULT '',
  service_score NUMERIC,
  cost_score NUMERIC,
  risk_score NUMERIC,
  decision_score NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_recommendations_case_created ON agent_recommendations(case_id, created_at DESC, rank ASC);

CREATE TABLE IF NOT EXISTS materializations (
  materialization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint TEXT NOT NULL DEFAULT '',
  subject TEXT NOT NULL DEFAULT '',
  idempotency_key TEXT NOT NULL DEFAULT '',
  request_hash TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_materializations_idem ON materializations(endpoint, subject, idempotency_key);
