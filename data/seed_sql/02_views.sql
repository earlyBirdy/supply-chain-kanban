CREATE OR REPLACE VIEW v_agent_cases AS
SELECT case_id, created_at, updated_at, status, owner, resource_id,
       risk_score, confidence, lead_time_to_failure_days, root_signals, scope
FROM agent_cases;

CREATE OR REPLACE VIEW v_market_signals_latest AS
SELECT DISTINCT ON (resource_id, signal_type)
  resource_id, signal_type, value, period, ts
FROM market_signals
ORDER BY resource_id, signal_type, ts DESC;

CREATE OR REPLACE VIEW v_supplier_otif_latest AS
SELECT DISTINCT ON (scope_id)
  scope_id AS supplier_id, value AS otif, period, ts
FROM ops_signals
WHERE scope_type='supplier' AND metric='otif'
ORDER BY scope_id, ts DESC;


CREATE OR REPLACE VIEW v_kanban_cards AS
SELECT
  k.card_id,
  k.created_at,
  k.updated_at,
  k.case_id,
  k.resource_id,
  k.scope,
  k.title,
  k.description,
  k.status,
  k.priority,
  k.assignee,
  k.tags,
  k.sla_hours,
  COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval)) AS sla_due_at,
  (k.status <> 'resolved' AND now() > COALESCE(k.sla_due_at, (k.created_at + (k.sla_hours || ' hours')::interval))) AS breached,
  k.blocked_reason,
  k.last_activity_at,
  k.resolved_at,
  c.risk_score AS case_risk_score,
  c.confidence AS case_confidence,
  c.status AS case_status
FROM kanban_cards k
LEFT JOIN agent_cases c ON c.case_id = k.case_id;




-- Pending actions (for UI): show approval/execution progress
CREATE OR REPLACE VIEW v_pending_actions AS
SELECT
  p.*,
  c.status AS case_status,
  c.risk_score AS case_risk_score,
  c.confidence AS case_confidence,
  k.status AS card_status,
  k.scope AS card_scope,
  k.resource_id AS card_resource_id
FROM pending_actions p
LEFT JOIN agent_cases c ON c.case_id = p.case_id
LEFT JOIN kanban_cards k ON k.card_id = p.card_id
;
