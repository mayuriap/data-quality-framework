# Data Quality Framework

A production-grade data quality testing framework for financial services ETL pipelines, built using **dbt**, **Great Expectations**, **Behave BDD** and **Python**.

Simulates a real-world Medallion Architecture data pipeline with comprehensive automated testing across Bronze, Silver and Gold layers.

---

## Project Overview

This framework validates data quality at every layer of a Medallion Architecture ETL pipeline:
Raw Data → Bronze (DQ Flags) → Silver (Cleaned) → Gold (Aggregated)

**Key Features:**
- BDD test scenarios written in plain English using Behave
- dbt schema tests with custom macros for financial services
- Great Expectations suites with dynamic evaluation parameters
- Unified HTML test dashboard showing all results
- Real data quality findings discovered and documented

---

## Architecture
┌─────────────────────────────────────────────────────────┐
│ Medallion Architecture │
├──────────────┬──────────────────┬───────────────────────┤
│ BRONZE │ SILVER │ GOLD │
│ │ │ │
│ raw_customers│ int_customers │ gold_customer_summary │
│ raw_transactions int_transactions gold_daily_summary │
│ │ │ │
│ DQ flags │ Cleaned data │ Aggregations │
│ All records │ Valid records │ Business metrics │
│ 100 customers│ 89 customers │ 89 customers │
│ 500 tx │ 435 transactions │ 263 daily summaries │
└──────────────┴──────────────────┴───────────────────────┘

**Data flow:**
1. Raw data generated with intentional DQ issues
2. Bronze layer — all records kept, DQ flags assigned
3. Silver layer — bad records removed, only clean data
4. Gold layer — aggregations for reporting

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Core language |
| PostgreSQL | 18 | Database |
| dbt-core | 1.12.5 | ETL pipeline + schema tests |
| dbt-postgres | 1.11.0 | PostgreSQL adapter |
| dbt_utils | 1.4.1 | Extended dbt test library |
| Great Expectations | 1.4.1 | Data quality validation |
| Behave | 1.3.3 | BDD test framework |
| SQLAlchemy | 2.0.54 | Database ORM |
| Loguru | - | Structured logging |

---

## Project Structure
data-quality-framework/
│
├── dq_pipeline/ # ETL pipeline (simulates data engineering)
│ └── models/
│ ├── staging/ # Bronze layer — DQ flags
│ ├── intermediate/ # Silver layer — cleaned data
│ └── marts/ # Gold layer — aggregations
│
├── dbt_tests/ # QA testing framework
│ ├── models/
│ │ └── sources.yml # 58 declarative tests
│ ├── tests/
│ │ ├── staging/ # Bronze custom SQL tests
│ │ ├── intermediate/ # Silver custom SQL tests
│ │ └── marts/ # Gold custom SQL tests
│ └── macros/
│ ├── not_negative.sql # Reusable negative amount check
│ ├── no_future_date.sql # Reusable future date check
│ └── settlement_after_trade.sql # Settlement date validation
│
├── great_expectations/ # GE validation suites
│ └── expectations/
│ ├── bronze_customers_suite.json
│ ├── bronze_transactions_suite.json
│ ├── silver_customers_suite.json
│ ├── silver_transactions_suite.json
│ ├── gold_daily_suite.json
│ └── gold_customer_suite.json
│
├── features/ # BDD test scenarios
│ ├── dbt_data_quality.feature # 9 BDD scenarios
│ ├── environment.py # Behave setup
│ └── steps/
│ └── dbt_steps.py # Step definitions
│
├── utils/ # Shared utilities
│ ├── config_manager.py # Environment configuration
│ ├── db_connection.py # Database connection
│ ├── data_generator.py # Test data generation
│ └── ge_validator.py # Great Expectations validator
│
├── reports/ # Generated test reports
│ ├── dashboard.html # Unified HTML dashboard
│ ├── dbt_test_results.txt
│ ├── behave_results.txt
│ └── ge_validation_results.txt
│
├── setup_database.py # Database initialisation
├── generate_dashboard.py # Generate HTML dashboard
├── generate_reports.py # Generate text reports
└── README.md


