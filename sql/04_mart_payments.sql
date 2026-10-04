-- Every non-cash payment system RBI reports, with its share of the year's payments.
-- Only "leaf" systems are kept (e.g. UPI, NEFT, credit cards), so shares add up to 100%.

CREATE OR REPLACE TABLE mart_payments AS
WITH leaves AS (
    SELECT fiscal_year, fy_start, code, system, volume_bn, value_lakh_cr,
           CASE
               WHEN system = 'UPI'                                       THEN 'UPI'
               WHEN code IN ('4.1', '4.2')                               THEN 'Cards'
               WHEN code IN ('1', '2.4', '2.6')                          THEN 'Bank transfers (RTGS, NEFT, IMPS)'
               WHEN code IN ('2.2', '2.5', '3.3')                        THEN 'Bulk & direct debits (NACH, APBS)'
               WHEN code = '6'                                           THEN 'Cheques'
               WHEN code = '5'                                           THEN 'Prepaid wallets & cards'
               ELSE 'Other'
           END AS category
    FROM stg_payments
    WHERE code IN ('1', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                   '3.1', '3.2', '3.3', '3.4', '4.1', '4.2', '5', '6')
)
SELECT *,
       ROUND(100 * volume_bn     / SUM(volume_bn)     OVER (PARTITION BY fy_start), 2)        AS share_of_volume_pct,
       ROUND(100 * value_lakh_cr / SUM(value_lakh_cr) OVER (PARTITION BY fy_start), 2)        AS share_of_value_pct,
       ROUND(value_lakh_cr * 1e12 / NULLIF(volume_bn * 1e9, 0))                               AS avg_ticket_rupees,
       ROUND(100 * (volume_bn / NULLIF(LAG(volume_bn) OVER s, 0) - 1), 1)                     AS volume_growth_pct,
       RANK() OVER (PARTITION BY fy_start ORDER BY volume_bn DESC)                            AS volume_rank
FROM leaves
WINDOW s AS (PARTITION BY system ORDER BY fy_start)
ORDER BY fy_start, volume_bn DESC;
