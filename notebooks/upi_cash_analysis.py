# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # UPI won. So why is India holding more cash than ever?
#
# In 2025-26 Indians made **242 billion UPI payments** worth ₹314 lakh crore. Over the same year,
# the cash in circulation grew **11.8% to a record ₹41.7 lakh crore**, its fastest growth since COVID.
# If UPI is replacing cash, why does India keep printing more of it?
#
# **Short answer:**
# 1. **Relative to the economy, cash hasn't grown or shrunk.** It's **12.0% of GDP**, exactly where it was in
#    2014-15, before UPI existed. It ranged 11.9–12.8% in the six years before demonetisation and
#    11.7–12.1% in the last three. Each shock (demonetisation, COVID) pushed it away for a few years, and it
#    came back. Cash rises because the economy does.
# 2. **UPI replaced cash as a way to *pay*, not as a way to *hold* money.** UPI's yearly value grew from 37% to
#    91% of GDP in four years, and the average UPI payment fell from ₹1,831 to ₹1,301. That's small,
#    everyday spending that used to be cash. Debit-card payments at shops fell 67%.
# 3. **Cash behaves like savings.** It jumped when the economy shrank (COVID), and it builds up every
#    October–May and drains every June–September.
#
# Data: RBI Handbook of Statistics (Tables 1, 36, 58, 165), World Bank. All modelling is in SQL (DuckDB):
# see `sql/`. Run `python src/parse_sources.py && python src/run_sql.py` first.

# %%
import sys
import warnings
from pathlib import Path

import duckdb
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

# the notebook is in the notebooks/ folder, so the project folder is one level up
ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent

# my chart colours and helpers (titles, footnote, save) are in src/style.py
sys.path.append(str(ROOT / "src"))
from style import AQUA, BLUE, BLUE_LIGHT, INK, INK_2, MAGENTA, NEUTRAL, ORANGE, VIOLET, footnote, save, titles

# src/run_sql.py builds all the tables in this DuckDB database
con = duckdb.connect(str(ROOT / "data" / "upi_cash.duckdb"), read_only=True)


def run_sql(query):
    """Run a SQL query on the database and return the result as a pandas DataFrame."""
    return con.execute(query).df()


pd.set_option("display.precision", 2)

# %% [markdown]
# ## 1. Data-quality checks
#
# The pipeline won't publish if any check fails. One check compares two RBI tables against each other: the
# March value in the monthly series must equal the annual (end-March) figure.

# %%
run_sql("SELECT check_name, detail, passed FROM dq_results ORDER BY check_name, detail")

# %% [markdown]
# ## 2. The paradox in one query

# %%
run_sql("""
    SELECT c.fiscal_year,
           c.cash_lakh_cr,
           c.cash_growth_pct,
           c.cash_to_gdp_pct,
           u.upi_txns_bn,
           u.upi_value_lakh_cr,
           u.upi_value_to_gdp_pct
    FROM mart_cash_annual c
    LEFT JOIN mart_upi_annual u USING (fy_start)
    WHERE c.fy_start IN (2014, 2015, 2021, 2022, 2023, 2024, 2025)
    ORDER BY c.fy_start
""")

# %%
# Chart 1: cash held vs UPI payments, both as % of GDP
cash = run_sql("SELECT * FROM mart_cash_annual ORDER BY fy_start")
upi = run_sql("SELECT * FROM mart_upi_annual ORDER BY fy_start")
cash_latest = cash["cash_to_gdp_pct"].iloc[-1]
upi_first = upi["upi_value_to_gdp_pct"].iloc[0]
upi_latest = upi["upi_value_to_gdp_pct"].iloc[-1]

fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(cash["fy_start"], cash["cash_to_gdp_pct"], color=BLUE, lw=2.5, marker="o", ms=5)
ax.plot(upi["fy_start"], upi["upi_value_to_gdp_pct"], color=ORANGE, lw=2.5, marker="o", ms=6)
ax.text(2025.25, cash_latest, f"Cash held\n{cash_latest:.0f}% of GDP", color=BLUE, fontsize=10.5, va="center",
        fontweight="bold")
