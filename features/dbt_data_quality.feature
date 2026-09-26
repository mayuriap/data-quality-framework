Feature: ETL Data Quality Validation using dbt
  As a Data Quality Engineer
  I want to run dbt tests against each pipeline layer
  So that data quality is validated automatically at Bronze, Silver and Gold

  Background:
    Given the database is connected
    And the ETL pipeline has run

  Scenario: Full ETL pipeline runs successfully
    Given the raw data exists in source tables
    When I run the full dbt pipeline
    Then all dbt models should complete successfully
    And Bronze layer should have data
    And Silver layer should have data
    And Gold layer should have data

  Scenario: Bronze layer passes all schema tests
    Given the Bronze layer has data
    When I run dbt tests on Bronze layer
    Then all Bronze schema tests should pass

  Scenario: Silver layer passes all schema tests
    Given the Silver layer has data
    When I run dbt tests on Silver layer
    Then all Silver schema tests should pass

  Scenario: Gold layer passes all schema tests
    Given the Gold layer has data
    When I run dbt tests on Gold layer
    Then all Gold schema tests should pass

  Scenario: Custom staging tests validate Bronze to raw count
    Given the Bronze layer has data
    When I run custom staging tests
    Then Bronze customer count should match raw customer count
    And Bronze transaction count should match raw transaction count

  Scenario: Custom intermediate tests validate Silver filtering
    Given the Silver layer has data
    When I run custom intermediate tests
    Then no bad customer records should exist in Silver
    And no bad transaction records should exist in Silver

  Scenario: Custom marts tests validate Gold aggregations
    Given the Gold layer has data
    When I run custom marts tests
    Then Gold totals should match Silver source totals
    And every Silver customer should appear in Gold summary

  Scenario: Known data quality findings are reported
    Given the Silver layer has data
    When I run all dbt tests
    Then duplicate findings should be logged and reported

  Scenario: Great Expectations validates data quality across all layers
    Given the ETL pipeline has run
    When I run Great Expectations validation on all layers
    Then all GE expectations should pass
    And Bronze layer GE expectations should pass
    And Silver layer GE expectations should pass
    And Gold layer GE expectations should pass

