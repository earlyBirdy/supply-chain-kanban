SELECT
  resource_id,
  (supply_confidence_decay + demand_acceleration + price_divergence) / 3
    AS constraint_risk_score
FROM resource_signals;
