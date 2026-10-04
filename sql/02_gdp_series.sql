-- One consistent nominal GDP series, 2010-11 to 2025-26.
-- India moved its GDP base year from 2011-12 to 2022-23. RBI publishes 2022-23 on both bases,
-- so older years are rescaled by (new / old) for that overlap year to avoid a fake jump in ratios.

CREATE OR REPLACE TABLE gdp_series AS
WITH splice AS (
    SELECT MAX(gdp_crore) FILTER (WHERE base_year = '2022-23')
         / MAX(gdp_crore) FILTER (WHERE base_year = '2011-12') AS factor
    FROM stg_gdp_rbi
    WHERE fy_start = 2022
),
old_base AS (
    -- World Bank for early years; RBI Table 1 where it is available on the old base
    SELECT fy_start, gdp_crore, 'World Bank (rescaled)' AS source
    FROM stg_gdp_worldbank
    WHERE fy_start < 2020
    UNION ALL
    SELECT fy_start, gdp_crore, 'RBI Table 1 (rescaled)'
    FROM stg_gdp_rbi
    WHERE base_year = '2011-12' AND fy_start IN (2020, 2021)
),
new_base AS (
    SELECT fy_start, gdp_crore, 'RBI Table 1' AS source
    FROM stg_gdp_rbi
    WHERE base_year = '2022-23'
)
SELECT o.fy_start, o.gdp_crore * s.factor / 1e5 AS gdp_lakh_cr, o.source, s.factor AS splice_factor
FROM old_base o CROSS JOIN splice s
UNION ALL
SELECT fy_start, gdp_crore / 1e5, source, NULL
FROM new_base
ORDER BY fy_start;
