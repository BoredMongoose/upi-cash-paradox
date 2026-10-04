"""Run the SQL models in order, enforce the data-quality checks, export marts for Power BI."""
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"


def main():
    os.chdir(ROOT)                      # SQL files use paths relative to the project root
    MARTS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "upi_cash.duckdb"))
    con.execute("SET threads = 1")   # same order and sums every run, so re-running reproduces the marts exactly
    for sql_file in sorted((ROOT / "sql").glob("*.sql")):
        con.execute(sql_file.read_text(encoding="utf-8"))
        print("ran", sql_file.name)

    dq = con.execute("SELECT * FROM dq_results ORDER BY passed, check_name").df()
    print(dq.to_string(index=False))
    failed = dq[~dq.passed]
    if len(failed):
        raise SystemExit(f"{len(failed)} data-quality check(s) failed - fix before using the marts")

    for table in ("mart_cash_annual", "mart_payments", "mart_upi_annual", "mart_cash_monthly", "mart_cash_seasonality"):
        con.execute(f"COPY {table} TO '{(MARTS / table.removeprefix('mart_')).as_posix()}.csv' (HEADER)")
    print("marts exported to", MARTS)


if __name__ == "__main__":
    main()
