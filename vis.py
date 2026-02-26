```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------
# STEP 2 — Page Config
# -----------------------
st.set_page_config(layout="wide")
st.title("NovaRetail Customer Intelligence Dashboard")
st.subheader("Revenue Performance, Growth Opportunities, and Decline Detection")

# -----------------------
# STEP 3 — Load Data
# -----------------------
try:
    df = pd.read_excel("NR_dataset.xlsx")
except FileNotFoundError:
    st.error("Dataset file not found in repository.")
    st.stop()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# Normalize column names
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

required_fields = [
    "label",
    "customerid",
    "transactiondate",
    "productcategory",
    "purchaseamount",
    "customerregion",
    "retailchannel",
    "customersatisfaction",
]

missing_fields = [col for col in required_fields if col not in df.columns]

if missing_fields:
    st.error(f"Missing required logical fields: {missing_fields}")
    st.write("Actual columns in dataset:")
    st.write(df.columns)
    st.stop()

# Data type conversions
df["purchaseamount"] = pd.to_numeric(df["purchaseamount"], errors="coerce")
df["transactiondate"] = pd.to_datetime(df["transactiondate"], errors="coerce")
df = df.dropna(subset=["purchaseamount"])

# -----------------------
# STEP 4 — Sidebar Filters
# -----------------------
st.sidebar.header("Filters")

def create_filter(column_name, label):
    options = sorted(df[column_name].dropna().unique())
    return st.sidebar.multiselect(
        label,
        options=["All"] + list(options),
        default=["All"]
    )

selected_label = create_filter("label", "Customer Segment")
selected_category = create_filter("productcategory", "Product Category")
selected_region = create_filter("customerregion", "Customer Region")
selected_channel = create_filter("retailchannel", "Retail Channel")
selected_gender = create_filter("customergender", "Customer Gender") if "customergender" in df.columns else ["All"]
selected_age = create_filter("customeragegroup", "Customer Age Group") if "customeragegroup" in df.columns else ["All"]

# -----------------------
# STEP 5 — Filtering Logic
# -----------------------
filtered_df = df.copy()

if "All" not in selected_label:
    filtered_df = filtered_df[filtered_df["label"].isin(selected_label)]

if "All" not in selected_category:
    filtered_df = filtered_df[filtered_df["productcategory"].isin(selected_category)]

if "All" not in selected_region:
    filtered_df = filtered_df[filtered_df["customerregion"].isin(selected_region)]

if "All" not in selected_channel:
    filtered_df = filtered_df[filtered_df["retailchannel"].isin(selected_channel)]

if "customergender" in df.columns and "All" not in selected_gender:
    filtered_df = filtered_df[filtered_df["customergender"].isin(selected_gender)]

if "customeragegroup" in df.columns and "All" not in selected_age:
    filtered_df = filtered_df[filtered_df["customeragegroup"].isin(selected_age)]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# -----------------------
# STEP 6 — KPI Section
# -----------------------
total_revenue = filtered_df["purchaseamount"].sum()
total_transactions = filtered_df["transactionid"].nunique() if "transactionid" in filtered_df.columns else len(filtered_df)
unique_customers = filtered_df["customerid"].nunique()
avg_satisfaction = filtered_df["customersatisfaction"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Transactions", f"{total_transactions:,}")
col3.metric("Unique Customers", f"{unique_customers:,}")
col4.metric("Avg Customer Satisfaction", f"{avg_satisfaction:.2f}")

# -----------------------
# STEP 7 — Visualizations
# -----------------------

# Revenue by Segment
segment_df = (
    filtered_df.groupby("label", as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="purchaseamount", ascending=False)
)

fig_segment = px.bar(
    segment_df,
    x="label",
    y="purchaseamount",
    color="label",
    title="Revenue by Customer Segment"
)
fig_segment.update_layout(plot_bgcolor="white", paper_bgcolor="white")
st.plotly_chart(fig_segment, use_container_width=True)

col_left, col_right = st.columns(2)

# Revenue by Region
region_df = (
    filtered_df.groupby("customerregion", as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="customerregion")
)

fig_region = px.bar(
    region_df,
    x="customerregion",
    y="purchaseamount",
    title="Revenue by Region"
)
fig_region.update_layout(plot_bgcolor="white", paper_bgcolor="white")

# Revenue by Product Category
category_df = (
    filtered_df.groupby("productcategory", as_index=False)["purchaseamount"]
    .sum()
)

fig_category = px.bar(
    category_df,
    x="productcategory",
    y="purchaseamount",
    title="Revenue by Product Category"
)
fig_category.update_layout(plot_bgcolor="white", paper_bgcolor="white")

col_left.plotly_chart(fig_region, use_container_width=True)
col_right.plotly_chart(fig_category, use_container_width=True)

col_left2, col_right2 = st.columns(2)

# Revenue by Channel (Donut)
channel_df = (
    filtered_df.groupby("retailchannel", as_index=False)["purchaseamount"]
    .sum()
)

fig_channel = px.pie(
    channel_df,
    values="purchaseamount",
    names="retailchannel",
    title="Revenue Distribution by Sales Channel",
    hole=0.4
)
fig_channel.update_layout(plot_bgcolor="white", paper_bgcolor="white")

# Satisfaction vs Revenue
fig_scatter = px.scatter(
    filtered_df,
    x="customersatisfaction",
    y="purchaseamount",
    color="label",
    title="Revenue vs Customer Satisfaction"
)
fig_scatter.update_layout(plot_bgcolor="white", paper_bgcolor="white")

col_left2.plotly_chart(fig_channel, use_container_width=True)
col_right2.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------
# STEP 8 — Decline Risk Analysis
# -----------------------
st.header("Decline Risk Analysis")

decline_df = filtered_df[filtered_df["label"] == "Decline"]
growth_df = filtered_df[filtered_df["label"] == "Growth"]

decline_revenue = decline_df["purchaseamount"].sum()
decline_share = (decline_revenue / total_revenue * 100) if total_revenue > 0 else 0
decline_satisfaction = decline_df["customersatisfaction"].mean()
growth_satisfaction = growth_df["customersatisfaction"].mean()

col_d1, col_d2, col_d3 = st.columns(3)
col_d1.metric("Decline Revenue Share (%)", f"{decline_share:.2f}%")
col_d2.metric("Avg Satisfaction (Decline)", f"{decline_satisfaction:.2f}" if not pd.isna(decline_satisfaction) else "N/A")
col_d3.metric("Avg Satisfaction (Growth)", f"{growth_satisfaction:.2f}" if not pd.isna(growth_satisfaction) else "N/A")

# -----------------------
# STEP 9 — Top Customers
# -----------------------
top_customers = (
    filtered_df.groupby(["customerid", "label"], as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="purchaseamount", ascending=False)
    .head(10)
)

top_customers = top_customers.rename(columns={"purchaseamount": "Total Revenue"})
st.subheader("Top 10 Customers by Revenue")
st.dataframe(top_customers.reset_index(drop=True))

# -----------------------
# STEP 10 — Raw Data
# -----------------------
st.subheader("Filtered Dataset")
st.dataframe(filtered_df.reset_index(drop=True))
```
