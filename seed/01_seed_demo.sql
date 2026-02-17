-- Idempotent demo seed: clear tables before inserting
TRUNCATE TABLE
  market_signals,
  ops_signals,
  erp_orders,
  wms_shipments,
  mes_production,
  kanban_cards,
  agent_cases,
  agent_scenarios,
  agent_recommendations,
  agent_actions,
  idempotency_keys,
  agent_predictions,
  dq_results
RESTART IDENTITY CASCADE;

INSERT INTO market_signals(resource_id, signal_type, value, period) VALUES
('dram_ddr5', 'price_index', 1.00, '2025-W01'),
('dram_ddr5', 'price_index', 1.18, '2025-W02'),
('dram_ddr5', 'price_index', 1.32, '2025-W03'),
('ocean_freight_asia_us', 'price_index', 1.00, '2025-W01'),
('ocean_freight_asia_us', 'price_index', 1.22, '2025-W03');

INSERT INTO ops_signals(scope_type, scope_id, metric, value, period) VALUES
('supplier', 'SUP_A', 'otif', 0.96, '2025-W01'),
('supplier', 'SUP_A', 'otif', 0.91, '2025-W02'),
('supplier', 'SUP_A', 'otif', 0.87, '2025-W03'),
('plant', 'PLANT_1', 'yield', 0.98, '2025-W01'),
('plant', 'PLANT_1', 'yield', 0.93, '2025-W03');

INSERT INTO erp_orders(order_id, sku, location, qty, need_date, net_price) VALUES
('SO-1001', 'AI-SERVER-01', 'DC_A', 100, '2025-01-20', 12000),
('SO-1002', 'AI-SERVER-01', 'DC_B', 80,  '2025-01-27', 12000),
('SO-2001', 'PC-STD-01',    'DC_A', 500, '2025-01-22', 900);

INSERT INTO wms_shipments(shipment_id, order_id, supplier_id, delivered_qty, ordered_qty, delivered_on_time, lead_time_days, period) VALUES
('SH-9001', 'SO-1001', 'SUP_A', 100, 100, TRUE,  14, '2025-W03'),
('SH-9002', 'SO-1002', 'SUP_A', 60,  80,  FALSE, 21, '2025-W03');

INSERT INTO mes_production,
  kanban_cards,
  agent_cases,
  agent_scenarios,
  agent_recommendations,
  agent_actions,
  idempotency_keys,
  agent_predictions,
  dq_results(record_id, plant_id, sku, input_qty, good_qty, scrap_qty, period) VALUES
('PR-1', 'PLANT_1', 'AI-SERVER-01', 120, 112, 8, '2025-W03'),
('PR-2', 'PLANT_1', 'PC-STD-01',    600, 585, 15,'2025-W03');


-- Demo case (AI agent output) + mapped Kanban card
INSERT INTO agent_cases(case_id, status, owner, resource_id, scope, risk_score, confidence, lead_time_to_failure_days, root_signals, last_observed_period)
VALUES (
  gen_random_uuid(),
  'AT_RISK',
  'planner@demo',
  'dram_ddr5',
  '{"scope_type":"supplier","scope_id":"SUP_A","sku":"AI-SERVER-01","location":"DC_A"}'::jsonb,
  82,
  0.74,
  14,
  '{"signals":["price_index_up","otif_down"]}'::jsonb,
  '2025-W03'
);

INSERT INTO agent_recommendations(case_id, rank, action_type, action_payload, service_score, cost_score, risk_score, decision_score)
SELECT case_id, 1, 'ExpediteShipment', '{"shipment_id":"SH-9002","carrier":"air"}'::jsonb, 85, 55, 70, 78
FROM agent_cases
ORDER BY created_at DESC
LIMIT 1;

INSERT INTO kanban_cards(case_id, resource_id, scope, title, description, status, priority, assignee, sla_hours)
SELECT
  case_id,
  resource_id,
  scope,
  'DDR5 risk: SUP_A OTIF drop + price spike',
  'Risk score elevated; evaluate expediting shipment SH-9002 and alternate sourcing.',
  'todo',
  2,
  'planner@demo',
  48
FROM agent_cases
ORDER BY created_at DESC
LIMIT 1;




-- Demo pending action (AI-proposed)
INSERT INTO pending_actions (case_id, card_id, status, approval_required, action_type, action_payload, rationale, rank)
SELECT
  c.case_id,
  k.card_id,
  'pending',
  TRUE,
  'ExpediteShipment',
  jsonb_build_object('resource_id', COALESCE(c.resource_id, k.resource_id), 'priority', 'high', 'reason', 'Demo: reduce lead-time risk'),
  'Agent proposal: expedite shipment to reduce risk exposure.',
  10
FROM agent_cases c
JOIN kanban_cards k ON k.case_id = c.case_id
ORDER BY c.created_at DESC
LIMIT 1;