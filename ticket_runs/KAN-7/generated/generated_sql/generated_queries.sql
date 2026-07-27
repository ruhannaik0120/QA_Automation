KAN-7 CONTROLLED READ-ONLY SQL CATALOG

This file is an execution catalog, not a batch script. Execute only the SQL text
inside one statement block at a time after separate execution approval.

Approved context: Jira plus validated QA package only.
Excluded source material: unresolved DOCX/XLSX attachments were not reviewed.
Excluded SQL: all scratch write tests in */06_scratch_write_test.sql.
Permission class for executable checks below: read-only.

CHECK_ID: PG-RO-001
PLATFORM: postgresql
SOURCE_PACKAGE_FILE: postgresql/01_setup_validation.sql
EXPECTED_OUTCOME: database_name is flight_delay_poc; source_flights_exists is true; target_exists is true.
SQL:
SELECT current_database() AS database_name,
       to_regclass('raw.flights') IS NOT NULL AS source_flights_exists,
       to_regclass('analytics.flight_performance') IS NOT NULL AS target_exists;

CHECK_ID: PG-RO-002
PLATFORM: postgresql
SOURCE_PACKAGE_FILE: postgresql/02_pre_qa_checks.sql
EXPECTED_OUTCOME: raw_flight_rows equals 5819079; blank field counts are captured for data-quality evidence.
SQL:
SELECT COUNT(*) AS raw_flight_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(year), '') IS NULL) AS blank_year_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(airline), '') IS NULL) AS blank_airline_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(origin_airport), '') IS NULL) AS blank_origin_rows,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(destination_airport), '') IS NULL) AS blank_destination_rows
FROM raw.flights;

CHECK_ID: PG-RO-003
PLATFORM: postgresql
SOURCE_PACKAGE_FILE: postgresql/03_post_qa_checks.sql
EXPECTED_OUTCOME: analytics metrics are captured for classification, data-quality, airline, and airport representation review.
SQL:
SELECT COUNT(*) AS analytics_rows,
       COUNT(*) FILTER (WHERE is_cancelled) AS cancelled_rows,
       COUNT(*) FILTER (WHERE is_diverted) AS diverted_rows,
       COUNT(*) FILTER (WHERE is_on_time) AS on_time_rows,
       COUNT(*) FILTER (WHERE data_quality_issue) AS data_quality_issue_rows,
       COUNT(*) FILTER (WHERE airline_name IS NULL) AS missing_airline_lookup_rows,
       COUNT(*) FILTER (WHERE origin_airport_name IS NULL) AS missing_origin_lookup_rows,
       COUNT(*) FILTER (WHERE destination_airport_name IS NULL) AS missing_destination_lookup_rows
FROM analytics.flight_performance;

CHECK_ID: PG-RO-004
PLATFORM: postgresql
SOURCE_PACKAGE_FILE: postgresql/04_reconciliation.sql
EXPECTED_OUTCOME: row_difference equals 0.
SQL:
SELECT r.raw_rows, t.analytics_rows,
       t.analytics_rows - r.raw_rows AS row_difference
FROM (SELECT COUNT(*) AS raw_rows FROM raw.flights) r
CROSS JOIN (SELECT COUNT(*) AS analytics_rows FROM analytics.flight_performance) t;

CHECK_ID: PG-RO-005
PLATFORM: postgresql
SOURCE_PACKAGE_FILE: postgresql/05_duplicate_and_rule_checks.sql
EXPECTED_OUTCOME: null_flight_keys equals 0; duplicate and business-rule exception counts are captured for review.
SQL:
SELECT
  COUNT(*) FILTER (WHERE flight_key IS NULL) AS null_flight_keys,
  COUNT(*) - COUNT(DISTINCT flight_key) AS duplicate_flight_keys,
  COUNT(*) FILTER (WHERE is_cancelled AND cancellation_reason IS NULL) AS cancelled_without_reason,
  COUNT(*) FILTER (WHERE origin_airport = destination_airport) AS same_origin_destination
FROM analytics.flight_performance;

CHECK_ID: SF-RO-001
PLATFORM: snowflake
SOURCE_PACKAGE_FILE: snowflake/01_setup_validation.sql
EXPECTED_OUTCOME: DATABASE_NAME is FLIGHT_DELAY_POC; SOURCE_FLIGHTS_EXISTS is 1; TARGET_EXISTS is 1.
SQL:
SELECT CURRENT_DATABASE() AS DATABASE_NAME,
       COUNT_IF(TABLE_SCHEMA = 'RAW' AND TABLE_NAME = 'FLIGHTS') AS SOURCE_FLIGHTS_EXISTS,
       COUNT_IF(TABLE_SCHEMA = 'ANALYTICS' AND TABLE_NAME = 'FLIGHT_PERFORMANCE') AS TARGET_EXISTS