---

## Setup Instructions

### Prerequisites

- Python 3.12
- PostgreSQL 18
- Git

### 1. Clone the repository

```bash
git clone https://github.com/mayuriap/data-quality-framework
cd data-quality-framework
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create `.env` file in project root:
ENVIRONMENT=test
DB_TYPE=postgresql
TEST_DB_HOST=localhost
TEST_DB_PORT=5432
TEST_DB_NAME=dq_framework_test
TEST_DB_USER=postgres
TEST_DB_PASSWORD=your_password


### 5. Create PostgreSQL database

```sql
CREATE DATABASE dq_framework_test;
```

### 6. Set up dbt profile

Create `~/.dbt/profiles.yml`:

```yaml
dbt_tests:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      password: your_password
      dbname: dq_framework_test
      schema: public
      threads: 4
```

### 7. Initialise database

```bash
python setup_database.py
```

### 8. Run ETL pipeline

```bash
cd dq_pipeline
dbt run
cd ..
```

### 9. Install dbt packages

```bash
cd dbt_tests
dbt deps
cd ..
```

---

## How to Run Tests

### Run all tests and generate dashboard

```bash
python generate_dashboard.py
```

Opens `reports/dashboard.html` automatically in browser.

### Run dbt tests only

```bash
cd dbt_tests
dbt test
cd ..
```

### Run BDD tests only

```bash
behave features/dbt_data_quality.feature
```

### Run Great Expectations only

```bash
python -c "from utils.ge_validator import GEValidator; gev = GEValidator(); print(gev.validate_all())"
```

### Run specific dbt layer

```bash
cd dbt_tests
dbt test --select source:bronze    # Bronze only
dbt test --select source:silver    # Silver only
dbt test --select source:gold      # Gold only
cd ..
```

---

## Test Results Summary

### dbt Tests — 58 total

| Layer | Tests | Status |
|-------|-------|--------|
| Bronze customers | 8 | ✅ PASS |
| Bronze transactions | 11 | ✅ PASS |
| Silver customers | 9 | ❌ 1 FAIL |
| Silver transactions | 12 | ❌ 1 FAIL |
| Gold daily summary | 6 | ✅ PASS |
| Gold customer summary | 5 | ❌ 1 FAIL |
| Custom staging | 2 | ✅ PASS |
| Custom intermediate | 3 | ❌ 1 FAIL |
| Custom marts | 2 | ✅ PASS |

### BDD Scenarios — 9 scenarios, 54 steps

| Scenario | Status |
|----------|--------|
| Full ETL pipeline runs successfully | ✅ PASS |
| Bronze layer passes all schema tests | ✅ PASS |
| Silver layer passes all schema tests | ❌ FAIL |
| Gold layer passes all schema tests | ❌ FAIL |
| Custom staging tests | ✅ PASS |
| Custom intermediate tests | ❌ FAIL |
| Custom marts tests | ✅ PASS |
| Known data quality findings reported | ✅ PASS |
| Great Expectations validates all layers | ❌ FAIL |

### Great Expectations — 50 expectations

| Suite | Expectations | Status |
|-------|-------------|--------|
| bronze_customers_suite | 8 | ✅ PASS |
| bronze_transactions_suite | 10 | ✅ PASS |
| silver_customers_suite | 9 | ❌ 1 FAIL |
| silver_transactions_suite | 9 | ❌ 1 FAIL |
| gold_daily_suite | 8 | ✅ PASS |
| gold_customer_suite | 6 | ❌ 1 FAIL |

---

## Known Findings

The framework discovered the following real data quality issues:

### Finding 1 — Duplicate Customer IDs
- **Severity:** High
- **Affected layer:** Silver, Gold
- **Description:** 1 duplicate customer ID found in Silver layer
- **Impact:** Customer aggregations in Gold are incorrect
- **Root cause:** ETL pipeline missing deduplication logic
- **Recommendation:** Add `ROW_NUMBER()` deduplication to `int_customers.sql`

### Finding 2 — Duplicate Transaction IDs
- **Severity:** High
- **Affected layer:** Silver
- **Description:** 10 duplicate transaction IDs found in Silver layer
- **Impact:** Transaction totals are inflated
- **Root cause:** ETL pipeline missing deduplication logic
- **Recommendation:** Add `ROW_NUMBER()` deduplication to `int_transactions.sql`

### Finding 3 — Bad Transactions in Silver
- **Severity:** Medium
- **Affected layer:** Silver
- **Description:** 3 transactions with bad DQ flags leaked to Silver
- **Root cause:** Duplicate transaction IDs bypassed the DQ filter
- **Recommendation:** Fix deduplication first — this issue will resolve

### Finding 4 — Settlement Date Before Transaction Date
- **Severity:** Critical
- **Affected layer:** Silver
- **Description:** 212 transactions have settlement date before transaction date
- **Impact:** Regulatory reporting errors, SWIFT settlement failures
- **Root cause:** Data generator not enforcing date sequence
- **Recommendation:** Add settlement_date > transaction_date constraint at source

---

## Recommendations

Based on findings, the following improvements are recommended:

1. **Add deduplication to Silver models**
```sql
   SELECT DISTINCT ON (customer_id) *
   FROM {{ ref('stg_customers') }}
   WHERE dq_email_flag = 'OK'
   ORDER BY customer_id, ingestion_timestamp DESC
