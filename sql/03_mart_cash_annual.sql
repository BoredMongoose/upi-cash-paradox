-- Cash against the size of the economy, every year since 2010-11.

CREATE OR REPLACE TABLE mart_cash_annual AS
WITH events(fy_start, event) AS (
    VALUES (2016, 'Demonetisation: ₹500/₹1000 notes withdrawn (Nov 2016); UPI launched (Apr 2016)'),
           (2020, 'COVID-19 lockdowns'),
           (2023, '₹2000 notes withdrawn (May 2023)')
)
SELECT c.fiscal_year,
       c.fy_start,
       ROUND(c.cic_lakh_cr, 2)                                              AS cash_lakh_cr,
       ROUND(g.gdp_lakh_cr, 2)                                              AS gdp_lakh_cr,
       ROUND(100 * c.cic_lakh_cr / g.gdp_lakh_cr, 2)                        AS cash_to_gdp_pct,
       ROUND(100 * (c.cic_lakh_cr / LAG(c.cic_lakh_cr) OVER w - 1), 1)      AS cash_growth_pct,
       ROUND(100 * (g.gdp_lakh_cr / LAG(g.gdp_lakh_cr) OVER w - 1), 1)      AS gdp_growth_pct,
       ROUND(100 * c.cic_lakh_cr / c.m3_lakh_cr, 2)                         AS cash_share_of_money_pct,
       ROUND(c.cic_lakh_cr * 1e12 / p.population)                           AS cash_per_person_rupees,
       e.event
FROM stg_cash_annual c
JOIN gdp_series g USING (fy_start)
LEFT JOIN stg_population p USING (fy_start)
LEFT JOIN events e USING (fy_start)
WINDOW w AS (ORDER BY c.fy_start)
ORDER BY c.fy_start;
