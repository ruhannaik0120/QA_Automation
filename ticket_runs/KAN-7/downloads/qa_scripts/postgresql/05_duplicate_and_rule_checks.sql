SELECT
  COUNT(*) FILTER (WHERE flight_key IS NULL) AS null_flight_keys,
  COUNT(*) - COUNT(DISTINCT flight_key) AS duplicate_flight_keys,
  COUNT(*) FILTER (WHERE is_cancelled AND cancellation_reason IS NULL) AS cancelled_without_reason,
  COUNT(*) FILTER (WHERE origin_airport = destination_airport) AS same_origin_destination
FROM {{ANALYTICS_SCHEMA}}.{{TARGET_TABLE}};
