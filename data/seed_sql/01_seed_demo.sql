-- Idempotent demo seed: clear tables before inserting
TRUNCATE TABLE
  blockchain_anchors,
  evidence_receipts,
  traceability_events,
  external_data_sources,
  market_signals,
  ops_signals,
  erp_orders,
  wms_shipments,
  mes_production,
  pending_actions,
  governed_writebacks,
  kanban_cards,
  agent_cases,
  agent_scenarios,
  agent_recommendations,
  agent_actions,
  idempotency_keys,
  agent_predictions,
  dq_results,
  materializations
RESTART IDENTITY CASCADE;

-- Market volatility, freight pressure, and component-specific movement
INSERT INTO market_signals(resource_id, signal_type, value, period) VALUES
('dram_ddr5', 'price_index', 1.00, '2025-W01'),
('dram_ddr5', 'price_index', 1.18, '2025-W02'),
('dram_ddr5', 'price_index', 1.32, '2025-W03'),
('dram_ddr5', 'spot_availability', 0.62, '2025-W03'),
('battery_cells_lfp', 'price_index', 1.00, '2025-W01'),
('battery_cells_lfp', 'price_index', 1.11, '2025-W02'),
('battery_cells_lfp', 'port_delay_days', 7, '2025-W03'),
('ocean_freight_asia_us', 'price_index', 1.00, '2025-W01'),
('ocean_freight_asia_us', 'price_index', 1.22, '2025-W03'),
('industrial_ethernet_switch', 'regulatory_alert_score', 0.88, '2025-W03');

-- Operational signals with more realistic spread across suppliers / plants
INSERT INTO ops_signals(scope_type, scope_id, metric, value, period) VALUES
('supplier', 'SUP_A', 'otif', 0.96, '2025-W01'),
('supplier', 'SUP_A', 'otif', 0.91, '2025-W02'),
('supplier', 'SUP_A', 'otif', 0.87, '2025-W03'),
('supplier', 'SUP_B', 'otif', 0.93, '2025-W02'),
('supplier', 'SUP_B', 'otif', 0.79, '2025-W03'),
('supplier', 'SUP_C', 'quality_ppm', 420, '2025-W03'),
('plant', 'PLANT_1', 'yield', 0.98, '2025-W01'),
('plant', 'PLANT_1', 'yield', 0.93, '2025-W03'),
('plant', 'PLANT_2', 'schedule_adherence', 0.86, '2025-W03');

INSERT INTO erp_orders(order_id, sku, location, qty, need_date, net_price) VALUES
('SO-1001', 'AI-SERVER-01', 'DC_A', 100, '2025-01-20', 12000),
('SO-1002', 'AI-SERVER-01', 'DC_B', 80,  '2025-01-27', 12000),
('SO-2001', 'EV-PACK-02',   'PLANT_2', 300, '2025-02-03', 8400),
('SO-3001', 'EDGE-SWITCH-8','DC_C', 220, '2025-02-07', 450);

INSERT INTO wms_shipments(shipment_id, order_id, supplier_id, delivered_qty, ordered_qty, delivered_on_time, lead_time_days, period) VALUES
('SH-9001', 'SO-1001', 'SUP_A', 100, 100, TRUE,  14, '2025-W03'),
('SH-9002', 'SO-1002', 'SUP_A', 60,  80,  FALSE, 21, '2025-W03'),
('SH-9010', 'SO-2001', 'SUP_B', 180, 300, FALSE, 29, '2025-W03'),
('SH-9020', 'SO-3001', 'SUP_C', 220, 220, TRUE,  11, '2025-W03');

INSERT INTO mes_production(record_id, plant_id, sku, input_qty, good_qty, scrap_qty, period) VALUES
('PR-1', 'PLANT_1', 'AI-SERVER-01', 120, 112, 8, '2025-W03'),
('PR-2', 'PLANT_2', 'EV-PACK-02',   320, 294, 26, '2025-W03'),
('PR-3', 'PLANT_2', 'EDGE-SWITCH-8',240, 235, 5, '2025-W03');

-- Transparency evidence sources and buyer-facing traceability proof.
INSERT INTO external_data_sources(source_id, label, source_type, trust_tier, owner, validation_method) VALUES
('erp_orders', 'ERP Orders', 'erp', 'high', 'supply-ops', 'schema_and_referential_check'),
('wms_shipments', 'WMS Shipments', 'wms', 'high', 'logistics', 'shipment_cross_check'),
('supplier_portal', 'Supplier Portal Commitments', 'supplier_portal', 'standard', 'supplier-management', 'human_confirmed_commitment'),
('iot_gateway', 'IoT Gateway Telemetry', 'iot', 'standard', 'plant-ops', 'device_signature_check'),
('news_monitor', 'External News Monitor', 'news', 'low', 'risk-intel', 'source_attribution_check');

