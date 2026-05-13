"""
GA4 BI Dashboard — Streamlit App
"""

import io
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_processor import (
    load_data, kpi_summary, category_agg,
    seller_agg, lang_agg, funnel_df, top_products, cvr_segments
)

st.set_page_config(
    page_title="GA4 BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  html, body, [class*="css"] {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background-color: #0A0F1C;
      color: #E2E8F0;
  }
  .metric-card {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 14px;
      padding: 18px 22px;
      margin-bottom: 10px;
  }
  .metric-label { font-size:11px; color:#64748B; letter-spacing:0.08em; text-transform:uppercase; }
  .metric-value { font-family:'Courier New',Courier,monospace; font-size:26px; font-weight:700; }
  .metric-sub   { font-size:12px; color:#475569; margin-top:2px; }
  [data-testid="stMetricValue"] {
      font-family:'Courier New',Courier,monospace !important;
      font-size:20px !important; font-weight:700 !important;
  }
  [data-testid="stMetricLabel"] { font-size:11px !important; color:#64748B !important; }
  .stTabs [data-baseweb="tab"] {
      background:rgba(255,255,255,0.04); border-radius:8px;
      padding:6px 18px; border:none !important;
      color:#64748B; font-size:12px; font-weight:600;
  }
  .stTabs [aria-selected="true"] { background:#F97316 !important; color:white !important; }
  h1,h2,h3 { font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Plotly theme ─────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="Courier New, monospace", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False, color="#475569"),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, color="#475569"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
)
ORANGE_SEQ = px.colors.sequential.Oranges
CAT_COLORS = px.colors.qualitative.Vivid

def apply_theme(fig, **kwargs):
    fig.update_layout(**{**PLOT_LAYOUT, **kwargs})
    return fig

@st.cache_data(show_spinner="Processing data...")
def process_file(file_bytes: bytes):
    df  = load_data(io.BytesIO(file_bytes))
    cat = category_agg(df, top_n=20)
    return (
        df, kpi_summary(df), cat,
        seller_agg(df), lang_agg(df), funnel_df(df),
        top_products(df, top_n=50), cvr_segments(cat),
    )

# ════════════════════════════════════════════════
# STEP 1 — Uploader in sidebar (NO st.stop inside with block)
# ════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📊 GA4 Dashboard")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📂 Upload GA4 CSV",
        type=["csv"],
        help="Columns: sku, seller_type, lang_code, attribute_set, views_total, "
             "Items added to cart, Items checked out, orders_count, qty, revenue, conversion_rate_orders",
    )

    # Save to session_state whenever a new file is uploaded
    if uploaded_file is not None:
        raw = uploaded_file.read()
        if raw:                                         # guard against empty reads
            st.session_state["file_bytes"] = raw
            st.session_state["file_name"]  = uploaded_file.name

# ════════════════════════════════════════════════
# STEP 2 — Guard outside sidebar (safe to st.stop here)
# ════════════════════════════════════════════════
if "file_bytes" not in st.session_state:
    st.markdown("""
    <div style="margin-top:80px; text-align:center;">
      <div style="font-size:56px; margin-bottom:16px;">📥</div>
      <div style="font-size:20px; font-weight:700; color:#475569; margin-bottom:8px;">
        No data loaded yet
      </div>
      <div style="font-size:14px; color:#334155; max-width:400px; margin:0 auto; line-height:1.8;">
        Use the <strong>Upload GA4 CSV</strong> button in the sidebar.<br>
        Data stays loaded even after page refresh.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ════════════════════════════════════════════════
# STEP 3 — Process data (cached, won't rerun unless file changes)
# ════════════════════════════════════════════════
file_bytes = st.session_state["file_bytes"]
file_name  = st.session_state["file_name"]

df, kpi, cat, sel, lng, fun, top, cvr = process_file(file_bytes)

# ════════════════════════════════════════════════
# STEP 4 — Rest of sidebar (filters + info)
# ════════════════════════════════════════════════
with st.sidebar:
    st.success(f"✅ {file_name}")
    st.caption(f"{kpi['skus_total']:,} SKUs · {len(file_bytes)/1024:,.0f} KB")
    st.markdown("---")

    st.markdown("### 🔍 Filters")
    seller_sel = st.selectbox(
        "Seller Type",
        ["All"] + sorted(df["seller_type"].dropna().unique().tolist())
    )
    lang_sel = st.selectbox(
        "Language",
        ["All"] + sorted(df["lang_code"].dropna().unique().tolist())
    )
    top_cats = cat["category"].tolist()
    cat_sel  = st.multiselect("Categories (top 20)", top_cats, default=top_cats[:10])

    st.markdown("---")
    st.markdown(f"**Total SKUs:** {kpi['skus_total']:,}")
    st.markdown(f"**With Revenue:** {kpi['skus_with_revenue']:,}")
    st.markdown(f"**Categories:** {df['category'].nunique()}")

# ════════════════════════════════════════════════
# STEP 5 — Apply filters
# ════════════════════════════════════════════════
filtered_df = df.copy()
if seller_sel != "All":
    filtered_df = filtered_df[filtered_df["seller_type"] == seller_sel]
if lang_sel != "All":
    filtered_df = filtered_df[filtered_df["lang_code"] == lang_sel]

f_kpi = kpi_summary(filtered_df)
f_cat = category_agg(filtered_df, top_n=20)
if cat_sel:
    f_cat = f_cat[f_cat["category"].isin(cat_sel)]
f_fun = funnel_df(filtered_df)

# ════════════════════════════════════════════════
# MAIN AREA — Header
# ════════════════════════════════════════════════
st.markdown("""
<div style="padding:16px 0 12px; border-bottom:1px solid rgba(255,255,255,0.07);
            margin-bottom:20px; display:flex; align-items:center; gap:12px;">
  <div style="font-size:28px;">📊</div>
  <div>
    <div style="font-size:22px; font-weight:800;">GA4 BI Dashboard</div>
    <div style="font-size:11px; color:#475569; margin-top:2px;">Product-level funnel & revenue analytics</div>
  </div>
</div>
""", unsafe_allow_html=True)

if seller_sel != "All" or lang_sel != "All":
    badges = (
        ([f"🏪 {seller_sel}"] if seller_sel != "All" else []) +
        ([f"🌐 {lang_sel}"]   if lang_sel   != "All" else [])
    )
    st.info(f"Active filters: {' · '.join(badges)}")

# ════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", "📦 Categories", "🔽 Funnel", "🧩 Segments", "🏆 Top Products"
])

# ── TAB 1: OVERVIEW ─────────────────────────────
with tab1:
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric("💰 Revenue",   f"EGP {f_kpi['total_revenue']/1e6:.2f}M")
    with c2: st.metric("🛒 Orders",    f"{f_kpi['total_orders']:,}")
    with c3: st.metric("👁 Views",     f"{f_kpi['total_views']/1e6:.2f}M")
    with c4: st.metric("📊 CVR",       f"{f_kpi['cvr_view_order']}%")
    with c5: st.metric("💎 AOV",       f"EGP {f_kpi['aov']:,.0f}")
    with c6: st.metric("🛍 Cart Rate", f"{f_kpi['cvr_view_cart']}%")
    st.markdown("---")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Revenue by Category (Top 10)")
        top10 = f_cat.head(10).sort_values("revenue")
        fig = px.bar(top10, x="revenue", y="category", orientation="h",
                     color="revenue", color_continuous_scale=ORANGE_SEQ,
                     text=top10["revenue"].apply(lambda v: f"EGP {v/1e6:.1f}M"))
        fig.update_traces(textposition="outside", textfont_size=10)
        fig.update_coloraxes(showscale=False)
        apply_theme(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Seller Type")
        fig_s = px.pie(sel, values="revenue", names="seller_type", hole=0.55,
                       color_discrete_sequence=["#F97316","#3B82F6"])
        fig_s.update_traces(textinfo="percent+label", textfont_size=12)
        apply_theme(fig_s, height=200, showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_s, use_container_width=True)

        st.subheader("Language")
        fig_l = px.pie(lng, values="revenue", names="lang_code", hole=0.55,
                       color_discrete_sequence=["#F97316","#3B82F6"])
        fig_l.update_traces(textinfo="percent+label", textfont_size=12)
        apply_theme(fig_l, height=200, showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_l, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Orders by Category")
        o10 = f_cat.head(10).sort_values("orders")
        fig2 = px.bar(o10, x="orders", y="category", orientation="h",
                      color="orders", color_continuous_scale=["#1E3A5F","#3B82F6"], text="orders")
        fig2.update_traces(textposition="outside", textfont_size=10)
        fig2.update_coloraxes(showscale=False)
        apply_theme(fig2, height=320)
        st.plotly_chart(fig2, use_container_width=True)

    with col_d:
        st.subheader("CVR % by Category")
        c10 = f_cat.nlargest(10,"cvr_pct").sort_values("cvr_pct")
        fig3 = px.bar(c10, x="cvr_pct", y="category", orientation="h",
                      color="cvr_pct", color_continuous_scale=["#14532D","#10B981"],
                      text=c10["cvr_pct"].apply(lambda v: f"{v:.2f}%"))
        fig3.update_traces(textposition="outside", textfont_size=10)
        fig3.update_coloraxes(showscale=False)
        apply_theme(fig3, height=320)
        st.plotly_chart(fig3, use_container_width=True)


# ── TAB 2: CATEGORIES ───────────────────────────
with tab2:
    st.subheader("Category Performance Table")
    dc = {
        "category":"Category","revenue":"Revenue (EGP)","orders":"Orders","views":"Views",
        "cvr_pct":"CVR %","aov":"AOV (EGP)","cart_rate_pct":"Cart Rate %",
        "rev_share_pct":"Rev Share %","sku_count":"SKUs",
    }
    tdf = f_cat[list(dc.keys())].rename(columns=dc)
    st.dataframe(
        tdf.style
           .format({c:"{:,.0f}" for c in ["Revenue (EGP)","Orders","Views","AOV (EGP)","SKUs"]})
           .format({c:"{:.2f}%" for c in ["CVR %","Cart Rate %","Rev Share %"]})
           .background_gradient(subset=["Revenue (EGP)"], cmap="Oranges")
           .background_gradient(subset=["CVR %"],         cmap="Greens")
           .background_gradient(subset=["AOV (EGP)"],     cmap="Blues"),
        use_container_width=True, height=480,
    )
    st.markdown("---")
    ce, cf = st.columns(2)
    with ce:
        st.subheader("Revenue vs Orders (Bubble = AOV)")
        fig4 = px.scatter(f_cat.head(15), x="orders", y="revenue", size="aov",
                          color="category", text="category", color_discrete_sequence=CAT_COLORS)
        fig4.update_traces(textposition="top center", textfont_size=9)
        apply_theme(fig4, height=380, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
    with cf:
        st.subheader("Views vs CVR %")
        fig5 = px.scatter(f_cat.head(20), x="views", y="cvr_pct", size="revenue",
                          color="category", text="category", color_discrete_sequence=CAT_COLORS)
        fig5.update_traces(textposition="top center", textfont_size=9)
        apply_theme(fig5, height=380, showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.subheader("AOV by Category (Top 15)")
    ac = f_cat.nlargest(15,"aov").sort_values("aov")
    fig6 = px.bar(ac, x="aov", y="category", orientation="h",
                  color="aov", color_continuous_scale=["#1E1B4B","#8B5CF6"],
                  text=ac["aov"].apply(lambda v: f"EGP {v:,.0f}"))
    fig6.update_traces(textposition="outside", textfont_size=10)
    fig6.update_coloraxes(showscale=False)
    apply_theme(fig6, height=420)
    st.plotly_chart(fig6, use_container_width=True)


# ── TAB 3: FUNNEL ───────────────────────────────
with tab3:
    cg, ch = st.columns(2)
    with cg:
        st.subheader("Conversion Funnel")
        ffig = go.Figure(go.Funnel(
            y=f_fun["stage"].tolist(), x=f_fun["count"].tolist(),
            textinfo="value+percent initial+percent previous",
            marker=dict(color=["#3B82F6","#8B5CF6","#F59E0B","#10B981"]),
            connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
        ))
        apply_theme(ffig, height=420, margin=dict(l=20,r=20,t=30,b=20))
        st.plotly_chart(ffig, use_container_width=True)

    with ch:
        st.subheader("Drop-off at Each Stage")
        ddf = f_fun[f_fun["drop_pct"] > 0].copy()
        fdrop = px.bar(ddf, x="stage", y="drop_pct",
                       color="drop_pct", color_continuous_scale=["#7F1D1D","#EF4444"],
                       text=ddf["drop_pct"].apply(lambda v: f"{v}%"))
        fdrop.update_traces(textposition="outside", textfont_size=12)
        fdrop.update_coloraxes(showscale=False)
        apply_theme(fdrop, height=420)
        st.plotly_chart(fdrop, use_container_width=True)

    st.markdown("---")
    fm_cols = st.columns(4)
    fm = [
        ("👁 Views",    f_kpi["total_views"],    "100% baseline",                          "#3B82F6"),
        ("🛒 Cart",     f_kpi["total_cart"],     f"{f_kpi['cvr_view_cart']}% of views",    "#8B5CF6"),
        ("💳 Checkout", f_kpi["total_checkout"], f"{f_kpi['cvr_cart_checkout']}% of cart", "#F59E0B"),
        ("✅ Orders",   f_kpi["total_orders"],   f"{f_kpi['cvr_view_order']}% of views",   "#10B981"),
    ]
    for col, (label, val, sub, color) in zip(fm_cols, fm):
        with col:
            st.markdown(
                f'<div class="metric-card" style="border-top:3px solid {color};">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value" style="color:{color}">{val:,}</div>'
                f'<div class="metric-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("---")
    lc, rc = st.columns(2)
    with lc:
        st.warning(f"⚠️ **Cart Abandonment:** {f_kpi['total_cart']-f_kpi['total_checkout']:,} users didn't reach checkout.")
    with rc:
        st.error(f"🚨 **Checkout Drop-off:** {f_kpi['total_checkout']-f_kpi['total_orders']:,} users didn't order. Rate: {f_kpi['cvr_checkout_order']}%")


# ── TAB 4: SEGMENTS ─────────────────────────────
with tab4:
    st.subheader("CVR Tier Segmentation")
    sdf = cvr_segments(f_cat)[["category","cvr_pct","cvr_tier","revenue","orders","aov","views"]]
    st.dataframe(
        sdf.style
           .format({"cvr_pct":"{:.2f}%","revenue":"{:,.0f}","orders":"{:,.0f}","aov":"{:,.0f}","views":"{:,.0f}"})
           .background_gradient(subset=["cvr_pct"], cmap="RdYlGn"),
        use_container_width=True, height=420,
    )
    st.markdown("---")
    ci, cj = st.columns(2)
    with ci:
        st.subheader("Seller: Revenue & Orders")
        fs2 = make_subplots(specs=[[{"secondary_y":True}]])
        fs2.add_trace(go.Bar(
            name="Revenue", x=sel["seller_type"], y=sel["revenue"],
            marker_color=["#F97316","#3B82F6"],
            text=sel["revenue"].apply(lambda v: f"EGP {v/1e6:.1f}M"),
            textposition="outside",
        ))
        fs2.add_trace(go.Scatter(
            name="Orders", x=sel["seller_type"], y=sel["orders"],
            mode="markers+lines", marker=dict(size=12, color="#10B981"),
            line=dict(color="#10B981", dash="dot"),
        ), secondary_y=True)
        fs2.update_layout(**{**PLOT_LAYOUT, "height":320})
        st.plotly_chart(fs2, use_container_width=True)

    with cj:
        st.subheader("Language: Revenue Split")
        fl2 = px.bar(lng, x="lang_code", y="revenue", color="lang_code",
                     color_discrete_sequence=["#F97316","#3B82F6"],
                     text=lng["revenue"].apply(lambda v: f"EGP {v/1e6:.1f}M"))
        fl2.update_traces(textposition="outside")
        apply_theme(fl2, height=320, showlegend=False)
        st.plotly_chart(fl2, use_container_width=True)

    st.markdown("---")
    st.subheader("💡 Key Strategic Insights")
    ins = [
        ("🔥 Arabic Dominance",      "Arabic drives 97% of revenue. English is underpenetrated — growth opportunity.", "#F97316"),
        ("📦 Marketplace Gap",       "More views but fewer conversions vs Retail. Improve MP pages & CVR.",           "#3B82F6"),
        ("💎 High-Value Appliances", "Top 5 categories = 50%+ of revenue. Protect budget allocation.",               "#8B5CF6"),
        ("⚡ Quick-Win SKUs",        "CVR >1% (Fans, Cookware) = fast revenue wins. Scale spend now.",               "#10B981"),
    ]
    ins_left, ins_right = st.columns(2)
    for i, (title, body, color) in enumerate(ins):
        target = ins_left if i % 2 == 0 else ins_right
        with target:
            st.markdown(
                f'<div class="metric-card" style="border-left:4px solid {color}; margin-bottom:12px;">'
                f'<div style="font-weight:700; color:{color}; margin-bottom:6px;">{title}</div>'
                f'<div style="font-size:13px; color:#94A3B8; line-height:1.6;">{body}</div></div>',
                unsafe_allow_html=True,
            )


# ── TAB 5: TOP PRODUCTS ─────────────────────────
with tab5:
    sort_by = st.selectbox("Sort by:", ["revenue","orders","views","aov","cvr_orders"])
    tp = top_products(filtered_df, by=sort_by, top_n=50)
    disp = tp[["sku","item_name","category","seller_type","lang_code",
               "views","cart","checkout","orders","revenue","aov","cvr_orders"]].copy()
    st.dataframe(
        disp.style
            .format({"revenue":"EGP {:,.0f}","aov":"EGP {:,.0f}","cvr_orders":"{:.4f}",
                     "views":"{:,.0f}","cart":"{:,.0f}","checkout":"{:,.0f}","orders":"{:,.0f}"})
            .background_gradient(subset=["revenue"],    cmap="Oranges")
            .background_gradient(subset=["orders"],     cmap="Greens")
            .background_gradient(subset=["cvr_orders"], cmap="Blues"),
        use_container_width=True, height=520,
    )
    st.markdown("---")
    ck, cl = st.columns(2)
    with ck:
        st.subheader("Top 15 by Revenue")
        t15 = tp.head(15)
        ft = px.bar(t15, x="revenue", y="item_name", orientation="h",
                    color="revenue", color_continuous_scale=ORANGE_SEQ,
                    text=t15["revenue"].apply(lambda v: f"EGP {v/1e3:.0f}K"))
        ft.update_traces(textposition="outside", textfont_size=9)
        ft.update_coloraxes(showscale=False)
        apply_theme(ft, height=480)
        st.plotly_chart(ft, use_container_width=True)

    with cl:
        st.subheader("Revenue Share by Category")
        cd = tp.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        fcp = px.pie(cd.head(10), values="revenue", names="category",
                     hole=0.45, color_discrete_sequence=CAT_COLORS)
        fcp.update_traces(textinfo="percent+label", textfont_size=10)
        apply_theme(fcp, height=480, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fcp, use_container_width=True)


st.markdown(
    '<div style="text-align:center;color:#334155;font-size:11px;margin-top:40px;padding:20px 0;'
    'border-top:1px solid rgba(255,255,255,0.06);">GA4 BI Dashboard · Streamlit + Plotly</div>',
    unsafe_allow_html=True,
)
