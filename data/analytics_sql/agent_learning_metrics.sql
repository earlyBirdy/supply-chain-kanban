SELECT
  quarter,
  AVG(prediction_accuracy) AS prediction_accuracy,
  AVG(false_positive_rate) AS false_positive_rate
FROM agent_performance
GROUP BY quarter;