-- Cases
INSERT INTO agent_cases(case_id, status, owner, resource_id, scope, risk_score, confidence, lead_time_to_failure_days, root_signals, last_observed_period, created_at, updated_at)
VALUES
('11111111-1111-1111-1111-111111111111', 'AT_RISK', 'planner@demo', 'dram_ddr5',
 '{"scope_type":"supplier","scope_id":"SUP_A","sku":"AI-SERVER-01","location":"DC_A","supplier_name":"Micron East"}'::jsonb,
 82, 0.74, 14, '{"signals":["price_index_up","otif_down","spot_availability_down"]}'::jsonb, '2025-W03', now() - interval '28 hours', now() - interval '3 hours'),
('22222222-2222-2222-2222-222222222222', 'AT_RISK', 'opslead@demo', 'battery_cells_lfp',
 '{"scope_type":"supplier","scope_id":"SUP_B","sku":"EV-PACK-02","location":"PLANT_2","supplier_name":"Shenzhen LFP Energy"}'::jsonb,
 91, 0.81, 9, '{"signals":["port_delay_days_up","otif_down","schedule_adherence_down"]}'::jsonb, '2025-W03', now() - interval '41 hours', now() - interval '2 hours'),
('33333333-3333-3333-3333-333333333333', 'WATCH', 'quality@demo', 'industrial_ethernet_switch',
 '{"scope_type":"supplier","scope_id":"SUP_C","sku":"EDGE-SWITCH-8","location":"DC_C","supplier_name":"Orion Edge Components"}'::jsonb,
 68, 0.72, 21, '{"signals":["regulatory_alert_score_up","quality_ppm_up"]}'::jsonb, '2025-W03', now() - interval '18 hours', now() - interval '1 hour');


INSERT INTO traceability_events(event_id, case_id, source_id, event_type, object_ref, observed_at, validation_status, evidence_confidence, payload) VALUES
('10000001-1000-1000-1000-000000000001', '11111111-1111-1111-1111-111111111111', 'wms_shipments', 'shipment_delay_observed', 'SH-9002', now() - interval '4 hours', 'cross_checked', 0.86, '{"matched_order":"SO-1002","late_qty":20,"oracle_note":"WMS delay cross-checked against ERP order need date"}'::jsonb),
('10000002-1000-1000-1000-000000000002', '11111111-1111-1111-1111-111111111111', 'erp_orders', 'need_date_verified', 'SO-1002', now() - interval '4 hours', 'verified', 0.92, '{"sku":"AI-SERVER-01","need_date":"2025-01-27","oracle_note":"ERP order schema and SKU reference matched"}'::jsonb),
('10000003-1000-1000-1000-000000000003', '22222222-2222-2222-2222-222222222222', 'supplier_portal', 'supplier_eta_commitment', 'SUP_B', now() - interval '2 hours', 'pending', 0.68, '{"commitment":"alternate routing under review","oracle_note":"Supplier commitment requires human confirmation"}'::jsonb),
('10000004-1000-1000-1000-000000000004', '33333333-3333-3333-3333-333333333333', 'iot_gateway', 'quality_containment_signal', 'EDGE-SWITCH-8', now() - interval '1 hour', 'verified', 0.79, '{"ppm":420,"oracle_note":"Device signature and MES lot reference matched"}'::jsonb);

INSERT INTO evidence_receipts(receipt_id, case_id, trace_event_id, evidence_type, validation_status, confidence_score, summary, receipt_payload) VALUES
('20000001-2000-2000-2000-000000000001', '11111111-1111-1111-1111-111111111111', '10000001-1000-1000-1000-000000000001', 'shipment_traceability', 'cross_checked', 0.86, 'Late shipment evidence is cross-checked between WMS and ERP.', '{"buyer_message":"Shipment delay is supported by WMS event and ERP order need date.","data_trust":"cross_checked"}'::jsonb),
('20000002-2000-2000-2000-000000000002', '11111111-1111-1111-1111-111111111111', '10000002-1000-1000-1000-000000000002', 'order_need_date', 'verified', 0.92, 'ERP need date is verified for the affected order.', '{"buyer_message":"ERP source validates which customer demand is at risk.","data_trust":"verified"}'::jsonb),
('20000003-2000-2000-2000-000000000003', '22222222-2222-2222-2222-222222222222', '10000003-1000-1000-1000-000000000003', 'supplier_commitment', 'pending', 0.68, 'Supplier ETA evidence is visible but not fully verified yet.', '{"buyer_message":"Supplier portal update exists but still needs human confirmation.","data_trust":"pending"}'::jsonb),
('20000004-2000-2000-2000-000000000004', '33333333-3333-3333-3333-333333333333', '10000004-1000-1000-1000-000000000004', 'quality_signal', 'verified', 0.79, 'Quality containment evidence is verified from IoT gateway telemetry.', '{"buyer_message":"Telemetry-backed quality signal supports containment action.","data_trust":"verified"}'::jsonb);

