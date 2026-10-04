# Building the Power BI dashboard

Time: about 45–60 minutes. You'll end up with a 3-page report (`upi_cash_dashboard.pbix`) and three screenshots for the README and portfolio.

## 1. Load the data

1. Open **Power BI Desktop**, then **Get data → Text/CSV**. Load these six files from `data/marts/`:
   `cash_annual.csv`, `upi_annual.csv`, `payments.csv`, `cash_monthly.csv`, `cash_forecast.csv`, `cash_seasonality.csv`
2. In **Transform data (Power Query)**, check the column types:
   - `month` in `cash_monthly` and `cash_forecast`: **Date**
   - `fiscal_year`, `system`, `category`, `event`: **Text**
   - Everything else: **Decimal number** (`fy_start` and `month_num`: **Whole number**)
3. **Close & Apply**.

## 2. Model

1. **Modeling → New table**: paste `FiscalYear` and `Calendar` from [`measures.dax`](measures.dax).
2. Select `Calendar`, then **Table tools → Mark as date table**, using column `Date`.
3. In **Model view**, create these relationships, all *one-to-many* with single-direction filtering:
   - `FiscalYear[fy_start]` → `cash_annual[fy_start]`, `upi_annual[fy_start]`, `payments[fy_start]`
   - `Calendar[Date]` → `cash_monthly[month]`, `cash_forecast[month]`
4. **Modeling → New measure**: paste each measure from `measures.dax`. Set the formats: percentages for `Cash to GDP`, `UPI value to GDP`, `Share of payments`, `Cash growth` and `Cash YoY, monthly`; whole numbers with a thousands separator for `Average payment (₹)`.
5. **View → Themes → Browse for themes**: choose [`theme.json`](theme.json). This uses the same colors as the Python charts (blue for cash, orange for UPI).

## 3. Page 1: "The paradox"

| Visual | Fields |
|---|---|
| Text box (title) | **UPI won. So why is India holding more cash than ever?** |
| 4 × Card | `Cash, latest year` · `Cash to GDP, latest year` · `UPI value, latest year` · `UPI share, latest year` |
| Line chart | X: `FiscalYear[Fiscal year]`; Y: `Cash to GDP`, `UPI value to GDP` |
| Slicer (dropdown) | `FiscalYear[Fiscal year]` |
| Text box (insight) | *Cash has stayed near 12% of GDP since 2010-11, while UPI's yearly value grew from 37% to 91% of GDP.* |

Tips: sort the line chart's axis by `fy_start` (select `Fiscal year` → **Column tools → Sort by column → fy_start**). Turn on data labels for the last point only.

## 4. Page 2: "How India pays"

| Visual | Fields |
|---|---|
| 100% stacked column chart | X: `FiscalYear[Fiscal year]`; Legend: `payments[category]`; Y: `Share of payments` |
| Line chart | X: `FiscalYear[Fiscal year]`; Y: `Average payment (₹)`; Legend: `payments[system]`, with a visual filter of system = UPI, Debit Cards |
| Matrix | Rows: `payments[system]`; Columns: `FiscalYear[Fiscal year]`; Values: `volume_bn` (sum), `volume_growth_pct` (sum). Add **Conditional formatting → Data bars** on `volume_bn` |

## 5. Page 3: "Cash through the year"

| Visual | Fields |
|---|---|
| Line chart | X: `Calendar[Month]`; Y: `Cash, monthly (₹ lakh cr)`, `Forecast (₹ lakh cr)`. In **Analytics → Error bars**, set the Forecast line's upper bound to `Forecast high (80%)` and lower bound to `Forecast low (80%)`, using the *Area* style |
| Column chart | X: `cash_seasonality[month_name]` (sort by `month_num`); Y: `avg_mom_pct` |
| Card | `Forecast, May 2027` |
| Line chart (small) | X: `Calendar[Month]`; Y: `Cash YoY, monthly` |

## 6. Save and share

1. Save as `powerbi/upi_cash_dashboard.pbix`.
2. Screenshot each page with **Win + Shift + S** and save the files as `images/powerbi_1_paradox.png`, `images/powerbi_2_payments.png` and `images/powerbi_3_cash_monthly.png`.
3. Optional: **Publish** to Power BI Service and use **File → Embed report → Publish to web** for a public link you can add to your portfolio. Only do this with public data like this.
