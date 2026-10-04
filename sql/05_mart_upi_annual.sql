-- UPI against cash and the economy, 2021-22 onwards (RBI's official fiscal-year figures).

CREATE OR REPLACE TABLE mart_upi_annual AS
SELECT u.fiscal_year,
       u.fy_start,
       ROUND(u.volume_bn, 1)                                          AS upi_txns_bn,
       ROUND(u.value_lakh_cr, 1)                                      AS upi_value_lakh_cr,
       u.avg_ticket_rupees                                            AS upi_avg_ticket_rupees,
       u.share_of_volume_pct                                          AS upi_share_of_payments_pct,
       u.volume_growth_pct                                            AS upi_txn_growth_pct,
       c.cash_lakh_cr,
       c.gdp_lakh_cr,
       ROUND(100 * u.value_lakh_cr / c.gdp_lakh_cr, 1)                AS upi_value_to_gdp_pct,
       -- how many times over UPI moves the entire stock of cash each year
       ROUND(u.value_lakh_cr / c.cash_lakh_cr, 1)                     AS upi_value_vs_cash_stock_x,
       ROUND(u.volume_bn * 1e9 / p.population / 12, 1)                AS upi_txns_per_person_per_month
FROM mart_payments u
JOIN mart_cash_annual c USING (fy_start)
LEFT JOIN stg_population p USING (fy_start)
WHERE u.system = 'UPI'
ORDER BY u.fy_start;
