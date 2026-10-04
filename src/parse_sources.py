"""Parse the raw RBI / World Bank / Wikipedia files into tidy CSVs (data/staging/).

RBI Handbook of Statistics on the Indian Economy (2025-26 edition, downloaded manually because
rbidocs.rbi.org.in blocks scripted downloads):
  Table 1    Macro-economic aggregates at current prices  -> gdp_rbi.csv
  Table 36   Components of money stock, annual           -> cash_annual.csv
  Table 58   Payment system indicators, annual           -> payments_annual.csv
  Table 165  Components of money stock, monthly          -> cash_monthly.csv
World Bank API: GDP (current LCU) and population         -> gdp_worldbank.csv, population.csv
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, STAGING = ROOT / "data" / "raw", ROOT / "data" / "staging"
STAGING.mkdir(parents=True, exist_ok=True)

MONEY_COLS = ["cic", "cash_with_banks", "currency_with_public", "other_deposits_rbi", "bankers_deposits_rbi",
              "demand_deposits", "time_deposits", "reserve_money", "m1", "m3"]
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                      "August", "September", "October", "November", "December"], start=1)}


def fy_start(label):
    """'2022-23' -> 2022 (Indian financial years run April-March)."""
    return int(str(label)[:4])


def parse_cash_annual():
    t = pd.read_excel(RAW / "rbi_t36_money_stock_annual.xlsx", header=None).iloc[:, 1:12]
    t.columns = ["fiscal_year"] + MONEY_COLS
    t = t[t.fiscal_year.astype(str).str.match(r"^\d{4}-\d{2}$")].copy()
    t.insert(1, "fy_start", t.fiscal_year.map(fy_start))
    t[MONEY_COLS] = t[MONEY_COLS].astype(float)          # ₹ crore, end-March (last reporting Friday)
    t.to_csv(STAGING / "cash_annual.csv", index=False)
    return t


def parse_cash_monthly():
    t = pd.read_excel(RAW / "rbi_t165_money_stock.xlsx", header=None).iloc[:, 1:12]
    t.columns = ["label"] + MONEY_COLS
    rows, fy = [], None
    for _, r in t.iterrows():
        label = str(r.label).strip()
        if re.match(r"^\d{4}-\d{2}$", label):
            fy = fy_start(label)
        elif label in MONTHS and fy is not None:
            m = MONTHS[label]
            rows.append({"month": pd.Timestamp(fy if m >= 4 else fy + 1, m, 1).date(),
                         **{c: float(r[c]) for c in MONEY_COLS}})
    out = pd.DataFrame(rows)
    out.to_csv(STAGING / "cash_monthly.csv", index=False)
    return out


def parse_payments():
    """Table 58 has two sheets (2021-22..2023-24 and 2024-25..2025-26), each with Volume/Value pairs."""
    frames = []
    for sheet in ("T_58(i)", "T_58(ii)"):
        t = pd.read_excel(RAW / "rbi_t58_payment_systems.xlsx", sheet_name=sheet, header=None)
        years = t.iloc[3].ffill().astype(str).str.strip()
        kinds = t.iloc[4]
        for _, r in t.iloc[5:].iterrows():
            item = str(r[1]).strip()
            if item in ("nan", "") or item.startswith(("Note", "Source", "(Continued)")) or re.match(r"^\d\.\s", item) and "  " in item:
                continue
            for col in range(2, t.shape[1]):
                if pd.isna(years[col]) or kinds[col] not in ("Volume", "Value"):
                    continue
                val = pd.to_numeric(r[col], errors="coerce")
                frames.append({"fiscal_year": years[col], "item": item, "measure": kinds[col].lower(), "amount": val})
    long = pd.DataFrame(frames)
    long = long[~long.item.str.startswith(("A.", "B.", "Retail Segment", "Notes"))]
    wide = long.pivot_table(index=["fiscal_year", "item"], columns="measure", values="amount", aggfunc="first").reset_index()
    wide.insert(1, "fy_start", wide.fiscal_year.map(fy_start))
    wide = wide.rename(columns={"volume": "volume_lakh", "value": "value_crore"})
    # system code: '2.7 UPI' -> '2.7'; totals keep their label
    wide["code"] = wide.item.str.extract(r"^(\d+(?:\.\d+)?)\.?\s")[0]
    wide["system"] = wide.item.str.replace(r"^\d+(?:\.\d+)?\.?\s*", "", regex=True).str.strip()
    wide.to_csv(STAGING / "payments_annual.csv", index=False)
    return wide


def parse_gdp_rbi():
    t = pd.read_excel(RAW / "rbi_t1_macro_current_prices.xlsx", header=None)
    years, bases = t.iloc[4], t.iloc[6].ffill()
    gdp = t[t[1].astype(str).str.strip() == "Gross Domestic Product"].iloc[0]
    pop = t[t[1].astype(str).str.startswith("Population")].iloc[0]
    rows = [{"fiscal_year": years[c], "fy_start": fy_start(years[c]),
             "base_year": re.search(r"(\d{4}-\d{2})", str(bases[c])).group(1),
             "gdp_crore": float(gdp[c]), "population_lakh": float(pop[c])} for c in range(2, t.shape[1])]
    out = pd.DataFrame(rows)
    out.to_csv(STAGING / "gdp_rbi.csv", index=False)
    return out


def parse_worldbank():
    for name, file, col in (("gdp_worldbank", "wb_gdp_current_lcu.json", "gdp_crore"),
                            ("population", "wb_population.json", "population")):
        j = json.loads((RAW / file).read_text())
        # World Bank reports India on its April-March fiscal year: '2020' = 2020-21 (checked against RBI Table 1)
        rows = [{"fy_start": int(r["date"]), "fiscal_year": f"{r['date']}-{str(int(r['date']) + 1)[2:]}",
                 col: r["value"] / 1e7 if col == "gdp_crore" else r["value"]} for r in j[1] if r["value"]]
        pd.DataFrame(rows).sort_values("fy_start").to_csv(STAGING / f"{name}.csv", index=False)


if __name__ == "__main__":
    a = parse_cash_annual()
    m = parse_cash_monthly()
    p = parse_payments()
    g = parse_gdp_rbi()
    parse_worldbank()
    print(f"cash annual: {len(a)} years ({a.fiscal_year.iloc[0]} to {a.fiscal_year.iloc[-1]})")
    print(f"cash monthly: {len(m)} months ({m.month.iloc[0]} to {m.month.iloc[-1]})")
    print(f"payments: {p.fiscal_year.nunique()} years x {p.item.nunique()} items")
    print(p[p.fy_start == 2025][["item", "code", "system", "volume_lakh", "value_crore"]].to_string())
    print(g.to_string())