FROM FLIGHT_DELAY_POC.INFORMATION_SCHEMA.TABLES;

CHECK_ID: SF-RO-002
PLATFORM: snowflake
SOURCE_PACKAGE_FILE: snowflake/02_pre_qa_checks.sql
EXPECTED_OUTCOME: RAW_FLIGHT_ROWS equals 5819079; blank field counts are captured for data-quality evidence.
SQL:
SELECT COUNT(*) AS RAW_FLIGHT_ROWS,
       COUNT_IF(NULLIF(TRIM(YEAR), '') IS NULL) AS BLANK_YEAR_ROWS,
       COUNT_IF(NULLIF(TRIM(AIRLINE), '') IS NULL) AS BLANK_AIRLINE_ROWS,
       COUNT_IF(NULLIF(TRIM(ORIGIN_AIRPORT), '') IS NULL) AS BLANK_ORIGIN_ROWS,
       COUNT_IF(NULLIF(TRIM(DESTINATION_AIRPORT), '') IS NULL) AS BLANK_DESTINATION_ROWS
FROM FLIGHT_DELAY_POC.RAW.FLIGHTS;

CHECK_ID: SF-RO-003
PLATFORM: snowflake
SOURCE_PACKAGE_FILE: snowflake/03_post_qa_checks.sql
EXPECTED_OUTCOME: Analytics metrics are captured for classification, data-quality, airline, and airport representation review.
SQL:
SELECT COUNT(*) AS ANALYTICS_ROWS,
       COUNT_IF(IS_CANCELLED) AS CANCELLED_ROWS,
       COUNT_IF(IS_DIVERTED) AS DIVERTED_ROWS,
       COUNT_IF(IS_ON_TIME) AS ON_TIME_ROWS,
       COUNT_IF(DATA_QUALITY_ISSUE) AS DATA_QUALITY_ISSUE_ROWS,
       COUNT_IF(AIRLINE_NAME IS NULL) AS MISSING_AIRLINE_LOOKUP_ROWS,
       COUNT_IF(ORIGIN_AIRPORT_NAME IS NULL) AS MISSING_ORIGIN_LOOKUP_ROWS,
       COUNT_IF(DESTINATION_AIRPORT_NAME IS NULL) AS MISSING_DESTINATION_LOOKUP_ROWS
FROM FLIGHT_DELAY_POC.ANALYTICS.FLIGHT_PERFORMANCE;

CHECK_ID: SF-RO-004
PLATFORM: snowflake
SOURCE_PACKAGE_FILE: snowflake/04_reconciliation.sql
EXPECTED_OUTCOME: ROW_DIFFERENCE equals 0.
SQL:
SELECT r.RAW_ROWS, t.ANALYTICS_ROWS,
       t.ANALYTICS_ROWS - r.RAW_ROWS AS ROW_DIFFERENCE
FROM (SELECT COUNT(*) AS RAW_ROWS FROM FLIGHT_DELAY_POC.RAW.FLIGHTS) r
CROSS JOIN (SELECT COUNT(*) AS ANALYTICS_ROWS FROM FLIGHT_DELAY_POC.ANALYTICS.FLIGHT_PERFORMANCE) t;

CHECK_ID: SF-RO-005
PLATFORM: snowflake
SOURCE_PACKAGE_FILE: snowflake/05_duplicate_and_rule_checks.sql
EXPECTED_OUTCOME: NULL_FLIGHT_KEYS equals 0; duplicate and business-rule exception counts are captured for review.
SQL:
SELECT
  COUNT_IF(FLIGHT_KEY IS NULL) AS NULL_FLIGHT_KEYS,
  COUNT(*) - COUNT(DISTINCT FLIGHT_KEY) AS DUPLICATE_FLIGHT_KEYS,
  COUNT_IF(IS_CANCELLED AND CANCELLATION_REASON IS NULL) AS CANCELLED_WITHOUT_REASON,
  COUNT_IF(ORIGIN_AIRPORT = DESTINATION_AIRPORT) AS SAME_ORIGIN_DESTINATION
FROM FLIGHT_DELAY_POC.ANALYTICS.FLIGHT_PERFORMANCE;

BLOCKED_CHECK_ID: PG-WRITE-001
PLATFORM: postgresql
SOURCE_PACKAGE_FILE: postgresql/06_scratch_write_test.sql
REASON: Contains DDL and DML; excluded from read-only scope and unresolved SCRATCH_TABLE token has no approved value.

BLOCKED_CHECK_ID: SF-WRITE-001
PLATFORM: snowflake
SOURCE_PACKAGE_FILE: snowflake/06_scratch_write_test.sql
REASON: Contains DDL and DML; excluded from read-only scope and unresolved SCRATCH_TABLE token has no approved value.