```

2. **Add settlement date constraint at source**
```sql
   CONSTRAINT chk_settlement_after_trade
   CHECK (settlement_date >= transaction_date)
```

3. **Add dbt snapshot for SCD Type-2**
   Track customer segment changes over time.

4. **Add data freshness checks**
   Ensure pipeline runs daily and data is not stale.

---

## CI/CD

GitHub Actions pipeline runs on every push:

```yaml
# .github/workflows/dbt_tests.yml
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run dbt tests
        run: |
          cd dbt_tests
          dbt test
```

Pipeline status: [![CI](https://github.com/mayuriap/data-quality-framework/actions/workflows/dbt_tests.yml/badge.svg)](https://github.com/mayuriap/data-quality-framework/actions)

---

## Screenshots

### Test Dashboard
![Dashboard](screenshots\Test Dasboard -1.png ,screenshots\Test Dashboard-2.png)

### dbt Test Results
![dbt Tests](screenshots\DBT Test-1.png, screenshots\DBT Test-2.png)

### BDD Scenarios
![BDD Tests](screenshots\Behave-BDD-1.png, screenshots\Behave-BDD-2.png)

### GE Test Results
![GE Tests](screenshots\GE-Test-1.png, screenshots\GE-Test-2.png)

---

## Future Work

-  **Automate GE suite generation** — Script to generate JSON expectation 
  suites directly from database schema, reducing manual effort
- - **Add data freshness checks** — GE expectation to alert when pipeline 
  has not run within expected time window
- **Allure reporting** — Integrate Allure for richer BDD test reports 
  with trend analysis across multiple runs
-- **Add PII detection expectations** — GE expectations to detect 
  personally identifiable information in unexpected columns
- **Performance testing** — Validate pipeline handles large data volumes 
  within SLA time limits
- **Add incremental testing** — Verify incremental dbt runs process only 
  new records without duplicating existing data

---

## About the Author

**Mayuri Pednekar** — Senior SDET / Data Quality Engineer

14 years experience in software testing with 6+ years in financial services (NatWest, UBS, Deutsche Bank, Credit Suisse).

Specialising in data quality frameworks, ETL testing and AI-enabled quality engineering.

- GitHub: [github.com/mayuriap](https://github.com/mayuriap)
- LinkedIn: [linkedin.com/in/mayuripednekar](https://linkedin.com/in/mayuripednekar)
- Portfolio: [mayuriap.github.io](https://mayuriap.github.io)