import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(page_title="Vehicle Error Analysis Dashboard", page_icon="🚗", layout="wide")

# Custom CSS to adjust padding and font sizes
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 50px 0 20px 0;
        font-size: 36px;
        font-weight: bold;
        color: #333333;
    }
    .subheader {
        text-align: center;
        font-size: 18px;
        color: #555555;
        margin-bottom: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# Main Title and Subtitle
st.markdown('<div class="main-header">🚗 Vehicle Error Analysis Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">An interactive dashboard to monitor and analyze vehicle errors over time.</div>', unsafe_allow_html=True)

# Load the dataset
@st.cache_data
def load_data():
    return pd.read_excel("Basic_Data.xlsx")

df = load_data()

# Ensure the 'Date' column is of datetime type
df['Date'] = pd.to_datetime(df['Date'])

# Map of troubleshooting codes to their descriptions
troubleshooting_descriptions = {
    "WA009": "Drivers: steeringTrackingLost\nSTARTUP_CHECKS_FAILED\nMay also work for other LLC errors.",
    "WA041": "Cameras 19-22: camera_internal_state_error\nVision orchestration process aborted.\nMay also work for other camera errors.",
    "WA042": "Cameras 1-18: camera_internal_state_error\nVision orchestration process aborted.\nMay also work for other camera errors.",
    "WA043": "Logger Status: Chum Recorder is not recording to external drives.\nDisk is not connected at USB 3.0 speed.\nDisk is not mounted.",
    "WA047": "Radar Communication Failure: Data_Invalid.",
    "WA066": "Lidar: PTPTimeSyncFault.",
    "WA070": "Drivers: LinkStabilityLow.",
    "WA065": "Radar: RadarOutputSilent\nRadarDataMissing\nInvalidPtl.",
    "WA050.a": "SideKick: DataDependency.",
    "WA050.b": "SideKick: Unable to complete mic check with 'Say Hello Hero'.",
    "WA050.c": "SideKick: Unable to start mic check with ADR button not responsive."
}

# Function to wrap text
def wrap_text(text, width=40):
    wrapped_text = []
    for line in text.splitlines():
        while len(line) > width:
            wrapped_text.append(line[:width])
            line = line[width:]
        wrapped_text.append(line)
    return "<br>".join(wrapped_text)

# Apply wrapping to descriptions
for code, description in troubleshooting_descriptions.items():
    troubleshooting_descriptions[code] = wrap_text(description)

# Sidebar for filters
st.sidebar.header("🔎 Filter Options")

# Car Number Filter with "Select All" option
car_list = sorted(df["Car Number"].unique())
selected_cars = st.sidebar.multiselect(
    "Select Car Number(s):",
    options=car_list,
    default=car_list
)

if st.sidebar.checkbox("Select All Cars", value=True):
    selected_cars = car_list

# Error Code Filter with "Select All" option
error_list = sorted(df["Troubleshooting Code"].unique())
selected_errors = st.sidebar.multiselect(
    "Select Troubleshooting Code(s):",
    options=error_list,
    default=error_list
)

if st.sidebar.checkbox("Select All Error Codes", value=True):
    selected_errors = error_list

# Date Range Filter
min_date = df["Date"].min()
max_date = df["Date"].max()
selected_dates = st.sidebar.date_input(
    "Select Date Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Period Filter
period_options = ["Daily", "Weekly", "Monthly", "Yearly"]
selected_period = st.sidebar.selectbox(
    "Select Time Period:",
    options=period_options,
    index=3  # Default to Yearly
)

# Apply Filters
filtered_df = df[
    (df["Car Number"].isin(selected_cars)) &
    (df["Troubleshooting Code"].isin(selected_errors)) &
    (df["Date"] >= pd.to_datetime(selected_dates[0])) &
    (df["Date"] <= pd.to_datetime(selected_dates[1]))
]

# Data aggregation based on selected period
if selected_period == "Daily":
    filtered_df["Period"] = filtered_df["Date"].dt.date
elif selected_period == "Weekly":
    filtered_df["Period"] = filtered_df["Date"].dt.to_period('W').apply(lambda r: r.start_time)
elif selected_period == "Monthly":
    filtered_df["Period"] = filtered_df["Date"].dt.to_period('M').apply(lambda r: r.start_time)
elif selected_period == "Yearly":
    filtered_df["Period"] = filtered_df["Date"].dt.to_period('Y').apply(lambda r: r.start_time)

# Aggregated data for plotting
agg_counts = filtered_df.groupby(["Period", "Troubleshooting Code"]).size().reset_index(name='Count')
agg_time = filtered_df.groupby(["Period", "Troubleshooting Code"])["Time (min)"].sum().reset_index()

# Merging count and time data
agg_data = pd.merge(agg_counts, agg_time, on=["Period", "Troubleshooting Code"])
agg_data["Description"] = agg_data["Troubleshooting Code"].map(troubleshooting_descriptions)

# Layout of the dashboard
st.markdown("## 📊 Overview")

# Total Errors and Total Time Spent
total_errors = filtered_df.shape[0]
total_time = filtered_df["Time (min)"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Errors", f"{total_errors}")
col2.metric("Total Time Spent (min)", f"{total_time:.2f}")
col3.metric("Unique Cars Affected", f"{filtered_df['Car Number'].nunique()}")

st.markdown("---")

# Error Trend Over Time
st.markdown(f"### 📈 Error Trend Over Time ({selected_period})")
fig_trend = px.line(
    agg_data,
    x="Period",
    y="Count",
    color="Troubleshooting Code",
    hover_data=["Description", "Time (min)"],
    labels={
        "Period": selected_period,
        "Count": "Number of Errors",
        "Troubleshooting Code": "Error Code"
    },
    template="plotly_white"
)
fig_trend.update_layout(hovermode="x unified")
st.plotly_chart(fig_trend, use_container_width=True)

# Top Errors Bar Chart
st.markdown("### 🏆 Top Errors")
top_errors = agg_data.groupby("Troubleshooting Code")["Count"].sum().reset_index().sort_values(by="Count", ascending=False).head(10)
top_errors["Description"] = top_errors["Troubleshooting Code"].map(troubleshooting_descriptions)

fig_top_errors = px.bar(
    top_errors,
    x="Count",
    y="Troubleshooting Code",
    orientation="h",
    hover_data=["Description"],
    labels={
        "Count": "Number of Errors",
        "Troubleshooting Code": "Error Code"
    },
    template="plotly_white"
)
fig_top_errors.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_top_errors, use_container_width=True)

# Heatmap of Errors by Car and Period
st.markdown(f"### 🔥 Heatmap of Errors by Car and {selected_period}")
heatmap_data = filtered_df.groupby(["Car Number", "Period"]).size().reset_index(name="Count")
heatmap_pivot = heatmap_data.pivot(index="Car Number", columns="Period", values="Count").fillna(0)

fig_heatmap = px.imshow(
    heatmap_pivot,
    aspect="auto",
    labels={
        "x": selected_period,
        "y": "Car Number",
        "color": "Number of Errors"
    },
    color_continuous_scale="Reds",
    template="plotly_white"
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Time spent on errors per car
st.markdown("### ⏳ Time Spent on Errors by Car")
time_spent_per_car = filtered_df.groupby('Car Number')['Time (min)'].sum().reset_index()
fig_time_spent = px.bar(time_spent_per_car, x='Car Number', y='Time (min)',
                        title="Total Time Spent on Errors by Car",
                        labels={'Time (min)': 'Total Time (min)'},
                        template="plotly_white")
st.plotly_chart(fig_time_spent, use_container_width=True)

# Treemap of Errors by Time Spent
st.markdown("### 🌳 Error Resolution Time Treemap")
treemap_data = filtered_df.groupby(["Troubleshooting Code", "Car Number"])['Time (min)'].sum().reset_index()
treemap_data["Description"] = treemap_data["Troubleshooting Code"].map(troubleshooting_descriptions)

fig_treemap = px.treemap(
    treemap_data,
    path=['Troubleshooting Code', 'Car Number'],
    values='Time (min)',
    hover_data=['Description'],
    color='Time (min)',
    color_continuous_scale='Viridis',
    labels={'Time (min)': 'Total Time Spent (min)'},
    title='Treemap of Error Resolution Time by Car and Error Type',
)

fig_treemap.update_traces(
    hovertemplate="<b>Error Code:</b> %{label}<br><b>Total Time Spent (min):</b> %{value}<br><b>Car:</b> %{parent}<extra></extra>",
    textinfo="label+value"
)
st.plotly_chart(fig_treemap, use_container_width=True)

# Sidebar Information
st.sidebar.header("About")
st.sidebar.write("""
This app allows users to analyze error data from vehicles over time. 
You can filter by car, error code, and date to see trends and patterns in the errors. 
The dashboard also provides insights into the time spent resolving each error, 
helping to identify areas for improving vehicle efficiency and reducing downtime.
""")

