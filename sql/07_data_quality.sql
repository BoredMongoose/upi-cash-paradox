-- Data-quality checks. The pipeline stops if any check fails.

CREATE OR REPLACE TABLE dq_results AS

-- 1. Payment systems add up to RBI's reported total (allowing for RBI's rounding)
SELECT 'payments: systems sum to reported total' AS check_name,
       p.fiscal_year AS detail,
       ABS(SUM(p.volume_bn) / MAX(t.volume_bn) - 1) < 0.01
         AND ABS(SUM(p.value_lakh_cr) / MAX(t.value_lakh_cr) - 1) < 0.01 AS passed
FROM mart_payments p
JOIN stg_payments t ON t.fy_start = p.fy_start AND t.item LIKE 'Total Payments%'
GROUP BY p.fiscal_year

UNION ALL
-- 2. Two different RBI tables agree: March value in the monthly table = annual (end-March) value
SELECT 'cash: monthly March = annual table', a.fiscal_year,
       ABS(m.cic_lakh_cr - a.cic_lakh_cr) < 0.01
FROM stg_cash_annual a
JOIN stg_cash_monthly m ON m.month = MAKE_DATE(a.fy_start + 1, 3, 1)

UNION ALL
-- 3. No missing months in the monthly series
SELECT 'cash: monthly series has no gaps',
       MIN(month) || ' to ' || MAX(month),
       COUNT(*) = DATEDIFF('month', MIN(month), MAX(month)) + 1
FROM stg_cash_monthly

UNION ALL
-- 4. World Bank and RBI agree on GDP where both report the same base (2020-21, 2021-22)
SELECT 'gdp: World Bank matches RBI', r.fiscal_year,
       ABS(w.gdp_crore / r.gdp_crore - 1) < 0.002
FROM stg_gdp_rbi r
JOIN stg_gdp_worldbank w USING (fy_start)
WHERE r.base_year = '2011-12' AND r.fy_start IN (2020, 2021)

UNION ALL
-- 5. The GDP base change is a modest level shift, not a data error
SELECT 'gdp: base-year splice factor between 0.9 and 1.1',
       ROUND(MAX(splice_factor), 4)::VARCHAR,
       MAX(splice_factor) BETWEEN 0.9 AND 1.1
FROM gdp_series

UNION ALL
-- 6. Continuous annual GDP series with no gaps
SELECT 'gdp: one value per year 2010-11 to 2025-26',
       COUNT(*)::VARCHAR || ' years',
       COUNT(*) = 16 AND COUNT(DISTINCT fy_start) = 16
FROM gdp_series

UNION ALL
-- 7. No negative or missing headline values
SELECT 'marts: no negative or missing headline values', 'cash, gdp, upi',
       (SELECT COUNT(*) FROM mart_cash_annual WHERE cash_lakh_cr <= 0 OR gdp_lakh_cr IS NULL) = 0
       AND (SELECT COUNT(*) FROM mart_upi_annual WHERE upi_value_lakh_cr <= 0 OR upi_txns_bn <= 0) = 0;
