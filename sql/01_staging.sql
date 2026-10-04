-- Staging: typed views over the parsed source files, converted to readable units.
-- Units: ₹ lakh crore (1 lakh crore = ₹1 trillion); transactions in billions.

CREATE OR REPLACE VIEW stg_cash_annual AS
SELECT fiscal_year,
       fy_start,
       cic                  / 1e5 AS cic_lakh_cr,          -- currency in circulation, end-March
       currency_with_public / 1e5 AS currency_with_public_lakh_cr,
       cash_with_banks      / 1e5 AS cash_with_banks_lakh_cr,
       demand_deposits      / 1e5 AS demand_deposits_lakh_cr,
       m3                   / 1e5 AS m3_lakh_cr             -- broad money
FROM read_csv_auto('data/staging/cash_annual.csv');

CREATE OR REPLACE VIEW stg_cash_monthly AS
SELECT CAST(month AS DATE)          AS month,
       cic                  / 1e5   AS cic_lakh_cr,
       currency_with_public / 1e5   AS currency_with_public_lakh_cr,
       cash_with_banks      / 1e5   AS cash_with_banks_lakh_cr,
       m3                   / 1e5   AS m3_lakh_cr
FROM read_csv_auto('data/staging/cash_monthly.csv');

CREATE OR REPLACE VIEW stg_payments AS
SELECT fiscal_year,
       fy_start,
       item,
       code,                                   -- RBI's numbering, e.g. '2.7' = UPI; NULL for totals
       system,
       volume_lakh / 1e4   AS volume_bn,       -- 1 lakh = 100,000 transactions
       value_crore / 1e5   AS value_lakh_cr
FROM read_csv_auto('data/staging/payments_annual.csv', types = {'code': 'VARCHAR'});

CREATE OR REPLACE VIEW stg_gdp_rbi AS
SELECT fiscal_year, fy_start, base_year, gdp_crore, population_lakh
FROM read_csv_auto('data/staging/gdp_rbi.csv');

CREATE OR REPLACE VIEW stg_gdp_worldbank AS
SELECT fiscal_year, fy_start, gdp_crore
FROM read_csv_auto('data/staging/gdp_worldbank.csv');

CREATE OR REPLACE VIEW stg_population AS
SELECT fy_start, population
FROM read_csv_auto('data/staging/population.csv');
