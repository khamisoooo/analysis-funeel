"""
GA4 BI Dashboard — Streamlit App
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_processor import (
    load_data, kpi_summary, category_agg,
    seller_agg, lang_agg, funnel_df, top_products, cvr_segments
)

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GA4 BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Theme / CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono&display=swap');

  html, body, [class*="css"] {
      font-family: 'Syne', sans-serif;
      background-color: #0A0F1C;
      color: #E2E8F0;
  }
  .metric-card {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 14px;
      padding: 18px 22px;
  }
  .metric-label {
      font-size: 11px;
      color: #64748B;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      font-family: 'DM Mono', monospace;
  }
  .metric-value {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.02em;
  }
  .metric-sub {
      font-size: 12px;
      color: #475569;
      margin-top: 2px;
  }
  [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 800 !important; }
  [data-testid="stMetricLabel"] { font-size: 11px !important; color: #64748B !important; }
  div[data-testid="stSidebarNav"] { display: none; }
  .stTabs [data-baseweb="tab-list"] { gap: 6px; }
  .stTabs [data-baseweb="tab"] {
      background: rgba(255,255,255,0.04);
      border-radius: 8px;
      padding: 6px 18px;
      border: none !important;
      color: #64748B;
      font-size: 12px;
      font-weight: 600;
  }
  .stTabs [aria-selected="true"] {
      background: #F97316 !important;
      color: white !important;
  }
  h1, h2, h3 { font-family: 'Syne', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Plotly dark theme helper
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="DM Mono, monospace", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False, color="#475569"),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, color="#475569"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
)
ORANGE_SEQ = px.colors.sequential.Oranges
BLUE_SEQ   = px.colors.sequential.Blues
CAT_COLORS = px.colors.qualitative.Vivid

def apply_theme(fig, **kwargs):
    layout = {**PLOT_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig


# ─────────────────────────────────────────────
# Load data (cached)
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data…")
def get_data():
    df  = load_data()
    kpi = kpi_summary(df)
    cat = category_agg(df, top_n=20)
    sel = seller_agg(df)
    lng = lang_agg(df)
    fun = funnel_df(df)
    top = top_products(df, top_n=50)
    cvr = cvr_segments(cat)
    return df, kpi, cat, sel, lng, fun, top, cvr

df, kpi, cat, sel, lng, fun, top, cvr = get_data()


# ─────────────────────────────────────────────
# Sidebar — filters
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 GA4 BI Dashboard")
    st.markdown("---")

    # Seller filter
    seller_opts = ["All"] + list(df["seller_type"].unique())
    seller_sel  = st.selectbox("Seller Type", seller_opts)

    # Language filter
    lang_opts = ["All"] + list(df["lang_code"].unique())
    lang_sel  = st.selectbox("Language", lang_opts)

    # Category filter (top 20)
    top_cats   = cat["category"].tolist()
    cat_sel    = st.multiselect("Categories (top 20)", top_cats, default=top_cats[:10])

    st.markdown("---")
    st.markdown(f"**Total SKUs:** {kpi['skus_total']:,}")
    st.markdown(f"**SKUs w/ Revenue:** {kpi['skus_with_revenue']:,}")
    st.markdown(f"**Categories:** {df['category'].nunique()}")
    st.markdown("---")
    st.caption("Data: GA4 Export · May 2026")

# Apply sidebar filters to raw df for any filtered views
filtered_df = df.copy()
if seller_sel != "All":
    filtered_df = filtered_df[filtered_df["seller_type"] == seller_sel]
if lang_sel != "All":
    filtered_df = filtered_df[filtered_df["lang_code"] == lang_sel]

# Recompute aggregations on filtered df
f_kpi = kpi_summary(filtered_df)
f_cat = category_agg(filtered_df, top_n=20)
if cat_sel:
    f_cat = f_cat[f_cat["category"].isin(cat_sel)]
f_fun = funnel_df(filtered_df)


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding: 20px 0 10px 0; border-bottom: 1px solid rgba(255,255,255,0.07); margin-bottom: 24px;">
  <div style="font-size:28px; font-weight:800; letter-spacing:-0.02em;">📊 GA4 BI Dashboard</div>
  <div style="font-size:12px; color:#475569; font-family:'DM Mono',monospace; margin-top:4px;">May 2026 · 132K+ SKUs · Real-time filtered</div>
</div>
""", unsafe_allow_html=True)

