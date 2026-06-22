import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title="Superstore Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load Data
df = pd.read_csv(
    r".\superstore_cleaned.csv",
    parse_dates=["order_date", "ship_date"]
)

with st.sidebar:

    st.header("Filters")

    with st.form("filter_form"):

        regions = st.multiselect(
            "Region",
            options=df["region"].unique(),
            default=df["region"].unique()
        )

        order_year = df["order_date"].dt.year

        years = st.multiselect(
            "Year",
            options=sorted(order_year.unique()),
            default=sorted(order_year.unique())
        )

        ship_modes = st.multiselect(
            "Shipping Mode",
            options=df["ship_mode"].unique(),
            default=df["ship_mode"].unique()
        )

        segments = st.multiselect(
            "Segment",
            options=df["segment"].unique(),
            default=df["segment"].unique()
        )

        apply_filters = st.form_submit_button(
            "🔍 Apply Filters",
            type="primary"
        )

# Filter Data
filtered = df[
    (df["region"].isin(regions))
    & (order_year.isin(years))
    & (df["ship_mode"].isin(ship_modes))
    & (df["segment"].isin(segments))
].copy()

# Dashboard Title
st.title("📊 Superstore Sales Dashboard")

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Sales",
        f"${filtered['sales'].sum():,.0f}"
    )

with col2:
    st.metric(
        "Total Profit",
        f"${filtered['profit'].sum():,.0f}"
    )

with col3:
    st.metric(
        "Average Discount",
        f"{filtered['discount(%)'].mean()*100:.2f}%"
    )

with col4:
    st.metric(
        "Orders",
        f"{filtered['order_id'].nunique():,}"
    )

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "By Category", "By Region", "Quality Alerts"]
)

# ---------------- TAB 1 ----------------
with tab1:

    with st.expander("📄 Show Raw Data"):
        st.dataframe(filtered, use_container_width=True)

    st.subheader("Monthly Sales by Year")

    filtered["order_year"] = filtered["order_date"].dt.year
    filtered["month"] = filtered["order_date"].dt.to_period("M").astype(str)

    monthly_yr = (
        filtered.groupby(["month", "order_year"])["sales"]
        .sum()
        .reset_index()
    )

    monthly_yr_fig = px.line(
        monthly_yr,
        x="month",
        y="sales",
        color="order_year",
        markers=True
    )

    st.plotly_chart(monthly_yr_fig, use_container_width=True)

    st.download_button(
        "📥 Download Filtered Data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_superstore_data.csv",
        mime="text/csv",
        type="primary"
    )

# ---------------- TAB 2 ----------------
with tab2:

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top 10 Sub-Categories")

        top_sub = (
            filtered.groupby("sub-category")["sales"]
            .sum()
            .nlargest(10)
            .reset_index()
        )

        fig_bar = px.bar(
            top_sub,
            x="sales",
            y="sub-category",
            orientation="h",
            title="Top 10 Sub-Categories by Sales"
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:

        st.subheader("Sales vs Profit")

        scatter_fig = px.scatter(
            filtered,
            x="sales",
            y="profit",
            color="category",
            hover_data=["sub-category"]
        )

        st.plotly_chart(scatter_fig, use_container_width=True)

# ---------------- TAB 3 ----------------
with tab3:

    st.subheader("Profit Distribution by Region")

    region_profit = (
        filtered.groupby("region")["profit"]
        .sum()
        .reset_index()
    )

    donut_region = px.pie(
        region_profit,
        names="region",
        values="profit",
        hole=0.5,
        title="Profit by Region"
    )

    donut_region.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    st.plotly_chart(
        donut_region,
        use_container_width=True
    )

# ---------------- TAB 4 ----------------
with tab4:

    st.subheader("🚨 Quality Alerts")

    disc_arr = filtered["discount(%)"].values
    sales_arr = filtered["sales"].values
    profit_arr = filtered["profit"].values

    # Average Profit
    avg_profit = np.mean(profit_arr)

    if avg_profit > 20:
        st.success(
            f"🟢 Healthy profit margin: {avg_profit:.1f}%"
        )
    elif avg_profit > 10:
        st.warning(
            f"🟡 Moderate profit margin: {avg_profit:.1f}%"
        )
    else:
        st.error(
            f"🔴 Low profit margin: {avg_profit:.1f}%"
        )

    # High Discount Orders
    high_disc_pct = np.percentile(disc_arr, 75)

    high_disc_n = int(
        np.sum(disc_arr > high_disc_pct)
    )

    st.info(
        f"ℹ️ {high_disc_n} orders above the 75th percentile discount"
    )

    # Outlier Detection
    z_score = (
        (sales_arr - np.mean(sales_arr))
        / np.std(sales_arr)
    )

    mask = np.abs(z_score) > 2

    outlier_n = int(np.sum(mask))

    if outlier_n > 0:
        st.warning(
            f"⚠️ {outlier_n} sales outliers detected (|z| > 2)"
        )
    else:
        st.success(
            "✅ No major outliers detected"
        )

    with st.expander("📋 View Outlier Rows"):

        st.dataframe(
            filtered[mask][
                [
                    "order_id",
                    "order_date",
                    "sales",
                    "profit",
                    "region"
                ]
            ],
            use_container_width=True
        )
