SELECT COUNT(*) AS raw_flight_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(year), '') IS NULL) AS blank_year_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(airline), '') IS NULL) AS blank_airline_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(origin_airport), '') IS NULL) AS blank_origin_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(destination_airport), '') IS NULL) AS blank_destination_rows
FROM {{RAW_SCHEMA}}.{{SOURCE_FLIGHTS_TABLE}};
