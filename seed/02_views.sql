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
