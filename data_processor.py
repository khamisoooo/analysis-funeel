"""
GA4 BI Data Processor
Cleans and aggregates raw GA4 product-level CSV into analysis-ready DataFrames.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "ga4_data.csv"


# ─────────────────────────────────────────────
# 1. Load & Clean
# ─────────────────────────────────────────────
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")

    # Rename columns to snake_case
    df.columns = [
        "sku", "parent_sku", "seller_type", "lang_code", "item_name",
        "category", "views", "cart", "checkout", "orders", "qty",
        "revenue", "cvr_orders"
    ]

    # Coerce numerics
    num_cols = ["views", "cart", "checkout", "orders", "qty", "revenue", "cvr_orders"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    # Derived fields
    df["aov"] = np.where(df["orders"] > 0, df["revenue"] / df["orders"], 0)
    df["cart_rate"]     = np.where(df["views"] > 0, df["cart"]     / df["views"], 0)
    df["checkout_rate"] = np.where(df["views"] > 0, df["checkout"] / df["views"], 0)
    df["order_rate"]    = np.where(df["views"] > 0, df["orders"]   / df["views"], 0)

    return df


# ─────────────────────────────────────────────
# 2. KPI Summary
# ─────────────────────────────────────────────
def kpi_summary(df: pd.DataFrame) -> dict:
    total_views    = df["views"].sum()
    total_cart     = df["cart"].sum()
    total_checkout = df["checkout"].sum()
    total_orders   = df["orders"].sum()
    total_revenue  = df["revenue"].sum()
    total_qty      = df["qty"].sum()

    return {
        "total_revenue":    round(total_revenue, 2),
        "total_orders":     int(total_orders),
        "total_views":      int(total_views),
        "total_cart":       int(total_cart),
        "total_checkout":   int(total_checkout),
        "total_qty":        int(total_qty),
        "aov":              round(total_revenue / total_orders, 2) if total_orders else 0,
        "cvr_view_order":   round(total_orders / total_views * 100, 3) if total_views else 0,
        "cvr_view_cart":    round(total_cart / total_views * 100, 2) if total_views else 0,
        "cvr_cart_checkout":round(total_checkout / total_cart * 100, 2) if total_cart else 0,
        "cvr_checkout_order":round(total_orders / total_checkout * 100, 2) if total_checkout else 0,
        "skus_total":       len(df),
        "skus_with_revenue":int((df["revenue"] > 0).sum()),
    }


# ─────────────────────────────────────────────
# 3. Category Aggregation
# ─────────────────────────────────────────────
def category_agg(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    g = df.groupby("category", as_index=False).agg(
        revenue=("revenue", "sum"),
        orders=("orders", "sum"),
        views=("views", "sum"),
        cart=("cart", "sum"),
        checkout=("checkout", "sum"),
        qty=("qty", "sum"),
        sku_count=("sku", "count"),
    )
    g["aov"]          = (g["revenue"] / g["orders"]).replace([np.inf, np.nan], 0).round(0)
    g["cvr_pct"]      = (g["orders"] / g["views"] * 100).replace([np.inf, np.nan], 0).round(3)
    g["cart_rate_pct"]= (g["cart"] / g["views"] * 100).replace([np.inf, np.nan], 0).round(2)
    g["rev_share_pct"]= (g["revenue"] / g["revenue"].sum() * 100).round(2)
    g = g.sort_values("revenue", ascending=False)
    return g.head(top_n).reset_index(drop=True)


# ─────────────────────────────────────────────
# 4. Seller Type Aggregation
# ─────────────────────────────────────────────
def seller_agg(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("seller_type", as_index=False).agg(
        revenue=("revenue", "sum"),
        orders=("orders", "sum"),
        views=("views", "sum"),
        cart=("cart", "sum"),
        checkout=("checkout", "sum"),
        sku_count=("sku", "count"),
    )
    g["aov"]     = (g["revenue"] / g["orders"]).replace([np.inf, np.nan], 0).round(0)
    g["cvr_pct"] = (g["orders"] / g["views"] * 100).replace([np.inf, np.nan], 0).round(3)
    g["rev_share_pct"] = (g["revenue"] / g["revenue"].sum() * 100).round(1)
    return g


# ─────────────────────────────────────────────
# 5. Language Aggregation
# ─────────────────────────────────────────────
def lang_agg(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("lang_code", as_index=False).agg(
        revenue=("revenue", "sum"),
        orders=("orders", "sum"),
        views=("views", "sum"),
    )
    g["aov"]           = (g["revenue"] / g["orders"]).replace([np.inf, np.nan], 0).round(0)
    g["cvr_pct"]       = (g["orders"] / g["views"] * 100).replace([np.inf, np.nan], 0).round(3)
    g["rev_share_pct"] = (g["revenue"] / g["revenue"].sum() * 100).round(1)
    return g.sort_values("revenue", ascending=False)


# ─────────────────────────────────────────────
# 6. Funnel DataFrame
# ─────────────────────────────────────────────
def funnel_df(df: pd.DataFrame) -> pd.DataFrame:
    kpi = kpi_summary(df)
    steps = [
        ("Views",       kpi["total_views"],    100.0),
        ("Add to Cart", kpi["total_cart"],      round(kpi["total_cart"]     / kpi["total_views"] * 100, 2)),
        ("Checkout",    kpi["total_checkout"],  round(kpi["total_checkout"]  / kpi["total_views"] * 100, 2)),
        ("Orders",      kpi["total_orders"],    round(kpi["total_orders"]    / kpi["total_views"] * 100, 3)),
    ]
    fdf = pd.DataFrame(steps, columns=["stage", "count", "pct_of_views"])
    fdf["drop_pct"] = [0] + [
        round((1 - fdf["count"].iloc[i] / fdf["count"].iloc[i - 1]) * 100, 1)
        for i in range(1, len(fdf))
    ]
    return fdf


# ─────────────────────────────────────────────
# 7. Top Products
# ─────────────────────────────────────────────
def top_products(df: pd.DataFrame, by: str = "revenue", top_n: int = 20) -> pd.DataFrame:
    cols = ["sku", "item_name", "category", "seller_type", "lang_code",
            "views", "cart", "checkout", "orders", "revenue", "aov", "cvr_orders"]
    valid = [c for c in cols if c in df.columns]
    out = df[valid].copy()
    out = out[out["revenue"] > 0].sort_values(by, ascending=False).head(top_n)
    return out.reset_index(drop=True)


# ─────────────────────────────────────────────
# 8. CVR Segments
# ─────────────────────────────────────────────
def cvr_segments(cat_df: pd.DataFrame) -> pd.DataFrame:
    """Label categories by CVR tier."""
    def tier(cvr):
        if cvr >= 1.0:   return "🟢 High (≥1%)"
        if cvr >= 0.5:   return "🟡 Medium (0.5–1%)"
        if cvr >= 0.25:  return "🟠 Low (0.25–0.5%)"
        return "🔴 Very Low (<0.25%)"

    out = cat_df.copy()
    out["cvr_tier"] = out["cvr_pct"].apply(tier)
    return out


# ─────────────────────────────────────────────
# CLI: print a quick summary
# ─────────────────────────────────────────────
if __name__ == "__main__":
    df = load_data()
    kpi = kpi_summary(df)

    print("\n" + "=" * 50)
    print("  GA4 BI — QUICK SUMMARY")
    print("=" * 50)
    for k, v in kpi.items():
        label = k.replace("_", " ").upper()
        if "revenue" in k or "aov" in k:
            print(f"  {label:<30} EGP {v:>15,.2f}")
        elif isinstance(v, float):
            print(f"  {label:<30} {v:>15.3f}%")
        else:
            print(f"  {label:<30} {v:>15,}")
    print("=" * 50)

    print("\nTop 5 Categories by Revenue:")
    cat = category_agg(df, top_n=5)
    print(cat[["category", "revenue", "orders", "cvr_pct", "aov"]].to_string(index=False))

    print("\nFunnel:")
    print(funnel_df(df).to_string(index=False))
