-- =====================================================================
-- Customer Churn & Retention — SQL verification queries (MySQL 8 compatible)
-- Dataset: data/customers.csv (5,000 SaaS customers)
-- Table: customers(customer_id, signup_date, plan, segment, monthly_revenue,
--                   tenure_months, support_tickets_last_90d,
--                   days_since_last_login, churned, churn_date)
-- Every query below is a SELECT that reproduces a headline number from
-- the README "Results" section (real run 2026-09-26).
-- =====================================================================

-- SETUP (run once in MySQL Workbench; then run the queries below):
--   1. CREATE DATABASE IF NOT EXISTS churn_analytics;
--      USE churn_analytics;
--   2. CREATE TABLE customers (
--          customer_id VARCHAR(20),
--          signup_date DATE,
--          plan VARCHAR(20),
--          segment VARCHAR(20),
--          monthly_revenue DECIMAL(10,2),
--          tenure_months INT,
--          support_tickets_last_90d INT,
--          days_since_last_login INT,
--          churned TINYINT,
--          churn_date DATE NULL
--      );
--   3. LOAD DATA INFILE '/path/to/customers.csv'
--      INTO TABLE customers
--      FIELDS TERMINATED BY ',' IGNORE 1 LINES;

-- ---------------------------------------------------------------------
-- Q1. Overall churn rate.
-- What it answers: what share of the 5,000 customers churned.
-- README link: headline overall churn rate 22.9% (95% CI 21.7% - 24.0%).
-- (CI/p-values stay in Python; SQL reproduces the descriptive rate.)
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS customers,
       SUM(churned) AS churned_customers,
       ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_pct
FROM customers;

-- ---------------------------------------------------------------------
-- Q2. Churn rate by customer segment.
-- What it answers: which segment churns most.
-- README link: Startup 29.3% (worst), SMB 20.8%, Mid-market 11.0%.
-- ---------------------------------------------------------------------
SELECT segment,
       COUNT(*) AS customers,
       SUM(churned) AS churned_customers,
       ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_pct
FROM customers
GROUP BY segment
ORDER BY churn_rate_pct DESC;

-- ---------------------------------------------------------------------
-- Q3. Churn rate by plan.
-- What it answers: which plan tier churns most.
-- README link: Basic 31.5% (worst), Pro 17.4%, Enterprise 8.0%.
-- ---------------------------------------------------------------------
SELECT plan,
       COUNT(*) AS customers,
       SUM(churned) AS churned_customers,
       ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_pct
FROM customers
GROUP BY plan
ORDER BY churn_rate_pct DESC;

-- ---------------------------------------------------------------------
-- Q4. Average support tickets: churned vs retained.
-- What it answers: do churned customers raise more tickets.
-- README link: churn drivers -- 2.2 tickets (churned) vs 1.5 (retained).
-- ---------------------------------------------------------------------
SELECT CASE WHEN churned = 1 THEN 'churned' ELSE 'retained' END AS status,
       COUNT(*) AS customers,
       ROUND(AVG(support_tickets_last_90d), 1) AS avg_support_tickets
FROM customers
GROUP BY churned
ORDER BY churned DESC;

-- ---------------------------------------------------------------------
-- Q5. Average days since last login: churned vs retained.
-- What it answers: login recency gap between churned and retained.
-- README link: churn drivers -- 29.5 dormant days (churned) vs 4.0 (retained).
-- ---------------------------------------------------------------------
SELECT CASE WHEN churned = 1 THEN 'churned' ELSE 'retained' END AS status,
       COUNT(*) AS customers,
       ROUND(AVG(days_since_last_login), 1) AS avg_days_since_login
FROM customers
GROUP BY churned
ORDER BY churned DESC;

-- ---------------------------------------------------------------------
-- Q6 (bonus). Churn rate for high-ticket customers (>= 4 tickets in 90d).
-- What it answers: the ticket-volume risk threshold used in the retention plan.
-- README link: high-ticket customers churn at 36.2% vs 21.2% for the rest.
-- ---------------------------------------------------------------------
SELECT CASE WHEN support_tickets_last_90d >= 4 THEN 'high_ticket_4plus'
            ELSE 'rest'
       END AS ticket_group,
       COUNT(*) AS customers,
       ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_pct
FROM customers
GROUP BY ticket_group
ORDER BY churn_rate_pct DESC;