# Active filter badge
if seller_sel != "All" or lang_sel != "All":
    badges = []
    if seller_sel != "All": badges.append(f"🏪 {seller_sel}")
    if lang_sel   != "All": badges.append(f"🌐 {lang_sel}")
    st.info(f"Active filters: {' · '.join(badges)}")


# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", "📦 Categories", "🔽 Funnel", "🧩 Segments", "🏆 Top Products"
])


# ══════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════
with tab1:
    # KPI Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("💰 Total Revenue",   f"EGP {f_kpi['total_revenue']/1e6:.2f}M")
    with c2:
        st.metric("🛒 Orders",          f"{f_kpi['total_orders']:,}")
    with c3:
        st.metric("👁 Views",           f"{f_kpi['total_views']/1e6:.2f}M")
    with c4:
        st.metric("📊 Overall CVR",     f"{f_kpi['cvr_view_order']}%")
    with c5:
        st.metric("💎 AOV",             f"EGP {f_kpi['aov']:,.0f}")
    with c6:
        st.metric("🛍 Cart Rate",       f"{f_kpi['cvr_view_cart']}%")

    st.markdown("---")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.subheader("Revenue by Category (Top 10)")
        top10 = f_cat.head(10).sort_values("revenue")
        fig = px.bar(
            top10, x="revenue", y="category", orientation="h",
            color="revenue", color_continuous_scale=ORANGE_SEQ,
            text=top10["revenue"].apply(lambda v: f"EGP {v/1e6:.1f}M"),
            labels={"revenue": "Revenue (EGP)", "category": ""},
        )
        fig.update_traces(textposition="outside", textfont_size=10)
        fig.update_coloraxes(showscale=False)
        apply_theme(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Seller Type")
        fig_sel = px.pie(
            sel, values="revenue", names="seller_type",
            hole=0.55,
            color_discrete_sequence=["#F97316", "#3B82F6"],
        )
        fig_sel.update_traces(textinfo="percent+label", textfont_size=12)
        apply_theme(fig_sel, height=200, showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_sel, use_container_width=True)

        st.subheader("Language")
        fig_lng = px.pie(
            lng, values="revenue", names="lang_code",
            hole=0.55,
            color_discrete_sequence=["#F97316", "#3B82F6"],
        )
        fig_lng.update_traces(textinfo="percent+label", textfont_size=12)
        apply_theme(fig_lng, height=200, showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_lng, use_container_width=True)

    # Orders + CVR side by side
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Orders by Category (Top 10)")
        top10_ord = f_cat.head(10).sort_values("orders")
        fig2 = px.bar(
            top10_ord, x="orders", y="category", orientation="h",
            color="orders", color_continuous_scale=["#1E3A5F", "#3B82F6"],
            text="orders",
        )
        fig2.update_traces(textposition="outside", textfont_size=10)
        fig2.update_coloraxes(showscale=False)
        apply_theme(fig2, height=320)
        st.plotly_chart(fig2, use_container_width=True)

    with col_d:
        st.subheader("CVR % by Category (Top 10)")
        top10_cvr = f_cat.nlargest(10, "cvr_pct").sort_values("cvr_pct")
        fig3 = px.bar(
            top10_cvr, x="cvr_pct", y="category", orientation="h",
            color="cvr_pct", color_continuous_scale=["#14532D", "#10B981"],
            text=top10_cvr["cvr_pct"].apply(lambda v: f"{v:.2f}%"),
        )
        fig3.update_traces(textposition="outside", textfont_size=10)
        fig3.update_coloraxes(showscale=False)
        apply_theme(fig3, height=320)
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2 — CATEGORIES
# ══════════════════════════════════════════════
with tab2:
    st.subheader("Category Performance Table")

    display_cols = {
        "category": "Category", "revenue": "Revenue (EGP)", "orders": "Orders",
        "views": "Views", "cvr_pct": "CVR %", "aov": "AOV (EGP)",
        "cart_rate_pct": "Cart Rate %", "rev_share_pct": "Rev Share %",
        "sku_count": "SKUs",
    }
    table_df = f_cat[list(display_cols.keys())].rename(columns=display_cols)

    # Format
    fmt_int  = ["Revenue (EGP)", "Orders", "Views", "AOV (EGP)", "SKUs"]
    fmt_pct  = ["CVR %", "Cart Rate %", "Rev Share %"]
    styled = table_df.style \
        .format({c: "{:,.0f}" for c in fmt_int}) \
        .format({c: "{:.2f}%" for c in fmt_pct}) \
        .background_gradient(subset=["Revenue (EGP)"], cmap="Oranges") \
        .background_gradient(subset=["CVR %"], cmap="Greens") \
        .background_gradient(subset=["AOV (EGP)"], cmap="Blues")

    st.dataframe(styled, use_container_width=True, height=480)

    st.markdown("---")

    col_e, col_f = st.columns(2)
    with col_e:
        st.subheader("Revenue vs Orders (Bubble = AOV)")
        bubble = f_cat.head(15)
        fig4 = px.scatter(
            bubble, x="orders", y="revenue", size="aov",
            color="category", text="category",
            color_discrete_sequence=CAT_COLORS,
            labels={"revenue": "Revenue (EGP)", "orders": "Orders"},
        )
        fig4.update_traces(textposition="top center", textfont_size=9)
        apply_theme(fig4, height=380, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    with col_f:
        st.subheader("Views vs CVR%")
        fig5 = px.scatter(
            f_cat.head(20), x="views", y="cvr_pct", size="revenue",
            color="category", text="category",
            color_discrete_sequence=CAT_COLORS,
            labels={"views": "Total Views", "cvr_pct": "CVR %"},
        )
        fig5.update_traces(textposition="top center", textfont_size=9)
        apply_theme(fig5, height=380, showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.subheader("AOV by Category")
    aov_cat = f_cat.nlargest(15, "aov").sort_values("aov", ascending=True)
    fig6 = px.bar(
        aov_cat, x="aov", y="category", orientation="h",
        color="aov", color_continuous_scale=["#1E1B4B", "#8B5CF6"],
        text=aov_cat["aov"].apply(lambda v: f"EGP {v:,.0f}"),
    )
    fig6.update_traces(textposition="outside", textfont_size=10)
    fig6.update_coloraxes(showscale=False)
    apply_theme(fig6, height=420)
    st.plotly_chart(fig6, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 3 — FUNNEL
# ══════════════════════════════════════════════
with tab3:
    col_g, col_h = st.columns([1, 1])

    with col_g:
        st.subheader("Conversion Funnel")
        fig_fun = go.Figure(go.Funnel(
            y=f_fun["stage"].tolist(),
            x=f_fun["count"].tolist(),
            textinfo="value+percent initial+percent previous",
            marker=dict(color=["#3B82F6", "#8B5CF6", "#F59E0B", "#10B981"]),
            connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
        ))
        apply_theme(fig_fun, height=420, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_fun, use_container_width=True)

    with col_h:
        st.subheader("Drop-off at Each Stage")
        drop_df = f_fun[f_fun["drop_pct"] > 0].copy()
        fig_drop = px.bar(
            drop_df, x="stage", y="drop_pct",
            color="drop_pct",
            color_continuous_scale=["#7F1D1D", "#EF4444"],
            text=drop_df["drop_pct"].apply(lambda v: f"{v}%"),
            labels={"drop_pct": "Drop-off %", "stage": ""},
        )
        fig_drop.update_traces(textposition="outside", textfont_size=12)
        fig_drop.update_coloraxes(showscale=False)
        apply_theme(fig_drop, height=420)
        st.plotly_chart(fig_drop, use_container_width=True)

    st.markdown("---")
    st.subheader("Funnel Step-by-Step KPIs")

    cols = st.columns(4)
    funnel_meta = [
        ("👁 Views",       f_kpi["total_views"],    "100% baseline", "#3B82F6"),
        ("🛒 Cart",        f_kpi["total_cart"],     f"{f_kpi['cvr_view_cart']}% of views", "#8B5CF6"),
        ("💳 Checkout",    f_kpi["total_checkout"], f"{f_kpi['cvr_cart_checkout']}% of cart", "#F59E0B"),
        ("✅ Orders",      f_kpi["total_orders"],   f"{f_kpi['cvr_view_order']}% of views", "#10B981"),
    ]
    for col, (label, val, sub, color) in zip(cols, funnel_meta):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid {color};">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="color:{color}">{val:,}</div>
              <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Opportunities
    c1, c2 = st.columns(2)
    lost_cart     = f_kpi["total_cart"] - f_kpi["total_checkout"]
    lost_checkout = f_kpi["total_checkout"] - f_kpi["total_orders"]

    with c1:
        st.warning(f"⚠️ **Cart Abandonment:** {lost_cart:,} users added to cart but didn't reach checkout. "
                   f"Recovery rate of just 5% = ~{int(lost_cart*0.05):,} extra orders.")
    with c2:
        st.error(f"🚨 **Checkout Drop-off:** {lost_checkout:,} users reached checkout but didn't order. "
                 f"Checkout-to-order rate is only {f_kpi['cvr_checkout_order']}%. "
                 f"Priority: payment UX & trust signals.")


# ══════════════════════════════════════════════
# TAB 4 — SEGMENTS
# ══════════════════════════════════════════════
with tab4:
    st.subheader("CVR Tier Segmentation")

    # CVR tier table
    seg_df = cvr_segments(f_cat)[["category", "cvr_pct", "cvr_tier", "revenue", "orders", "aov", "views"]]
    st.dataframe(
        seg_df.style
            .format({"cvr_pct": "{:.2f}%", "revenue": "{:,.0f}", "orders": "{:,.0f}", "aov": "{:,.0f}", "views": "{:,.0f}"})
            .background_gradient(subset=["cvr_pct"], cmap="RdYlGn"),
        use_container_width=True,
        height=420,
    )

    st.markdown("---")

    col_i, col_j = st.columns(2)

    with col_i:
        st.subheader("Seller: Revenue & Orders")
        fig_sel2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig_sel2.add_trace(go.Bar(
            name="Revenue", x=sel["seller_type"], y=sel["revenue"],
            marker_color=["#F97316", "#3B82F6"], text=sel["revenue"].apply(lambda v: f"EGP {v/1e6:.1f}M"),
            textposition="outside",
        ))
        fig_sel2.add_trace(go.Scatter(
            name="Orders", x=sel["seller_type"], y=sel["orders"],
            mode="markers+lines", marker=dict(size=12, color="#10B981"),
            line=dict(color="#10B981", dash="dot"),
        ), secondary_y=True)
        fig_sel2.update_layout(**{**PLOT_LAYOUT, "height": 320})
        st.plotly_chart(fig_sel2, use_container_width=True)

    with col_j:
        st.subheader("Language: Revenue Split")
        fig_lng2 = px.bar(
            lng, x="lang_code", y="revenue",
            color="lang_code",
            color_discrete_sequence=["#F97316", "#3B82F6"],
            text=lng["revenue"].apply(lambda v: f"EGP {v/1e6:.1f}M"),
        )
        fig_lng2.update_traces(textposition="outside")
        apply_theme(fig_lng2, height=320, showlegend=False)
        st.plotly_chart(fig_lng2, use_container_width=True)

    # Insight cards
    st.markdown("---")
    st.subheader("💡 Key Strategic Insights")

    ins = [
        ("🔥 Arabic Dominance", f"97% of revenue (EGP {lng[lng.lang_code=='AR']['revenue'].values[0]/1e6:.1f}M) is Arabic. English is underpenetrated — growth opportunity.", "#F97316"),
        ("📦 Marketplace Efficiency", "Marketplace drives 68% more views but 56% less orders vs Retail. Improve MP product pages & CVR.", "#3B82F6"),
        ("💎 High-Value Appliances", "Top 5 categories = 56% of revenue. AOVs range EGP 10K–26K. Budget should protect these.", "#8B5CF6"),
        ("⚡ Quick-Win SKUs", "Fans & Cookware: CVR >1.15%. High order volume + good margins. Scale spend here immediately.", "#10B981"),
    ]
    cols_ins = st.columns(2)
    for i, (title, body, color) in enumerate(ins):
        with cols_ins[i % 2]:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid {color}; margin-bottom: 12px;">
              <div style="font-weight:700; color:{color}; margin-bottom:6px;">{title}</div>
              <div style="font-size:13px; color:#94A3B8; line-height:1.6;">{body}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 5 — TOP PRODUCTS
# ══════════════════════════════════════════════
with tab5:
    st.subheader("Top 50 Products by Revenue")

    sort_by = st.selectbox("Sort by:", ["revenue", "orders", "views", "aov", "cvr_orders"])
    top_filtered = top_products(filtered_df, by=sort_by, top_n=50)

    display = top_filtered[["sku", "item_name", "category", "seller_type", "lang_code",
                             "views", "cart", "checkout", "orders", "revenue", "aov", "cvr_orders"]].copy()

    styled_top = display.style \
        .format({"revenue": "EGP {:,.0f}", "aov": "EGP {:,.0f}", "cvr_orders": "{:.4f}",
                 "views": "{:,.0f}", "cart": "{:,.0f}", "checkout": "{:,.0f}", "orders": "{:,.0f}"}) \
        .background_gradient(subset=["revenue"], cmap="Oranges") \
        .background_gradient(subset=["orders"], cmap="Greens") \
        .background_gradient(subset=["cvr_orders"], cmap="Blues")

    st.dataframe(styled_top, use_container_width=True, height=520)

    st.markdown("---")

    col_k, col_l = st.columns(2)
    with col_k:
        st.subheader("Top 15 by Revenue")
        t15 = top_filtered.head(15)
        fig_t = px.bar(
            t15, x="revenue", y="item_name", orientation="h",
            color="revenue", color_continuous_scale=ORANGE_SEQ,
            text=t15["revenue"].apply(lambda v: f"EGP {v/1e3:.0f}K"),
        )
        fig_t.update_traces(textposition="outside", textfont_size=9)
        fig_t.update_coloraxes(showscale=False)
        apply_theme(fig_t, height=480)
        st.plotly_chart(fig_t, use_container_width=True)

    with col_l:
        st.subheader("Revenue by Category (Top Products)")
        cat_dist = top_filtered.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        fig_cp = px.pie(
            cat_dist.head(10), values="revenue", names="category",
            hole=0.45, color_discrete_sequence=CAT_COLORS,
        )
        fig_cp.update_traces(textinfo="percent+label", textfont_size=10)
        apply_theme(fig_cp, height=480, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_cp, use_container_width=True)


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#334155; font-size:11px; margin-top:40px; padding:20px 0;
border-top: 1px solid rgba(255,255,255,0.06); font-family:'DM Mono',monospace;">
  GA4 BI Dashboard · May 2026 · Built with Streamlit + Plotly
</div>
""", unsafe_allow_html=True)
