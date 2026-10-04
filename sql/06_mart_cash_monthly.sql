-- Monthly cash in circulation, April 2022 onwards, with growth rates and the events behind the bumps.

CREATE OR REPLACE TABLE mart_cash_monthly AS
WITH events(month, event) AS (
    VALUES (DATE '2022-10-01', 'Diwali (24 Oct)'),
           (DATE '2023-05-01', '₹2000 notes withdrawn (19 May)'),
           (DATE '2023-11-01', 'Diwali (12 Nov)'),
           (DATE '2024-04-01', 'General election (19 Apr – 1 Jun)'),
           (DATE '2024-11-01', 'Diwali (1 Nov)'),
           (DATE '2025-10-01', 'Diwali (20 Oct)')
)
SELECT m.month,
       ROUND(m.cic_lakh_cr, 2)                                                   AS cash_lakh_cr,
       ROUND(100 * (m.cic_lakh_cr / LAG(m.cic_lakh_cr) OVER w - 1), 2)           AS mom_pct,
       ROUND(100 * (m.cic_lakh_cr / LAG(m.cic_lakh_cr, 12) OVER w - 1), 2)       AS yoy_pct,
       ROUND(m.cash_with_banks_lakh_cr, 2)                                       AS cash_with_banks_lakh_cr,
       ROUND(100 * m.cic_lakh_cr / m.m3_lakh_cr, 2)                              AS cash_share_of_money_pct,
       e.event
FROM stg_cash_monthly m
LEFT JOIN events e USING (month)
WINDOW w AS (ORDER BY m.month)
ORDER BY m.month;

-- Typical change in each calendar month (the seasonal pattern), leaving out the
-- ₹2000-note withdrawal (Jun-Oct 2023), which would distort it.
CREATE OR REPLACE TABLE mart_cash_seasonality AS
SELECT EXTRACT(month FROM month)              AS month_num,
       STRFTIME(MIN(month), '%b')             AS month_name,
       ROUND(AVG(mom_pct), 2)                 AS avg_mom_pct,
       COUNT(mom_pct)                         AS years_observed
FROM mart_cash_monthly
WHERE mom_pct IS NOT NULL
  AND NOT month BETWEEN DATE '2023-06-01' AND DATE '2023-10-01'
GROUP BY 1
ORDER BY 1;