INSERT INTO blockchain_anchors(anchor_id, receipt_id, ledger_name, anchor_status, tx_ref, content_hash, anchored_at, proof_payload) VALUES
('30000001-3000-3000-3000-000000000001', '20000001-2000-2000-2000-000000000001', 'demo-ledger', 'stubbed', 'DEMO-TX-SH-9002', 'sha256:demo-shipment-delay-cross-check', now() - interval '3 hours', '{"proof_type":"stub","note":"Replace with real ledger adapter only when required."}'::jsonb),
('30000002-3000-3000-3000-000000000002', '20000002-2000-2000-2000-000000000002', 'demo-ledger', 'stubbed', 'DEMO-TX-SO-1002', 'sha256:demo-erp-need-date', now() - interval '3 hours', '{"proof_type":"stub","note":"Hash anchor stub for demo transparency report."}'::jsonb),
('30000003-3000-3000-3000-000000000003', '20000004-2000-2000-2000-000000000004', 'demo-ledger', 'stubbed', 'DEMO-TX-QA-EDGE', 'sha256:demo-quality-containment-signal', now() - interval '45 minutes', '{"proof_type":"stub","note":"IoT evidence anchor stub."}'::jsonb);

-- Recommendations
INSERT INTO agent_recommendations(case_id, rank, action_type, action_payload, rationale, service_score, cost_score, risk_score, decision_score, created_at)
VALUES
('11111111-1111-1111-1111-111111111111', 1, 'ExpediteShipment', '{"shipment_id":"SH-9002","resource_id":"dram_ddr5","priority":"high","reason":"Recover service for DC_B builds"}'::jsonb, 'Pull the late memory shipment forward to protect DC_B server demand.', 85, 55, 70, 78, now() - interval '3 hours'),
('11111111-1111-1111-1111-111111111111', 2, 'TriggerPurchase', '{"resource_id":"dram_ddr5","supplier_id":"SUP_A","qty":40,"need_date":"2025-01-25"}'::jsonb, 'Create a controlled spot buy buffer.', 74, 61, 66, 70, now() - interval '3 hours'),
('22222222-2222-2222-2222-222222222222', 1, 'RebalanceAllocation', '{"resource_id":"battery_cells_lfp","from_location":"PLANT_3","to_location":"PLANT_2","qty":120}'::jsonb, 'Shift available cells from lower-priority builds to keep EV launch timing.', 88, 52, 83, 84, now() - interval '2 hours'),
('22222222-2222-2222-2222-222222222222', 2, 'OpenSupplierTicket', '{"resource_id":"battery_cells_lfp","supplier_id":"SUP_B","priority":"urgent","subject":"Port disruption recovery plan"}'::jsonb, 'Push supplier for alternate routing and ETA confirmation.', 79, 48, 77, 73, now() - interval '2 hours'),
('33333333-3333-3333-3333-333333333333', 1, 'CreateOpsTicket', '{"resource_id":"industrial_ethernet_switch","queue":"QUALITY-RISK","severity":"medium","summary":"Compliance and quality containment"}'::jsonb, 'Open an internal risk ticket so quality, procurement, and compliance can coordinate.', 67, 36, 58, 60, now() - interval '1 hour');

-- Kanban cards
INSERT INTO kanban_cards(card_id, case_id, resource_id, scope, title, description, status, priority, assignee, sla_hours, created_at, updated_at, last_activity_at, blocked_reason, resolved_at)
VALUES
('aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1', '11111111-1111-1111-1111-111111111111', 'dram_ddr5',
 '{"site":"DC_A","customer_program":"AI Rack Q1"}'::jsonb,
 'DDR5 risk: SUP_A OTIF drop + price spike',
 'Risk score elevated; evaluate expediting shipment SH-9002 and spot-buy coverage for AI server builds.',
 'todo', 2, 'planner@demo', 48, now() - interval '28 hours', now() - interval '3 hours', now() - interval '3 hours', NULL, NULL),
('bbbbbbb2-bbbb-bbbb-bbbb-bbbbbbbbbbb2', '22222222-2222-2222-2222-222222222222', 'battery_cells_lfp',
 '{"site":"PLANT_2","customer_program":"EV Launch Wave 2"}'::jsonb,
 'LFP battery cells delayed at port',
 'Inbound cells are late; rebalancing and supplier escalation needed to protect launch schedule.',
 'in_progress', 1, 'opslead@demo', 24, now() - interval '41 hours', now() - interval '2 hours', now() - interval '2 hours', NULL, NULL),