ax.text(2025.25, upi_latest, f"UPI payments\n{upi_latest:.0f}% of GDP", color=ORANGE, fontsize=10.5, va="center",
        fontweight="bold")
ax.text(2021, upi_first + 6, f"{upi_first:.0f}%", color=ORANGE, ha="center")
ax.axvline(2016, color=INK_2, lw=0.8, ls=":")
ax.text(2016.1, 60, "UPI launched (Apr 2016)", color=INK_2, fontsize=9.5)
ax.set_xticks(cash["fy_start"][::2], cash["fiscal_year"][::2])     # label every other year
ax.set_xlim(2009.6, 2027.2)
ax.set_ylim(0, 100)
ax.set_ylabel("% of GDP")
titles(ax, "UPI exploded. Cash didn't shrink.",
       "Yearly value of UPI payments, and cash in circulation (end of March), both as a share of nominal GDP")
footnote(fig, "Data: RBI Handbook of Statistics (Tables 1, 36, 58), World Bank. GDP before 2022-23 rescaled to the new 2022-23 base.", y=-0.03)
save(fig, "01_upi_vs_cash.png")
plt.show()

# %% [markdown]
# ## 3. Cash keeps returning to about 12% of GDP
#
# The two exceptions are both shocks to *trust and liquidity*, not to payment habits. Demonetisation
# (Nov 2016) mechanically removed 86% of notes. COVID (2020-21) made households hoard cash while GDP fell.

# %%
# Chart 2: cash as % of GDP, with the normal range shaded and the shocks labelled
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.fill_between(cash["fy_start"], 11.7, 12.8, color=BLUE_LIGHT, alpha=0.6, lw=0)
ax.text(2010.1, 12.95, "range before 2016 and since 2023: 11.7–12.8%", color=BLUE, fontsize=9.5)
ax.plot(cash["fy_start"], cash["cash_to_gdp_pct"], color=BLUE, lw=2.5, marker="o", ms=5)

# (year, label, where the label goes relative to the point)
notes = [
    (2016, "Demonetisation\n8.9%", (0, -38)),
    (2020, "COVID hoarding\n14.8%", (0, 14)),
    (2023, "₹2000 notes\nwithdrawn", (0, -42)),
]
cash_by_year = cash.set_index("fy_start")["cash_to_gdp_pct"]
for year, label, offset in notes:
    ax.annotate(label, (year, cash_by_year[year]), xytext=offset, textcoords="offset points", ha="center",
                fontsize=9.5, arrowprops=dict(arrowstyle="-", color=INK_2))

ax.set_xticks(cash["fy_start"][::2], cash["fiscal_year"][::2])
ax.set_ylim(7, 16)
ax.set_ylabel("Cash in circulation, % of GDP")
titles(ax, "A decade of digital payments, and cash is still 12% of GDP",
       "Currency in circulation (end of March) as a share of that year's nominal GDP")
footnote(fig, "Data: RBI Handbook of Statistics (Tables 1, 36), World Bank.", y=-0.03)
save(fig, "02_cash_to_gdp.png")
plt.show()

# %% [markdown]
# ## 4. What UPI actually replaced
#
# UPI's share of non-cash payments rose from 63% to 86% in four years. Most of that came from other
# *digital* channels. Debit cards at shops collapsed, and the average UPI payment keeps getting smaller.

# %%
# Chart 3: share of non-cash transactions by payment system, stacked to 100%
mix_long = run_sql("""
    SELECT fiscal_year,
           CASE WHEN category IN ('UPI', 'Bank transfers (RTGS, NEFT, IMPS)', 'Prepaid wallets & cards', 'Cards')
                THEN category ELSE 'Everything else' END AS category,
           SUM(share_of_volume_pct) AS share_pct
    FROM mart_payments
    GROUP BY 1, 2          -- 1, 2 = the first two columns (the year and the grouped category)
    ORDER BY fiscal_year
""")
mix = mix_long.pivot(index="fiscal_year", columns="category", values="share_pct")

