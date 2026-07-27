SELECT r.raw_rows, t.analytics_rows,
       t.analytics_rows - r.raw_rows AS row_difference
FROM (SELECT COUNT(*) AS raw_rows FROM {{RAW_SCHEMA}}.{{SOURCE_FLIGHTS_TABLE}}) r
CROSS JOIN (SELECT COUNT(*) AS analytics_rows FROM {{ANALYTICS_SCHEMA}}.{{TARGET_TABLE}}) t;
