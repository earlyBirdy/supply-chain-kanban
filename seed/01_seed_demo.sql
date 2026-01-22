-- Idempotent demo seed: clear tables before inserting
TRUNCATE TABLE
  market_signals,
  ops_signals,
  erp_orders,
  wms_shipments,
  mes_production
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

INSERT INTO mes_production(record_id, plant_id, sku, input_qty, good_qty, scrap_qty, period) VALUES
('PR-1', 'PLANT_1', 'AI-SERVER-01', 120, 112, 8, '2025-W03'),
('PR-2', 'PLANT_1', 'PC-STD-01',    600, 585, 15,'2025-W03');