categories = ["UPI", "Bank transfers (RTGS, NEFT, IMPS)", "Prepaid wallets & cards", "Cards", "Everything else"]
colours = [ORANGE, AQUA, VIOLET, MAGENTA, NEUTRAL]

fig, ax = plt.subplots(figsize=(11, 5.8))
bottom = np.zeros(len(mix))
for category, colour in zip(categories, colours):
    values = mix[category].values
    ax.bar(mix.index, values, bottom=bottom, color=colour, width=0.62, edgecolor="#fcfcfb", linewidth=2,
           label=category)

    # label the segments that are big enough to read (white text on the dark colours)
    if category in ["UPI", "Prepaid wallets & cards"]:
        text_colour = "white"
    else:
        text_colour = INK
    for x in range(len(values)):
        if values[x] >= 4:
            ax.text(x, bottom[x] + values[x] / 2, f"{values[x]:.0f}%", ha="center", va="center", fontsize=10,
                    color=text_colour)
    bottom = bottom + values

ax.set_ylim(0, 100)
ax.set_yticks([])
ax.grid(False)
ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
titles(ax, "UPI now handles 86% of India's non-cash payments",
       "Share of the number of non-cash transactions, by payment system")
footnote(fig, "Data: RBI Handbook of Statistics, Table 58 (Payment System Indicators). Excludes CCIL settlement systems.", y=-0.03)
save(fig, "03_payment_mix.png")
plt.show()

# %%
# Chart 4: average payment size, UPI vs debit cards
tickets = run_sql("""
    SELECT fiscal_year, system, avg_ticket_rupees, volume_bn
    FROM mart_payments
    WHERE system IN ('UPI', 'Debit Cards')
    ORDER BY fiscal_year
""")
display(tickets.pivot(index="fiscal_year", columns="system", values=["volume_bn", "avg_ticket_rupees"]))

# (system, colour, label, how far to nudge the first value's label up or down)
# the two series start almost level, so their first labels are nudged apart
lines = [
    ("UPI", ORANGE, "UPI", -110),
    ("Debit Cards", AQUA, "Debit cards (at shops & online)", 110),
]
fig, ax = plt.subplots(figsize=(10, 5.5))
for system, colour, label, nudge in lines:
    rows = tickets[tickets["system"] == system]
    first_value = rows["avg_ticket_rupees"].iloc[0]
    last_value = rows["avg_ticket_rupees"].iloc[-1]
    ax.plot(rows["fiscal_year"], rows["avg_ticket_rupees"], color=colour, lw=2.5, marker="o", ms=7)
    ax.text(4.12, last_value, f"{label}\n₹{last_value:,.0f}", color=colour, fontsize=10.5, va="center",
            fontweight="bold")
    ax.text(-0.12, first_value + nudge, f"₹{first_value:,.0f}", color=colour, fontsize=10, ha="right", va="center")

ax.set_xlim(-0.6, 5.2)
ax.set_ylim(0, 4000)
ax.set_ylabel("Average payment (₹)")
titles(ax, "UPI took the small payments, the ones cash used to handle",
       "Average value per transaction. Debit-card volumes fell 67% as small purchases moved to UPI")
footnote(fig, "Data: RBI Handbook of Statistics, Table 58.", y=-0.03)
save(fig, "04_ticket_size.png")
plt.show()

# %% [markdown]
# ## 5. When India reaches for cash
#
# Monthly data (April 2022 – May 2026) shows a strong seasonal rhythm. Cash builds from October (festivals,
# weddings) through May (financial year-end, rabi harvest), then drains through the monsoon. The withdrawal
# of ₹2000 notes in May 2023 pulled cash down sharply as notes were deposited back into banks.

# %%
monthly = run_sql("SELECT * FROM mart_cash_monthly ORDER BY month")
seasonal = run_sql("SELECT * FROM mart_cash_seasonality ORDER BY month_num")
seasonal

