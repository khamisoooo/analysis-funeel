# 📊 GA4 BI Dashboard

A production-ready Streamlit dashboard for GA4 e-commerce analytics.  
Built for a **132K+ SKU** catalog with full funnel, category, and segment analysis.

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ga4-dashboard.git
cd ga4-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your data
cp your_ga4_export.csv data/ga4_data.csv

# 4. Run
streamlit run app.py
```

---

## 📁 Project Structure

```
ga4-dashboard/
│
├── app.py                  # Streamlit dashboard (5 tabs)
├── data_processor.py       # Pure-Python data pipeline
├── requirements.txt
│
├── data/
│   └── ga4_data.csv        # GA4 export (not committed to git)
│
├── tests/
│   ├── conftest.py
│   └── test_data_processor.py   # 25+ pytest unit tests
│
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI pipeline
```

---

## 📊 Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **📈 Overview** | Total KPIs, revenue by category, seller type & language split |
| **📦 Categories** | Full category table, scatter plots, AOV comparison |
| **🔽 Funnel** | View → Cart → Checkout → Order with drop-off analysis |
| **🧩 Segments** | CVR tier segmentation, Retail vs Marketplace, strategic insights |
| **🏆 Top Products** | Top 50 SKUs by any metric, sortable & filterable |

---

## 🔧 Data Format

The dashboard expects a CSV with these columns:

| Column | Description |
|--------|-------------|
| `sku` | Product SKU |
| `parent_sku` | Parent SKU |
| `seller_type` | `Retail` or `Marketplace` |
| `lang_code` | `AR` or `EN` |
| `item_name` | Product name |
| `attribute_set` | Category name |
| `views_total` | Total product page views |
| `Items added to cart` | Cart additions |
| `Items checked out` | Checkout initiations |
| `orders_count` | Completed orders |
| `qty` | Items sold |
| `revenue` | Total revenue |
| `conversion_rate_orders` | CVR (orders/views) |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

25+ unit tests covering all aggregation functions:
- KPI calculations
- Category/Seller/Language aggregations
- Funnel stages & drop-off rates
- CVR tier segmentation
- Edge cases (zero views, zero revenue)

---

## ⚙️ CI/CD

GitHub Actions runs on every push to `main` or `dev`:

1. **Lint** with flake8 (max line length: 120)
2. **Unit tests** with pytest
3. **Import validation** for `app.py`

---

## 📈 Key Metrics (May 2026 Export)

| Metric | Value |
|--------|-------|
| Total Revenue | EGP 62.2M |
| Total Orders | 20,512 |
| Total SKUs | 132,283 |
| Overall CVR | 0.822% |
| AOV | EGP 3,033 |
| Top Category | Air Conditioner (EGP 10.5M) |

---

## 🛠 Tech Stack

- **Streamlit** — dashboard framework
- **Pandas + NumPy** — data processing
- **Plotly** — interactive charts
- **Pytest** — testing
- **GitHub Actions** — CI/CD

---

## 📝 License

MIT