('ccccccc3-cccc-cccc-cccc-ccccccccccc3', '33333333-3333-3333-3333-333333333333', 'industrial_ethernet_switch',
 '{"site":"DC_C","customer_program":"Edge Retrofit"}'::jsonb,
 'Edge switch compliance follow-up',
 'A regulatory alert and rising quality ppm require an internal coordination ticket and controlled containment.',
 'todo', 3, 'quality@demo', 72, now() - interval '18 hours', now() - interval '1 hour', now() - interval '1 hour', NULL, NULL);

-- Scenarios with comparison-ready metrics
INSERT INTO agent_scenarios(case_id, created_at, scenario_name, supply_factor, price_factor, demand_factor, gap_qty, revenue_at_risk, cost_impact, service_impact, risk_exposure, details)
VALUES
('11111111-1111-1111-1111-111111111111', now() - interval '3 hours', 'Expedite inbound shipment', 0.95, 1.08, 1.00, 20, 240000, 26000, 4, 32, '{"recommended":true,"lead_time_reduction_days":5}'::jsonb),
('11111111-1111-1111-1111-111111111111', now() - interval '3 hours', 'Spot buy + dual source',      0.98, 1.16, 1.00, 10, 120000, 48000, 2, 28, '{"supplier_mix":"dual"}'::jsonb),
('11111111-1111-1111-1111-111111111111', now() - interval '3 hours', 'Do nothing / watch',         0.84, 1.00, 1.00, 35, 410000,  9000, 8, 57, '{"recommended":false}'::jsonb),
('22222222-2222-2222-2222-222222222222', now() - interval '2 hours', 'Rebalance inventory',        0.92, 1.04, 1.00, 18, 300000, 34000, 5, 35, '{"from":"PLANT_3","to":"PLANT_2"}'::jsonb),
('22222222-2222-2222-2222-222222222222', now() - interval '2 hours', 'Escalate supplier + expedite',0.96, 1.10, 1.00, 12, 190000, 52000, 3, 29, '{"expedite_mode":"air"}'::jsonb),
('22222222-2222-2222-2222-222222222222', now() - interval '2 hours', 'Absorb delay in schedule',   0.79, 1.00, 1.00, 42, 610000, 12000, 9, 71, '{"customer_impact":"launch slip"}'::jsonb),
('33333333-3333-3333-3333-333333333333', now() - interval '1 hour', 'Contain and inspect lots',    0.97, 1.02, 1.00, 5,  70000, 11000, 2, 18, '{"inspection":"100_percent"}'::jsonb),
('33333333-3333-3333-3333-333333333333', now() - interval '1 hour', 'Pause new receipts',          0.88, 1.00, 0.97, 14, 180000,  6000, 6, 36, '{"pause_reason":"compliance hold"}'::jsonb);

-- Pending actions across three connector packs
INSERT INTO pending_actions(pending_id, case_id, card_id, status, approval_required, action_type, action_payload, rationale, rank, created_at, updated_at)
VALUES
('ddddddd1-dddd-dddd-dddd-ddddddddddd1', '11111111-1111-1111-1111-111111111111', 'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1', 'pending', TRUE,
 'ExpediteShipment', '{"resource_id":"dram_ddr5","shipment_id":"SH-9002","priority":"high","reason":"Recover DC_B service"}'::jsonb,
 'Agent proposal: expedite the late memory shipment to protect AI server demand.', 10, now() - interval '3 hours', now() - interval '3 hours'),
('eeeeeee2-eeee-eeee-eeee-eeeeeeeeeee2', '22222222-2222-2222-2222-222222222222', 'bbbbbbb2-bbbb-bbbb-bbbb-bbbbbbbbbbb2', 'approved', TRUE,
 'OpenSupplierTicket', '{"resource_id":"battery_cells_lfp","supplier_id":"SUP_B","priority":"urgent","subject":"Port disruption recovery plan"}'::jsonb,
 'Approved supplier escalation to get committed ETA and alternate routing.', 20, now() - interval '2 hours', now() - interval '90 minutes'),
('fffffff3-ffff-ffff-ffff-fffffffffff3', '33333333-3333-3333-3333-333333333333', 'ccccccc3-cccc-cccc-cccc-ccccccccccc3', 'pending', TRUE,
 'CreateOpsTicket', '{"resource_id":"industrial_ethernet_switch","queue":"QUALITY-RISK","severity":"medium","summary":"Compliance containment and inspection"}'::jsonb,
 'Open an internal ticket for cross-functional containment and quality governance.', 30, now() - interval '1 hour', now() - interval '1 hour');