# %% [markdown]
# ## 6. Forecast: how much cash will India need through Diwali 2026?
#
# The RBI has to print notes months in advance, so forecasting cash demand is a real operational problem.
# Three models are compared with a **rolling-origin backtest**: for each of 25 start months, each model is
# fitted on the history up to that point and forecasts 1–6 months ahead.

# %%
# monthly cash on a log scale (so the models work with growth rates)
y = np.log(monthly.set_index("month")["cash_lakh_cr"])
y.index = pd.DatetimeIndex(y.index, freq="MS")


def naive(train, h):
    """Every future month = the last month."""
    return np.repeat(train.iloc[-1], h)


def seasonal_naive_drift(train, h):
    """Same month last year, plus last year's growth."""
    drift = train.iloc[-1] - train.iloc[-13]
    forecasts = []
    for i in range(h):
        forecasts.append(train.iloc[-12 + i] + drift)
    return np.array(forecasts)


def holt_winters(train, h):
    """Holt-Winters: a trend plus a repeating 12-month pattern."""
    model = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=12)
    fit = model.fit()
    return fit.forecast(h).values


models = {"Naive (last value)": naive, "Seasonal naive + drift": seasonal_naive_drift, "Holt-Winters": holt_winters}

# for each start month: fit on everything before it, forecast the next 6 months, and record the errors
rows = []
for end in range(24, len(y) - 1):            # at least two years of history before the first forecast
    train = y.iloc[:end]
    test = y.iloc[end:end + 6]
    for name, model in models.items():
        predictions = model(train, len(test))
        for h in range(len(test)):
            actual = np.exp(test.values[h])          # back from the log scale to ₹ lakh crore
            predicted = np.exp(predictions[h])
            error_pct = (predicted / actual - 1) * 100
            rows.append({"model": name, "months ahead": h + 1, "abs % error": abs(error_pct), "% error": error_pct})
backtest = pd.DataFrame(rows)

summary = backtest.pivot_table(index="model", columns="months ahead", values="abs % error")
summary["average"] = backtest.groupby("model")["abs % error"].mean()
summary["bias"] = backtest.groupby("model")["% error"].mean()
summary.round(2)

# %% [markdown]
# Holt-Winters wins, with an average error of about 1.1%. Every model is biased slightly low (about −1%),
# because cash growth sped up from ~4% a year in 2023 to ~12% in 2026. The forecast below uses
# Holt-Winters (an ETS model with additive trend and seasonality on the log scale) with an 80% prediction
# interval.

# %%
# fit the model on all the data and forecast 12 months, with an 80% interval
ets = ETSModel(y, error="add", trend="add", seasonal="add", seasonal_periods=12)
ets_fit = ets.fit(disp=False)
prediction = ets_fit.get_prediction(start=len(y), end=len(y) + 11).summary_frame(alpha=0.2)

forecast = pd.DataFrame()
forecast["forecast"] = np.exp(prediction["mean"])        # back from the log scale
forecast["low_80"] = np.exp(prediction["pi_lower"])
forecast["high_80"] = np.exp(prediction["pi_upper"])
forecast.index = pd.date_range(y.index[-1] + pd.offsets.MonthBegin(), periods=12, freq="MS")

forecast.to_csv(ROOT / "data" / "marts" / "cash_forecast.csv", index_label="month")
forecast.round(2)

# %%
# Chart 5: monthly cash with the 12-month forecast
cash_by_month = monthly.set_index("month")["cash_lakh_cr"]
may_2027 = forecast.loc["2027-05-01"]
change_from_may_2026 = may_2027["forecast"] / monthly["cash_lakh_cr"].iloc[-1] - 1

fig, ax = plt.subplots(figsize=(11.5, 5.8))
ax.plot(monthly["month"], monthly["cash_lakh_cr"], color=BLUE, lw=2.5, label="Cash in circulation")
ax.fill_between(forecast.index, forecast["low_80"], forecast["high_80"], color=BLUE_LIGHT, lw=0,
                label="80% prediction interval")

