import sqlite3
from pathlib import Path

V2_DIR = Path("/workspace/Lantern_V2/Lantern_V2")
SQL_DIR = V2_DIR / "matrix_queries"

COMPANIES = {
    "Apex Strategy Consulting": "service1",
    "Meridian Consulting Group": "service2",
    "Vertex Advisory Partners": "service3",
}

SQL_FILES = {
    "net_profit_margin":      "01_net_profit_margin.sql",
    "monthly_revenue_trend":  "02_monthly_revenue_trend.sql",
    "days_sales_outstanding": "03_days_sales_outstanding.sql",
    "client_concentration":   "04_client_concentration.sql",
    "burn_rate_runway":       "05_burn_rate_runway.sql",
    "expense_breakdown":      "06_expense_breakdown.sql",
    "revenue_per_employee":   "07_revenue_per_employee.sql",
    "client_churn_rate":      "08_client_churn_rate.sql",
}

def list_companies():
    return list(COMPANIES.keys())

def get_metric(company, metric):
    if company not in COMPANIES:
        return f"Unknown company. Choose from: {list(COMPANIES)}"
    if metric not in SQL_FILES:
        return f"Uknown company. Choose from: {list(SQL_FILES)}"

    db_path = V2_DIR / "databases" / f"{COMPANIES[company]}.db"
    sql = (SQL_DIR / SQL_FILES[metric]).read_text(encoding="utf-8")

    #Read only connections: writes fail at the databse level
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

if __name__ == "__main__":
    print(list_companies())
    print(get_metric("Vertex Advisory Partners", "client_concentration"))
