SELECT COUNT(*) AS analytics_rows,
       COUNT(*) FILTER (WHERE is_cancelled) AS cancelled_rows,
       COUNT(*) FILTER (WHERE is_diverted) AS diverted_rows,
       COUNT(*) FILTER (WHERE is_on_time) AS on_time_rows,
       COUNT(*) FILTER (WHERE data_quality_issue) AS data_quality_issue_rows,
       COUNT(*) FILTER (WHERE airline_name IS NULL) AS missing_airline_lookup_rows,
       COUNT(*) FILTER (WHERE origin_airport_name IS NULL) AS missing_origin_lookup_rows,
       COUNT(*) FILTER (WHERE destination_airport_name IS NULL) AS missing_destination_lookup_rows
FROM {{ANALYTICS_SCHEMA}}.{{TARGET_TABLE}};