# the dashed forecast line starts from the last real month
forecast_x = [monthly["month"].iloc[-1]] + list(forecast.index)
forecast_y = [monthly["cash_lakh_cr"].iloc[-1]] + list(forecast["forecast"])
ax.plot(forecast_x, forecast_y, color=BLUE, lw=2, ls="--", label="Forecast")

events = {"2023-06-01": "₹2000 notes\nwithdrawn", "2024-04-01": "General\nelection", "2026-11-01": "Diwali 2026\n(forecast)"}
for date, label in events.items():
    month = pd.Timestamp(date)
    if month in forecast.index:
        value = forecast.loc[month, "forecast"]
    else:
        value = cash_by_month[month]
    if "withdrawn" in label:
        offset = (0, -46)     # below the line
    else:
        offset = (0, 26)      # above the line
    ax.annotate(label, (month, value), xytext=offset, textcoords="offset points", ha="center", fontsize=9.5,
                arrowprops=dict(arrowstyle="-", color=INK_2))

ax.text(forecast.index[-1], may_2027["forecast"] + 2.2,
        f"May 2027:\n₹{may_2027['forecast']:.1f} lakh cr\n(₹{may_2027['low_80']:.1f}–{may_2027['high_80']:.1f})",
        ha="center", fontsize=9.5, color=BLUE)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.set_ylabel("₹ lakh crore")
ax.legend(loc="upper left")
titles(ax, f"Cash in circulation is forecast to reach ₹{may_2027['forecast']:.0f} lakh crore by May 2027",
       f"Monthly currency in circulation, with a Holt-Winters forecast ({change_from_may_2026:+.0%} on May 2026)")
footnote(fig, "Data: RBI Handbook of Statistics, Table 165. Backtest error ~1.1% (1–6 months ahead), biased slightly low.", y=-0.04)
save(fig, "05_cash_forecast.png")
plt.show()

# %% [markdown]
# ## 7. A simple projection: will UPI move more money than India's GDP?
#
# In 2025-26 UPI's yearly value reached 90.7% of GDP. If UPI and the economy keep 2025-26's growth rates,
# UPI crosses 100% of GDP in 2026-27. These are scenarios, not a model.

# %%
# the latest year's UPI value, GDP, and growth rates
latest = run_sql("""
    SELECT u.upi_value_lakh_cr,
           u.gdp_lakh_cr,
           100 * (u.upi_value_lakh_cr / LAG(u.upi_value_lakh_cr) OVER (ORDER BY fy_start) - 1) AS upi_value_growth_pct,
           c.gdp_growth_pct
    FROM mart_upi_annual u
    JOIN mart_cash_annual c USING (fy_start)
    ORDER BY fy_start DESC
    LIMIT 1
""").iloc[0]

scenarios = pd.DataFrame({
    "UPI value growth": [0.15, latest["upi_value_growth_pct"] / 100, 0.25],
    "nominal GDP growth": [0.10, latest["gdp_growth_pct"] / 100, 0.08],
}, index=["Slower UPI", "Same pace as 2025-26", "Faster UPI"])

upi_next_year = latest["upi_value_lakh_cr"] * (1 + scenarios["UPI value growth"])
gdp_next_year = latest["gdp_lakh_cr"] * (1 + scenarios["nominal GDP growth"])
scenarios["UPI value / GDP, 2026-27"] = (100 * upi_next_year / gdp_next_year).round(1)
scenarios

# %% [markdown]
# ## Limitations
#
# - **Stocks against flows.** Cash in circulation is a stock (measured at end-March) and UPI value is a flow
#   (summed over the year). Both are shown as a share of GDP, but they measure different things.
#   Comparing them shows how each has grown, not that one equals the other.
# - **There's no direct measure of cash *use*** (such as ATM withdrawals) in these tables. "UPI replaced small cash
#   payments" is inferred from falling ticket sizes and collapsing debit-card volumes, not measured directly.
# - **UPI data starts in 2021-22**, the first year in RBI's current handbook table. Earlier figures exist (NPCI)
#   but come from a different source, so they're left out.
# - **The forecast has only four years of monthly history**, and the backtest shows it tends to under-predict when
#   cash growth speeds up.
