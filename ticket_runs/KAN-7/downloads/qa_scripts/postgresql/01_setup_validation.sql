SELECT current_database() AS database_name,
       to_regclass('{{RAW_SCHEMA}}.{{SOURCE_FLIGHTS_TABLE}}') IS NOT NULL AS source_flights_exists,
       to_regclass('{{ANALYTICS_SCHEMA}}.{{TARGET_TABLE}}') IS NOT NULL AS target_exists;
