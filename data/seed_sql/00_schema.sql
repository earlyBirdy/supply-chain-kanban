-- (patched) Removed pgcrypto extension requirement; UUIDs generated without extensions.

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
  case_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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


-- Transparency evidence layer: external data -> traceability event -> evidence receipt -> optional ledger anchor.
CREATE TABLE IF NOT EXISTS external_data_sources (
  source_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('erp','wms','mes','iot','supplier_portal','news','audit','manual')),
  trust_tier TEXT NOT NULL DEFAULT 'standard' CHECK (trust_tier IN ('high','standard','low')),
  owner TEXT,
  validation_method TEXT NOT NULL DEFAULT 'schema_check',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS traceability_events (
  event_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  case_id UUID REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  source_id TEXT REFERENCES external_data_sources(source_id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  object_ref TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  validation_status TEXT NOT NULL DEFAULT 'pending' CHECK (validation_status IN ('verified','cross_checked','pending','rejected')),
  evidence_confidence NUMERIC NOT NULL DEFAULT 0.50 CHECK (evidence_confidence >= 0 AND evidence_confidence <= 1),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_traceability_events_case_observed ON traceability_events(case_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_traceability_events_source ON traceability_events(source_id);

CREATE TABLE IF NOT EXISTS evidence_receipts (
  receipt_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  case_id UUID REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  trace_event_id UUID REFERENCES traceability_events(event_id) ON DELETE SET NULL,
  evidence_type TEXT NOT NULL,
  validation_status TEXT NOT NULL DEFAULT 'pending' CHECK (validation_status IN ('verified','cross_checked','pending','rejected')),
  confidence_score NUMERIC NOT NULL DEFAULT 0.50 CHECK (confidence_score >= 0 AND confidence_score <= 1),
  summary TEXT NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  receipt_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_evidence_receipts_case_generated ON evidence_receipts(case_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS blockchain_anchors (
  anchor_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  receipt_id UUID REFERENCES evidence_receipts(receipt_id) ON DELETE CASCADE,
  ledger_name TEXT NOT NULL DEFAULT 'demo-ledger',
  anchor_status TEXT NOT NULL DEFAULT 'stubbed' CHECK (anchor_status IN ('stubbed','queued','anchored','failed')),
  tx_ref TEXT NOT NULL DEFAULT '',
  content_hash TEXT NOT NULL,
  anchored_at TIMESTAMPTZ,
  proof_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_blockchain_anchors_receipt ON blockchain_anchors(receipt_id);


-- Kanban (Operational cards as first-class objects)
CREATE TABLE IF NOT EXISTS kanban_cards (
  card_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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
  scenario_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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
-- Materializations (required by pending_actions.materialization_id)
CREATE TABLE IF NOT EXISTS materializations (
  materialization_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  endpoint TEXT NOT NULL DEFAULT '',
  subject TEXT NOT NULL DEFAULT '',
  idempotency_key TEXT NOT NULL DEFAULT '',
  request_hash TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_materializations_idem ON materializations(endpoint, subject, idempotency_key);

CREATE TABLE IF NOT EXISTS pending_actions (
  pending_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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
  action_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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


-- Audit log: lightweight event trail for demos / governance.
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor TEXT,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS audit_log_ts_idx ON audit_log (ts DESC);
CREATE INDEX IF NOT EXISTS idx_idempotency_created ON idempotency_keys(created_at DESC);


CREATE INDEX IF NOT EXISTS idx_agent_actions_type_created ON agent_actions(action_type, created_at DESC);

CREATE TABLE IF NOT EXISTS governed_writebacks (
  writeback_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  action_id UUID REFERENCES agent_actions(action_id) ON DELETE SET NULL,
  case_id UUID REFERENCES agent_cases(case_id) ON DELETE CASCADE,
  pending_id UUID REFERENCES pending_actions(pending_id) ON DELETE SET NULL,
  adapter_name TEXT NOT NULL,
  connector_name TEXT NOT NULL,
  target_system TEXT NOT NULL,
  action_type TEXT NOT NULL,
  status TEXT NOT NULL,
  external_ref TEXT NOT NULL,
  policy_gate TEXT NOT NULL DEFAULT '',
  approval_state TEXT NOT NULL DEFAULT '',
  connector_family TEXT NOT NULL DEFAULT '',
  approval_policy TEXT NOT NULL DEFAULT '',
  receipt_summary TEXT NOT NULL DEFAULT '',
  request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_governed_writebacks_case_created ON governed_writebacks(case_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_governed_writebacks_pending ON governed_writebacks(pending_id, created_at DESC);

CREATE TABLE IF NOT EXISTS dq_results (
  dq_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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
  pred_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  resource_id TEXT NOT NULL,
  risk_score NUMERIC NOT NULL,
  confidence NUMERIC,
  predicted_window_days INT,
  features JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_agent_predictions_resource_ts ON agent_predictions(resource_id, ts DESC);

CREATE TABLE IF NOT EXISTS agent_recommendations (
  rec_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
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

-- duplicate materializations DDL removed; canonical definition lives above.

-- News evidence (Gemini Live demo)
CREATE TABLE IF NOT EXISTS news_items (
  item_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at TIMESTAMPTZ,
  topic TEXT NOT NULL DEFAULT 'general',
  source TEXT,
  title TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  summary TEXT,
  severity INT NOT NULL DEFAULT 0,
  signals JSONB NOT NULL DEFAULT '{}'::jsonb,
  raw JSONB NOT NULL DEFAULT '{}'::jsonb,
  case_id UUID
);

CREATE INDEX IF NOT EXISTS idx_news_items_topic_time ON news_items(topic, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_items_severity ON news_items(severity DESC);

CREATE TABLE IF NOT EXISTS news_alerts (
  alert_id UUID PRIMARY KEY DEFAULT (md5(random()::text || clock_timestamp()::text)::uuid),
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  topic TEXT NOT NULL,
  severity INT NOT NULL DEFAULT 0,
  item_id UUID,
  case_id UUID,
  status TEXT NOT NULL DEFAULT 'open',
  note TEXT
);

CREATE INDEX IF NOT EXISTS idx_news_alerts_topic_time ON news_alerts(topic, ts DESC);
